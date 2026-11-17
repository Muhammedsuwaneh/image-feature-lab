import numpy as np
import pytest

from app.backend.datasets.mnist_dataset import (
    dataset_from_splits,
    experiment_subset,
    load_mnist_dataset,
)


def test_tensorflow_mnist_dimensions_official_split_and_normalization(mnist_data):
    dataset = mnist_data

    assert len(dataset) == 70000
    assert dataset.images.shape == (70000, 28, 28)
    assert dataset.feature_vectors.shape == (70000, 784)
    assert dataset.labels.shape == (70000,)
    assert dataset.classes == tuple(range(10))
    assert len(dataset.train_indices) == 60000
    assert len(dataset.test_indices) == 10000
    assert dataset.train_indices[-1] == 59999
    assert dataset.test_indices[0] == 60000
    assert dataset.images.dtype == np.uint8
    assert dataset.feature_vectors.dtype == np.float32
    assert dataset.feature_vectors.min() == 0
    assert dataset.feature_vectors.max() == 1

    np.testing.assert_allclose(dataset.feature_vectors[0], dataset.images[0].ravel() / 255.0)

    assert load_mnist_dataset() is dataset


def test_subset_is_reproducible_stratified_and_never_moves_test_images_into_training(mnist_data):
    first = experiment_subset(mnist_data, train_limit=600, test_limit=100, random_state=7)
    second = experiment_subset(mnist_data, train_limit=600, test_limit=100, random_state=7)
    np.testing.assert_array_equal(first.source_indices, second.source_indices)

    assert np.all(first.source_indices[first.train_indices] < 60000)
    assert np.all(first.source_indices[first.test_indices] >= 60000)
    assert np.intersect1d(first.train_indices, first.test_indices).size == 0
    assert set(first.labels[first.train_indices]) == set(range(10))
    assert set(first.labels[first.test_indices]) == set(range(10))

    np.testing.assert_array_equal(first.images, mnist_data.images[first.source_indices])


def test_samples_and_all_dataset_arrays_are_read_only(small_mnist):
    dataset = small_mnist
    sample = dataset.get_sample(0)

    assert sample.label == dataset.labels[0]

    np.testing.assert_array_equal(sample.image, dataset.images[0])

    for array in (
        dataset.images,
        dataset.labels,
        dataset.feature_vectors,
        dataset.train_indices,
        dataset.test_indices,
        dataset.source_indices,
    ):
        assert not array.flags.writeable

    with pytest.raises(ValueError):
        dataset.images[0, 0, 0] = 99

    with pytest.raises(IndexError):
        dataset.get_sample(len(dataset))


def test_dataset_factory_copies_library_arrays_without_mutating_them():
    training = np.arange(20 * 784, dtype=np.uint8).reshape(20, 28, 28)
    test = training[:10].copy()
    labels = np.arange(20, dtype=np.uint8) % 10
    original = training.copy()
    dataset = dataset_from_splits(training, labels, test, labels[:10])
    np.testing.assert_array_equal(training, original)

    assert training.flags.writeable

    training[:] = 0
    np.testing.assert_array_equal(dataset.images[:20], original)


@pytest.mark.parametrize("limit", [0, -1, 1.5, True])
def test_subset_rejects_invalid_limits(small_mnist, limit):
    with pytest.raises(ValueError):
        experiment_subset(small_mnist, train_limit=limit)
