import numpy as np
import pytest
from sklearn.datasets import load_digits

from app.backend.datasets.digits_dataset import load_digits_dataset


def test_loads_original_digits_dimensions_and_classes():
    dataset = load_digits_dataset()

    assert len(dataset) == 1797
    assert dataset.images.shape == (1797, 8, 8)
    assert dataset.feature_vectors.shape == (1797, 64)
    assert dataset.labels.shape == (1797,)
    assert dataset.classes == tuple(range(10))
    assert dataset.feature_vectors.min() == 0
    assert dataset.feature_vectors.max() == 16
    assert np.array_equal(dataset.feature_vectors, dataset.images.reshape(-1, 64))


def test_split_is_reproducible_stratified_and_covers_all_samples():
    first = load_digits_dataset(test_size=0.25, random_state=7)
    second = load_digits_dataset(test_size=0.25, random_state=7)

    assert np.array_equal(first.train_indices, second.train_indices)
    assert np.array_equal(first.test_indices, second.test_indices)
    assert np.intersect1d(first.train_indices, first.test_indices).size == 0
    assert np.union1d(first.train_indices, first.test_indices).size == len(first)
    assert set(first.labels[first.train_indices]) == set(first.classes)
    assert set(first.labels[first.test_indices]) == set(first.classes)


def test_samples_and_reference_arrays_are_read_only():
    dataset = load_digits_dataset()
    sample = dataset.get_sample(0)

    assert sample.index == 0
    assert sample.label == int(dataset.labels[0])
    assert np.array_equal(sample.image, dataset.images[0])
    assert np.array_equal(sample.feature_vector, dataset.feature_vectors[0])
    with pytest.raises(ValueError):
        dataset.images[0, 0, 0] = 99
    with pytest.raises(IndexError):
        dataset.get_sample(len(dataset))


def test_loading_does_not_modify_sklearn_reference_values():
    reference = load_digits()
    reference_images = reference.images.copy()
    reference_targets = reference.target.copy()
    reference_features = reference.data.copy()

    load_digits_dataset()

    assert np.array_equal(reference.images, reference_images)
    assert np.array_equal(reference.target, reference_targets)
    assert np.array_equal(reference.data, reference_features)
