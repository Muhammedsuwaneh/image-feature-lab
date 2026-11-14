from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


@dataclass(frozen=True)
class ProcessedImage:
    """Original image and its MNIST-compatible 28x28 representation."""

    original_image: np.ndarray
    processed_image: np.ndarray
    feature_vector: np.ndarray
    source_path: Path
    normalization_summary: str = "Grayscale pixels resized to 28 x 28 and normalized to 0-1."

    @property
    def original_width(self) -> int:
        return int(self.original_image.shape[1])

    @property
    def original_height(self) -> int:
        return int(self.original_image.shape[0])


def _normalize_digit(grayscale: np.ndarray) -> tuple[np.ndarray, str]:
    """Match a single glyph to MNIST: light strokes, 20px glyph in a 28px frame."""
    border = np.concatenate((grayscale[0], grayscale[-1], grayscale[:, 0], grayscale[:, -1]))
    inverted = float(np.median(border)) > 127
    foreground = 255 - grayscale if inverted else grayscale.copy()
    if int(foreground.max()) - int(foreground.min()) < 8:
        raise ValueError("No clear digit was found. Choose an image with visible strokes and background.")
    if grayscale.shape == (28, 28):
        return foreground, "Dark strokes inverted; native 28 x 28 pixels preserved." if inverted else "Native MNIST 28 x 28 pixels preserved."
    mask = (foreground >= max(8, float(foreground.max()) * 0.05)).astype(np.uint8)
    count, components, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    if count <= 1:
        raise ValueError("No digit foreground was found in this image.")
    areas = stats[1:, cv2.CC_STAT_AREA]
    keep = np.flatnonzero(areas >= max(2, float(areas.max()) * 0.01)) + 1
    if not keep.size:
        raise ValueError("The image does not contain enough digit foreground.")
    retained = np.isin(components, keep)
    x, y, width, height = cv2.boundingRect(retained.astype(np.uint8))
    foreground = np.where((components == 0) | retained, foreground, 0).astype(np.uint8)
    cropped = foreground[y:y + height, x:x + width]
    scale = 20.0 / max(width, height)
    target_width = max(1, min(20, round(width * scale)))
    target_height = max(1, min(20, round(height * scale)))
    interpolation = cv2.INTER_AREA if scale <= 1 else cv2.INTER_LINEAR
    glyph = cv2.resize(cropped, (target_width, target_height), interpolation=interpolation)
    frame = np.zeros((28, 28), dtype=np.float32)
    left, top = (28 - target_width) // 2, (28 - target_height) // 2
    frame[top:top + target_height, left:left + target_width] = glyph
    moments = cv2.moments(frame)
    if moments["m00"] <= 0:
        raise ValueError("No digit foreground remains after normalization.")
    shift_x = 13.5 - moments["m10"] / moments["m00"]
    shift_y = 13.5 - moments["m01"] / moments["m00"]
    transform = np.float32([[1, 0, shift_x], [0, 1, shift_y]])
    normalized = cv2.warpAffine(frame, transform, (28, 28), flags=cv2.INTER_LINEAR, borderValue=0)
    polarity = "Dark strokes inverted" if inverted else "Light strokes preserved"
    return np.rint(normalized).astype(np.uint8), polarity + "; cropped to a 20px glyph, aspect ratio preserved, centered in a 28 x 28 MNIST frame."


def preprocess_image(image_path: str | Path, *, normalize_digit: bool = False) -> ProcessedImage:
    """Decode an image and convert it to a 784-value feature vector normalized to [0, 1]."""
    path = Path(image_path).expanduser()
    if path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
        raise ValueError("Supported image formats are PNG, JPG, and JPEG.")
    if not path.is_file():
        raise FileNotFoundError(f"Image file does not exist: {path}")

    try:
        encoded_image = np.fromfile(path, dtype=np.uint8)
    except OSError as error:
        raise OSError(f"Could not read image file: {path}") from error
    if encoded_image.size == 0:
        raise ValueError(f"Image file is empty: {path}")

    decoded = cv2.imdecode(encoded_image, cv2.IMREAD_UNCHANGED)
    if decoded is None:
        raise ValueError(f"Could not decode image file: {path}")
    if decoded.dtype == np.uint16:
        decoded = np.rint(decoded.astype(np.float64) / 257.0).astype(np.uint8)
    if decoded.ndim == 2:
        original_image = cv2.cvtColor(decoded, cv2.COLOR_GRAY2BGR)
    elif decoded.shape[2] == 4:
        alpha = decoded[:, :, 3:4].astype(np.float32) / 255.0
        original_image = np.rint(decoded[:, :, :3] * alpha + 255 * (1 - alpha)).astype(np.uint8)
    else:
        original_image = decoded

    grayscale = cv2.cvtColor(original_image, cv2.COLOR_BGR2GRAY)
    summary = "Grayscale pixels resized to 28 x 28 and normalized to 0-1."
    if normalize_digit:
        resized, summary = _normalize_digit(grayscale)
    else:
        interpolation = cv2.INTER_AREA if min(grayscale.shape) >= 28 else cv2.INTER_LINEAR
        resized = cv2.resize(grayscale, (28, 28), interpolation=interpolation)
    processed = resized.astype(np.uint8)
    feature_vector = processed.reshape(784).astype(np.float32) / 255.0

    return ProcessedImage(
        original_image=original_image,
        processed_image=processed,
        feature_vector=feature_vector,
        source_path=path.resolve(),
        normalization_summary=summary,
    )
