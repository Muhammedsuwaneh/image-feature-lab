"""TensorFlow/Keras MNIST with its official, disjoint train/test split.
"""

from dataclasses import dataclass
from functools import lru_cache
import os
from pathlib import Path

import numpy as np

from app.backend.validation import positive_integer


CACHE_DIRECTORY = Path(__file__).resolve().parents[3] / "data" / "keras"
os.environ.setdefault("KERAS_HOME", str(CACHE_DIRECTORY))
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
IMAGE_SIZE = 28
FEATURE_COUNT = IMAGE_SIZE * IMAGE_SIZE


@dataclass(frozen=True)
class MNISTSample:
    index: int
    image: np.ndarray
    label: int
    feature_vector: np.ndarray


@dataclass(frozen=True, eq=False)
class MNISTDataset:
    images: np.ndarray
    labels: np.ndarray
    feature_vectors: np.ndarray
    classes: tuple[int, ...]
    train_indices: np.ndarray
    test_indices: np.ndarray
    source_indices: np.ndarray
    split_random_state: int = 42

    def __len__(self) -> int:
        return len(self.labels)

    def get_sample(self, index: int) -> MNISTSample:
        if index < 0 or index >= len(self):
            raise IndexError(f"Sample index out of range: {index}")
        return MNISTSample(index, self.images[index], int(self.labels[index]), self.feature_vectors[index])


def dataset_from_splits(x_train, y_train, x_test, y_test) -> MNISTDataset:
    """Copy the library arrays without changing their values or official split."""
    for images, labels in ((x_train, y_train), (x_test, y_test)):
        if images.ndim != 3 or images.shape[1:] != (28, 28) or len(images) == 0:
            raise ValueError("MNIST images must have non-empty shape (samples, 28, 28).")
        if images.dtype != np.uint8:
            raise ValueError("MNIST source pixels must be uint8 intensities in [0,255].")
        if labels.ndim != 1 or len(labels) != len(images) or not np.issubdtype(labels.dtype, np.integer):
            raise ValueError("MNIST labels must be a matching integer vector.")
        if np.any((labels < 0) | (labels > 9)):
            raise ValueError("MNIST labels must be digits 0 through 9.")
    images = np.concatenate((x_train, x_test))
    labels = np.concatenate((y_train, y_test))
    features = images.reshape(-1, FEATURE_COUNT).astype(np.float32)
    features /= 255.0
    train_indices = np.arange(len(x_train))
    test_indices = np.arange(len(x_train), len(images))
    source_indices = np.arange(len(images))
    for array in (images, labels, features, train_indices, test_indices, source_indices):
        array.setflags(write=False)
    return MNISTDataset(images, labels, features, tuple(range(10)), train_indices, test_indices, source_indices)


@lru_cache(maxsize=1)
def load_mnist_dataset() -> MNISTDataset:
    """
        Load TensorFlow's MNIST (60,000 train / 10,000 test), downloading once.

        Keras verifies its own download hash and reuses the archive in KERAS_HOME.
        There is no fallback to a different dataset or to fabricated samples.
    """
    from tensorflow.keras.datasets import mnist

    (x_train, y_train), (x_test, y_test) = mnist.load_data()
    return dataset_from_splits(x_train, y_train, x_test, y_test)


def _sample_indices(indices, labels, limit, seed):
    limit = positive_integer(limit, "sample limit")
    if limit >= len(indices):
        return indices.copy()
    from sklearn.model_selection import train_test_split
    selected, _ = train_test_split(indices, train_size=limit, stratify=labels[indices], random_state=seed)
    return np.sort(selected)


def experiment_subset(dataset: MNISTDataset, *, train_limit=5000, test_limit=1000, random_state=42) -> MNISTDataset:
    """Stratified subsets drawn separately within the official training/test sets."""
    train = _sample_indices(dataset.train_indices, dataset.labels, train_limit, random_state)
    test = _sample_indices(dataset.test_indices, dataset.labels, test_limit, random_state)
    selected = np.concatenate((train, test))
    arrays = [dataset.images[selected], dataset.labels[selected], dataset.feature_vectors[selected],
              np.arange(len(train)), np.arange(len(train), len(selected)), dataset.source_indices[selected]]
    for array in arrays:
        array.setflags(write=False)
    return MNISTDataset(arrays[0], arrays[1], arrays[2], dataset.classes, arrays[3], arrays[4], arrays[5], random_state)
