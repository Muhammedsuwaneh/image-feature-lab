from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from app.backend.datasets.digits_dataset import DigitsDataset
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
        query = np.asarray(values, dtype=np.float64)
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
    ) -> tuple[np.ndarray, np.ndarray] | np.ndarray:
        neighbour_count = self.k if n_neighbors is None else positive_integer(n_neighbors, "n_neighbors")
        if neighbour_count > self.train_features.shape[0]:
            raise ValueError("n_neighbors cannot exceed the number of training samples.")

        query = self._prepare_query_matrix(values)
        # Bound temporary memory instead of allocating queries x training x features.
        nearest_indices = np.empty((query.shape[0], neighbour_count), dtype=int)
        nearest_distances = np.empty((query.shape[0], neighbour_count), dtype=float)
        for start, distances in distance_batches(self.train_features, query):
            indices = np.argsort(distances, axis=1, kind="stable")[:, :neighbour_count]
            nearest_indices[start : start + len(distances)] = indices
            nearest_distances[start : start + len(distances)] = np.take_along_axis(distances, indices, axis=1)

        if return_distance:
            return nearest_distances, nearest_indices
        return nearest_indices

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


def train_knn_classifier(dataset: DigitsDataset, *, k: int = 5) -> KNNModel:
    """Train a Euclidean-distance k-NN model on the Digits dataset."""
    x_train = dataset.feature_vectors[dataset.train_indices]
    y_train = dataset.labels[dataset.train_indices]
    return KNNModel(train_features=x_train, train_labels=y_train, k=k)


def evaluate_knn_classifier(dataset: DigitsDataset, *, k: int = 5) -> dict[str, Any]:
    """Evaluate the model on the held-out Digits test split."""
    model = train_knn_classifier(dataset, k=k)
    x_test = dataset.feature_vectors[dataset.test_indices]
    y_test = dataset.labels[dataset.test_indices]

    nearest_distances, nearest_indices = model.kneighbors(x_test, n_neighbors=k, return_distance=True)
    predictions = model.predict_from_neighbors(nearest_indices)

    return {
        "k": int(k),
        "model": model,
        "test_accuracy": float(np.mean(predictions == y_test.astype(int))),
        "predicted_labels": predictions.astype(int),
        "actual_labels": y_test.astype(int),
        "nearest_neighbor_indices": nearest_indices.astype(int),
        "nearest_neighbor_dataset_indices": dataset.train_indices[nearest_indices].astype(int),
        "nearest_neighbor_labels": model.train_labels[nearest_indices].astype(int),
        "nearest_neighbor_distances": nearest_distances.astype(float),
        "prediction_count": int(x_test.shape[0]),
    }


def predict_knn_for_feature_vector(feature_vector: np.ndarray | list[float], dataset: DigitsDataset, *, k: int = 5) -> dict[str, Any]:
    """Predict the label for a single 64-dimensional feature vector and retrieve its nearest neighbors."""
    vector = np.asarray(feature_vector, dtype=np.float64).ravel()
    if vector.size != dataset.feature_vectors.shape[1]:
        raise ValueError(
            f"Feature vector length {vector.size} does not match dataset feature count {dataset.feature_vectors.shape[1]}."
        )

    model = train_knn_classifier(dataset, k=k)
    query = vector.reshape(1, -1)
    nearest_distances, nearest_indices = model.kneighbors(query, n_neighbors=k, return_distance=True)
    predicted_label = int(model.predict_from_neighbors(nearest_indices)[0])

    return {
        "predicted_label": predicted_label,
        "neighbor_indices": nearest_indices[0].astype(int),
        "neighbor_dataset_indices": dataset.train_indices[nearest_indices[0]].astype(int),
        "neighbor_labels": model.train_labels[nearest_indices[0]].astype(int),
        "neighbor_distances": nearest_distances[0].astype(float),
    }


def predict_image_with_knn(
    image_path: str | Path, dataset: DigitsDataset, *, k: int = 5
) -> dict[str, Any]:
    """Process a local image into Digits features and classify it using the trained k-NN model."""
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
