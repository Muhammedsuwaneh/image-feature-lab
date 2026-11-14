from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


@dataclass(frozen=True)
class ProcessedImage:
    """Original image and its Digits-compatible 8x8 representation."""

    original_image: np.ndarray
    processed_image: np.ndarray
    feature_vector: np.ndarray
    source_path: Path
    normalization_summary: str = "Grayscale pixels resized to 8 x 8 and scaled to 0-16."

    @property
    def original_width(self) -> int:
        return int(self.original_image.shape[1])

    @property
    def original_height(self) -> int:
        return int(self.original_image.shape[0])


def _normalize_digit(grayscale: np.ndarray) -> tuple[np.ndarray, str]:
    """Match a single uploaded glyph to Digits polarity, scale and placement.

    Background is estimated from the image border. Thresholding locates the
    foreground only; the resized features retain grayscale stroke information.
    Already-sized 8 x 8 inputs retain their original geometry and intensities.
    """
    border = np.concatenate((grayscale[0], grayscale[-1], grayscale[:, 0], grayscale[:, -1]))
    inverted = float(np.median(border)) > 127
    foreground = 255 - grayscale if inverted else grayscale.copy()
    if int(foreground.max()) - int(foreground.min()) < 8:
        raise ValueError("No clear digit was found. Choose an image with visible strokes and background.")
    if grayscale.shape == (8, 8):
        return foreground, "Dark strokes inverted; 8 x 8 geometry preserved." if inverted else "Digits-compatible 8 x 8 pixels preserved."

    # A low foreground threshold retains faint grayscale edge pixels. Otsu's
    # binary threshold can crop away useful outer strokes in low-resolution digits.
    mask = (foreground >= max(8, float(foreground.max()) * 0.05)).astype(np.uint8)
    count, components, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    if count <= 1:
        raise ValueError("No digit foreground was found in this image.")
    areas = stats[1:, cv2.CC_STAT_AREA]
    # Keep separate substantial strokes while ignoring isolated specks.
    keep = np.flatnonzero(areas >= max(2, float(areas.max()) * 0.01)) + 1
    if not keep.size:
        raise ValueError("The image does not contain enough digit foreground.")
    clean_mask = np.isin(components, keep).astype(np.uint8)
    x, y, width, height = cv2.boundingRect(clean_mask)
    # Keep antialiasing around the retained strokes rather than binarizing them.
    foreground = np.where((components == 0) | np.isin(components, keep), foreground, 0).astype(np.uint8)
    if 0.9 <= grayscale.shape[0] / grayscale.shape[1] <= 1.1 and height >= grayscale.shape[0] * 0.9:
        # An already aligned, square reference-style image should not be recropped.
        resized = cv2.resize(foreground, (8, 8), interpolation=cv2.INTER_AREA)
        return resized, "Dark strokes inverted; aligned layout preserved." if inverted else "Aligned light-on-dark layout preserved."
    cropped = foreground[y:y + height, x:x + width]
    side = max(width, height)
    # Center at source resolution, before downsampling. Rounding a narrow glyph
    # to an integer 8 x 8 width first causes a substantial half-pixel shift.
    centered = np.zeros((side, side), dtype=np.uint8)
    left, top = (side - width) // 2, (side - height) // 2
    centered[top:top + height, left:left + width] = cropped
    scale = 8.0 / side
    interpolation = cv2.INTER_AREA if scale <= 1 else cv2.INTER_LINEAR
    resized = cv2.resize(centered, (8, 8), interpolation=interpolation)
    polarity = "Dark strokes inverted" if inverted else "Light strokes preserved"
    return resized, polarity + "; foreground cropped, aspect ratio preserved, and centered."


def preprocess_image(image_path: str | Path, *, normalize_digit: bool = False) -> ProcessedImage:
    """Decode an image and convert it to a 64-value feature vector in [0, 16]."""
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
    summary = "Grayscale pixels resized to 8 x 8 and scaled to 0-16."
    if normalize_digit:
        resized, summary = _normalize_digit(grayscale)
    else:
        interpolation = cv2.INTER_AREA if min(grayscale.shape) >= 8 else cv2.INTER_LINEAR
        resized = cv2.resize(grayscale, (8, 8), interpolation=interpolation)
    processed = np.rint(resized.astype(np.float32) * (16.0 / 255.0)).astype(np.uint8)
    feature_vector = processed.reshape(64).astype(np.float64)

    return ProcessedImage(
        original_image=original_image,
        processed_image=processed,
        feature_vector=feature_vector,
        source_path=path.resolve(),
        normalization_summary=summary,
    )
