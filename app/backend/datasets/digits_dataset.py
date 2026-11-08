from dataclasses import dataclass

import numpy as np
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split


@dataclass(frozen=True)
class DigitsSample:
	index: int
	image: np.ndarray
	label: int
	feature_vector: np.ndarray


@dataclass(frozen=True)
class DigitsDataset:
	"""Read-only copies of the original scikit-learn Digits dataset."""

	images: np.ndarray
	labels: np.ndarray
	feature_vectors: np.ndarray
	classes: tuple[int, ...]
	train_indices: np.ndarray
	test_indices: np.ndarray

	def __len__(self) -> int:
		return int(self.labels.shape[0])

	def get_sample(self, index: int) -> DigitsSample:
		if index < 0 or index >= len(self):
			raise IndexError(f"Sample index out of range: {index}")
		return DigitsSample(
			index=index,
			image=self.images[index],
			label=int(self.labels[index]),
			feature_vector=self.feature_vectors[index],
		)


def load_digits_dataset(*, test_size: float = 0.2, random_state: int = 42) -> DigitsDataset:
	"""Load the 8x8 Digits baseline and create a reproducible stratified split."""
	digits = load_digits()
	images = np.array(digits.images, copy=True)
	labels = np.array(digits.target, copy=True)
	feature_vectors = np.array(digits.data, copy=True)

	indices = np.arange(labels.shape[0])
	train_indices, test_indices = train_test_split(
		indices,
		test_size=test_size,
		random_state=random_state,
		stratify=labels,
	)

	for array in (images, labels, feature_vectors, train_indices, test_indices):
		array.setflags(write=False)

	return DigitsDataset(
		images=images,
		labels=labels,
		feature_vectors=feature_vectors,
		classes=tuple(int(value) for value in np.unique(labels)),
		train_indices=train_indices,
		test_indices=test_indices,
	)