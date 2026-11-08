import cv2
import numpy as np
import pytest

from app.backend.image_processing.image_preprocessor import preprocess_image


def write_image(path, image):
	encoded, buffer = cv2.imencode(path.suffix, image)
	assert encoded
	buffer.tofile(path)


@pytest.mark.parametrize("extension", [".png", ".jpg", ".jpeg"])
def test_preprocesses_supported_image_formats(tmp_path, extension):
	image_path = tmp_path / f"sample{extension}"
	image = np.full((16, 20, 3), 255, dtype=np.uint8)
	write_image(image_path, image)

	result = preprocess_image(image_path)

	assert result.original_image.shape == (16, 20, 3)
	assert result.processed_image.shape == (8, 8)
	assert result.feature_vector.shape == (64,)
	assert result.processed_image.dtype == np.uint8
	assert np.all(result.processed_image == 16)
	assert np.all(result.feature_vector == 16)
	assert result.original_width == 20
	assert result.original_height == 16


def test_converts_color_to_grayscale_and_scales_to_digits_range(tmp_path):
	image_path = tmp_path / "green.png"
	write_image(image_path, np.full((8, 8, 3), (0, 255, 0), dtype=np.uint8))

	result = preprocess_image(image_path)

	expected_gray = cv2.cvtColor(np.uint8([[[0, 255, 0]]]), cv2.COLOR_BGR2GRAY)[0, 0]
	expected_value = round(float(expected_gray) * 16.0 / 255.0)
	assert np.all(result.processed_image == expected_value)
	assert np.array_equal(result.feature_vector, result.processed_image.reshape(64))
	assert result.feature_vector.min() >= 0
	assert result.feature_vector.max() <= 16


def test_rejects_unsupported_and_corrupt_images(tmp_path):
	unsupported = tmp_path / "sample.bmp"
	unsupported.write_bytes(b"not an image")
	with pytest.raises(ValueError, match="Supported image formats"):
		preprocess_image(unsupported)

	corrupt = tmp_path / "corrupt.png"
	corrupt.write_bytes(b"not a png")
	with pytest.raises(ValueError, match="Could not decode"):
		preprocess_image(corrupt)


def test_reports_missing_image(tmp_path):
	with pytest.raises(FileNotFoundError, match="does not exist"):
		preprocess_image(tmp_path / "missing.jpg")