from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from app.backend.datasets.digits_dataset import DigitsDataset
from app.backend.image_processing.image_preprocessor import preprocess_image


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
        if self.k <= 0:
            raise ValueError("k must be a positive integer.")
        if self.train_features.ndim != 2:
            raise ValueError("Training features must be a 2D array.")
        if self.train_features.shape[0] != self.train_labels.shape[0]:
            raise ValueError("Feature and label counts must match.")

    def _prepare_query_matrix(self, values: np.ndarray) -> np.ndarray:
        query = np.asarray(values, dtype=np.float64)
        if query.ndim == 1:
            query = query.reshape(1, -1)
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
        neighbour_count = self.k if n_neighbors is None else int(n_neighbors)
        if neighbour_count <= 0:
            raise ValueError("n_neighbors must be a positive integer.")
        if neighbour_count > self.train_features.shape[0]:
            raise ValueError("n_neighbors cannot exceed the number of training samples.")

        query = self._prepare_query_matrix(values)
        distances = np.linalg.norm(self.train_features[None, :, :] - query[:, None, :], axis=2)
        nearest_indices = np.argsort(distances, axis=1)[:, :neighbour_count]
        nearest_distances = np.take_along_axis(distances, nearest_indices, axis=1)

        if return_distance:
            return nearest_distances, nearest_indices
        return nearest_indices

    def predict(self, values: np.ndarray) -> np.ndarray:
        query = self._prepare_query_matrix(values)
        distances, indices = self.kneighbors(query, n_neighbors=self.k, return_distance=True)
        predictions = []
        for row_index in range(query.shape[0]):
            labels = self.train_labels[indices[row_index]]
            counts = np.bincount(labels.astype(int), minlength=int(self.train_labels.max()) + 1)
            predictions.append(int(np.argmax(counts)))
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

    predictions = model.predict(x_test)
    nearest_distances, nearest_indices = model.kneighbors(x_test, n_neighbors=k, return_distance=True)

    return {
        "k": int(k),
        "model": model,
        "test_accuracy": float(np.mean(predictions == y_test.astype(int))),
        "predicted_labels": predictions.astype(int),
        "actual_labels": y_test.astype(int),
        "nearest_neighbor_indices": nearest_indices.astype(int),
        "nearest_neighbor_labels": dataset.labels[nearest_indices].astype(int),
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
    predicted_label = int(model.predict(query)[0])
    nearest_distances, nearest_indices = model.kneighbors(query, n_neighbors=k, return_distance=True)

    return {
        "predicted_label": predicted_label,
        "neighbor_indices": nearest_indices[0].astype(int),
        "neighbor_labels": dataset.labels[nearest_indices[0]].astype(int),
        "neighbor_distances": nearest_distances[0].astype(float),
    }


def predict_image_with_knn(
    image_path: str | Path, dataset: DigitsDataset, *, k: int = 5
) -> dict[str, Any]:
    """Process a local image into Digits features and classify it using the trained k-NN model."""
    processed = preprocess_image(image_path)
    return predict_knn_for_feature_vector(processed.feature_vector, dataset, k=k)


__all__ = [
    "KNNModel",
    "KNNPrediction",
    "evaluate_knn_classifier",
    "predict_image_with_knn",
    "predict_knn_for_feature_vector",
    "train_knn_classifier",
]
