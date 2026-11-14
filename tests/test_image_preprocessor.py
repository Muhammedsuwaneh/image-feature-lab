import cv2
import numpy as np
import pytest

from app.backend.image_processing.image_preprocessor import preprocess_image
from app.backend.image_processing.image_preprocessor import _normalize_digit
from app.backend.datasets.digits_dataset import load_digits_dataset
from app.backend.machine_learning.knn_classifier import predict_image_with_knn, train_knn_classifier
from pathlib import Path


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


def test_supplied_stylized_two_is_predicted_as_two():
    image_path = Path(__file__).parent / "fixtures" / "digit_2.png"
    dataset = load_digits_dataset()
    result = predict_image_with_knn(image_path, dataset)
    assert result["predicted_label"] == 2
    assert all(index in dataset.train_indices for index in result["neighbor_dataset_indices"])
    processed = preprocess_image(image_path, normalize_digit=True)
    assert "inverted" in processed.normalization_summary
    assert "cropped" in processed.normalization_summary
    assert processed.processed_image[0, 0] == 0


def test_polarity_padding_and_transparency_produce_equivalent_digit_features(tmp_path):
    original = cv2.imdecode(np.fromfile(Path(__file__).parent / "fixtures" / "digit_2.png", dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
    light_on_dark = 255 - original
    padded = cv2.copyMakeBorder(light_on_dark, 35, 80, 65, 20, cv2.BORDER_CONSTANT, value=0)
    transparent = np.zeros((*original.shape, 4), dtype=np.uint8)
    transparent[:, :, 3] = light_on_dark  # Black ink over transparent background.
    images = [original, light_on_dark, padded, 255 - padded, transparent]
    vectors = []
    for index, image in enumerate(images):
        path = tmp_path / f"variant-{index}.png"
        write_image(path, image)
        vectors.append(preprocess_image(path, normalize_digit=True).feature_vector)
    for vector in vectors[1:]:
        np.testing.assert_array_equal(vector, vectors[0])


@pytest.mark.parametrize("brightness", [0, 127, 255])
def test_normalized_upload_rejects_blank_images(tmp_path, brightness):
    path = tmp_path / "blank.png"
    write_image(path, np.full((32, 32), brightness, dtype=np.uint8))
    with pytest.raises(ValueError, match="No clear digit"):
        preprocess_image(path, normalize_digit=True)


def test_normalization_preserves_native_digits_features():
    dataset = load_digits_dataset()
    for index in dataset.test_indices:
        pixels = np.rint(dataset.images[index] * (255.0 / 16)).astype(np.uint8)
        for variant in (pixels, 255 - pixels):
            normalized, _ = _normalize_digit(variant)
            np.testing.assert_array_equal(np.rint(normalized * (16.0 / 255)), dataset.images[index])


@pytest.mark.parametrize("inverted", [False, True])
def test_padded_uploaded_digits_have_good_accuracy_across_all_classes(inverted):
    dataset = load_digits_dataset()
    vectors = []
    for index in dataset.test_indices:
        pixels = np.rint(dataset.images[index] * (255.0 / 16)).astype(np.uint8)
        enlarged = cv2.resize(pixels, (64, 64), interpolation=cv2.INTER_NEAREST)
        padded = cv2.copyMakeBorder(enlarged, 13, 29, 47, 11, cv2.BORDER_CONSTANT, value=0)
        normalized, _ = _normalize_digit(255 - padded if inverted else padded)
        vectors.append(np.rint(normalized * (16.0 / 255)).ravel())
    predictions = train_knn_classifier(dataset).predict(np.asarray(vectors))
    assert np.mean(predictions == dataset.labels[dataset.test_indices]) >= 0.95


def test_enlarged_aligned_digits_keep_baseline_accuracy():
    dataset = load_digits_dataset()
    vectors = []
    for index in dataset.test_indices:
        pixels = np.rint(dataset.images[index] * (255.0 / 16)).astype(np.uint8)
        enlarged = cv2.resize(pixels, (64, 64), interpolation=cv2.INTER_NEAREST)
        normalized, _ = _normalize_digit(enlarged)
        vectors.append(np.rint(normalized * (16.0 / 255)).ravel())
    model = train_knn_classifier(dataset)
    labels = dataset.labels[dataset.test_indices]
    baseline_accuracy = np.mean(model.predict(dataset.feature_vectors[dataset.test_indices]) == labels)
    assert np.mean(model.predict(np.asarray(vectors)) == labels) >= baseline_accuracy
