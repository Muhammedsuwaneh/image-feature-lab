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

	@property
	def original_width(self) -> int:
		return int(self.original_image.shape[1])

	@property
	def original_height(self) -> int:
		return int(self.original_image.shape[0])


def preprocess_image(image_path: str | Path) -> ProcessedImage:
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

	original_image = cv2.imdecode(encoded_image, cv2.IMREAD_COLOR)
	if original_image is None:
		raise ValueError(f"Could not decode image file: {path}")

	grayscale = cv2.cvtColor(original_image, cv2.COLOR_BGR2GRAY)
	interpolation = (
		cv2.INTER_AREA
		if grayscale.shape[0] >= 8 and grayscale.shape[1] >= 8
		else cv2.INTER_LINEAR
	)
	resized = cv2.resize(grayscale, (8, 8), interpolation=interpolation)
	processed = np.rint(resized.astype(np.float32) * (16.0 / 255.0)).astype(np.uint8)
	feature_vector = processed.reshape(64).astype(np.float64)

	return ProcessedImage(
		original_image=original_image,
		processed_image=processed,
		feature_vector=feature_vector,
		source_path=path.resolve(),
	)