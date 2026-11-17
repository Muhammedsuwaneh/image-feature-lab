from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any

import numpy as np

from app.backend.datasets.mnist_dataset import MNISTDataset, CACHE_DIRECTORY
from app.backend.calculations.pairwise import distance_batches
from app.backend.image_processing.image_preprocessor import preprocess_image
from app.backend.validation import feature_matrix, positive_integer


@dataclass(frozen=True)
class KNNPrediction:
    predicted_label: int
    neighbor_indices: np.ndarray
    neighbor_labels: np.ndarray
    neighbor_distances: np.ndarray
    query_vector: np.ndarray


@dataclass
class KNNModel:
    train_features: np.ndarray
    train_labels: np.ndarray
    k: int = 5

    def __post_init__(self) -> None:
        self.k = positive_integer(self.k, "k")
        self.train_features = feature_matrix(self.train_features, "Training features")
        self.train_labels = np.asarray(self.train_labels)

        if self.train_labels.ndim != 1 or self.train_features.shape[0] != len(self.train_labels):
            raise ValueError("Feature and label counts must match.")

        if not np.issubdtype(self.train_labels.dtype, np.integer):
            raise ValueError("Training labels must be integers.")

        if self.k > len(self.train_features):
            raise ValueError("k cannot exceed the number of training samples.")

    def _prepare_query_matrix(self, values: np.ndarray) -> np.ndarray:
        query = np.asarray(values, dtype=self.train_features.dtype)

        if query.ndim == 1:
            query = query.reshape(1, -1)

        query = feature_matrix(query, "Query features", allow_empty=True)

        if query.shape[1] != self.train_features.shape[1]:
            raise ValueError(
                f"Feature vector length {query.shape[1]} does not match dataset feature count {self.train_features.shape[1]}."
            )

        return query

    def kneighbors(
        self,
        values: np.ndarray,
        *,
        n_neighbors: int | None = None,
        return_distance: bool = True,
        cancel_requested=None,
    ) -> tuple[np.ndarray, np.ndarray] | np.ndarray:
        neighbour_count = (
            self.k if n_neighbors is None else positive_integer(n_neighbors, "n_neighbors")
        )

        if neighbour_count > self.train_features.shape[0]:
            raise ValueError("n_neighbors cannot exceed the number of training samples.")

        query = self._prepare_query_matrix(values)
        nearest_indices = np.empty((query.shape[0], neighbour_count), dtype=int)
        nearest_distances = np.empty((query.shape[0], neighbour_count), dtype=float)

        for start, distances in distance_batches(self.train_features, query):
            if cancel_requested is not None and cancel_requested():
                raise InterruptedError("MNIST evaluation cancelled.")

            indices = self.neighbor_indices(distances, neighbour_count)
            nearest_indices[start : start + len(distances)] = indices
            nearest_distances[start : start + len(distances)] = np.take_along_axis(
                distances, indices, axis=1
            )

        if return_distance:
            return nearest_distances, nearest_indices

        return nearest_indices

    @staticmethod
    def neighbor_indices(distances: np.ndarray, count: int) -> np.ndarray:
        """Select only k neighbors, retaining training-order ties at the cutoff."""
        if count == distances.shape[1]:
            return np.argsort(distances, axis=1, kind="stable")

        candidates = np.argpartition(distances, count - 1, axis=1)[:, :count]
        selected = np.empty_like(candidates)

        for row, indices in enumerate(candidates):
            cutoff = distances[row, indices].max()
            closer = np.flatnonzero(distances[row] < cutoff)
            tied = np.flatnonzero(distances[row] == cutoff)[: count - len(closer)]
            chosen = np.concatenate((closer, tied))
            selected[row] = chosen[np.lexsort((chosen, distances[row, chosen]))]

        return selected

    def predict(self, values: np.ndarray) -> np.ndarray:
        query = self._prepare_query_matrix(values)
        indices = self.kneighbors(query, n_neighbors=self.k, return_distance=False)

        return self.predict_from_neighbors(indices)

    def predict_from_neighbors(self, indices: np.ndarray) -> np.ndarray:
        """Vote once neighbors are known; ties choose the smallest class label."""
        predictions = []

        for row in indices:
            labels, counts = np.unique(self.train_labels[row], return_counts=True)
            predictions.append(int(labels[np.argmax(counts)]))

        return np.asarray(predictions, dtype=int)


def train_knn_classifier(dataset: MNISTDataset, *, k: int = 5) -> KNNModel:
    """Cache training references for repeated predictions on the MNIST dataset."""
    return _cached_training_model(dataset, positive_integer(k, "k"))


@lru_cache(maxsize=2)
def _cached_training_model(dataset: MNISTDataset, k: int) -> KNNModel:
    x_train = dataset.feature_vectors[dataset.train_indices]
    y_train = dataset.labels[dataset.train_indices]

    return KNNModel(train_features=x_train, train_labels=y_train, k=k)


@lru_cache(maxsize=2)
def dataset_fingerprint(dataset: MNISTDataset) -> str:
    digest = hashlib.sha256()

    for array in (
        dataset.feature_vectors,
        dataset.labels,
        dataset.train_indices,
        dataset.test_indices,
    ):
        digest.update(str((array.shape, array.dtype.str)).encode("ascii"))
        digest.update(memoryview(np.ascontiguousarray(array)).cast("B"))

    return digest.hexdigest()


def supports_baseline_cache(dataset: MNISTDataset) -> bool:
    return (
        len(dataset.train_indices) == 60000
        and len(dataset.test_indices) == 10000
        and dataset.feature_vectors.shape == (70000, 784)
    )


def save_baseline_accuracy(dataset: MNISTDataset, *, k: int, accuracy: float) -> None:
    """Persist measured accuracy with a fingerprint of all values and partitions."""
    folder = CACHE_DIRECTORY
    temporary = None

    try:
        folder.mkdir(parents=True, exist_ok=True)
        record = {
            "algorithm": "euclidean-uniform-stable-v1",
            "fingerprint": dataset_fingerprint(dataset),
            "k": k,
            "test_accuracy": accuracy,
            "test_samples": len(dataset.test_indices),
        }

        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=folder, delete=False
        ) as file:
            temporary = Path(file.name)
            json.dump(record, file)

        os.replace(temporary, folder / f"knn-baseline-k{k}.json")
    except OSError:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass


def _cached_accuracy(dataset: MNISTDataset, k: int):
    try:
        record = json.loads(
            (CACHE_DIRECTORY / f"knn-baseline-k{k}.json").read_text(encoding="utf-8")
        )
        value = float(record["test_accuracy"])

        if (
            record.get("algorithm") == "euclidean-uniform-stable-v1"
            and record.get("k") == k
            and record.get("fingerprint") == dataset_fingerprint(dataset)
            and record.get("test_samples") == len(dataset.test_indices)
            and 0 <= value <= 1
        ):
            return value
    except (OSError, ValueError, TypeError, KeyError):
        pass

    return None


def evaluate_knn_classifier(
    dataset: MNISTDataset, *, k: int = 5, cancel_requested=None, accuracy_only=False
) -> dict[str, Any]:
    """Evaluate MNIST; accuracy_only can reuse a fingerprint-verified summary.

    The default still returns full freshly calculated predictions and neighbors.
    """
    k = positive_integer(k, "k")
    cacheable = supports_baseline_cache(dataset)

    if accuracy_only and cacheable:
        accuracy = _cached_accuracy(dataset, k)

        if accuracy is not None:
            return {
                "k": k,
                "test_accuracy": accuracy,
                "prediction_count": len(dataset.test_indices),
                "cached": True,
            }

    model = train_knn_classifier(dataset, k=k)
    x_test = dataset.feature_vectors[dataset.test_indices]
    y_test = dataset.labels[dataset.test_indices]

    nearest_distances, nearest_indices = model.kneighbors(
        x_test, n_neighbors=k, return_distance=True, cancel_requested=cancel_requested
    )
    predictions = model.predict_from_neighbors(nearest_indices)
    accuracy = float(np.mean(predictions == y_test.astype(int)))

    if cacheable:
        save_baseline_accuracy(dataset, k=k, accuracy=accuracy)

    return {
        "k": int(k),
        "model": model,
        "test_accuracy": accuracy,
        "predicted_labels": predictions.astype(int),
        "actual_labels": y_test.astype(int),
        "nearest_neighbor_indices": nearest_indices.astype(int),
        "nearest_neighbor_dataset_indices": dataset.train_indices[nearest_indices].astype(int),
        "nearest_neighbor_labels": model.train_labels[nearest_indices].astype(int),
        "nearest_neighbor_distances": nearest_distances.astype(float),
        "prediction_count": int(x_test.shape[0]),
    }


def predict_knn_for_feature_vector(
    feature_vector: np.ndarray | list[float], dataset: MNISTDataset, *, k: int = 5
) -> dict[str, Any]:
    """Predict a 784-dimensional MNIST vector and retrieve training neighbors."""
    vector = np.asarray(feature_vector, dtype=np.float64).ravel()

    if vector.size != dataset.feature_vectors.shape[1]:
        raise ValueError(
            f"Feature vector length {vector.size} does not match dataset feature count {dataset.feature_vectors.shape[1]}."
        )

    model = train_knn_classifier(dataset, k=k)
    query = vector.reshape(1, -1)
    nearest_distances, nearest_indices = model.kneighbors(
        query, n_neighbors=k, return_distance=True
    )
    predicted_label = int(model.predict_from_neighbors(nearest_indices)[0])

    return {
        "predicted_label": predicted_label,
        "neighbor_indices": nearest_indices[0].astype(int),
        "neighbor_dataset_indices": dataset.train_indices[nearest_indices[0]].astype(int),
        "neighbor_labels": model.train_labels[nearest_indices[0]].astype(int),
        "neighbor_distances": nearest_distances[0].astype(float),
    }


def predict_image_with_knn(
    image_path: str | Path, dataset: MNISTDataset, *, k: int = 5
) -> dict[str, Any]:
    """Normalize an uploaded image to MNIST and classify it against training data."""
    processed = preprocess_image(image_path, normalize_digit=True)

    return predict_knn_for_feature_vector(processed.feature_vector, dataset, k=k)


__all__ = [
    "KNNModel",
    "KNNPrediction",
    "evaluate_knn_classifier",
    "predict_image_with_knn",
    "predict_knn_for_feature_vector",
    "train_knn_classifier",
]
