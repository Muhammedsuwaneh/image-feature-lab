from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from app.backend.calculations.distance_metrics import (
    coefficient_of_variation,
    distance_standard_deviation,
    mean_distance,
    relative_distance_contrast,
    theoretical_squared_distance_cv,
    theoretical_squared_distance_expectation,
    theoretical_squared_distance_variance,
)
from app.backend.datasets.digits_dataset import DigitsDataset, load_digits_dataset
from app.backend.machine_learning.knn_classifier import train_knn_classifier


def _safe_relative_contrast(distances: np.ndarray) -> float:
    distances = np.asarray(distances, dtype=np.float64).ravel()
    if distances.size == 0:
        return 0.0
    minimum = float(np.min(distances))
    maximum = float(np.max(distances))
    if np.isclose(minimum, 0.0):
        return 0.0 if np.isclose(maximum, 0.0) else float("inf")
    return float((maximum - minimum) / minimum)


def _summarize_distance_distribution(distances: np.ndarray) -> dict[str, Any]:
    distances = np.asarray(distances, dtype=np.float64).ravel()
    if distances.size == 0:
        raise ValueError("Distance distribution must not be empty.")

    mean_value = float(np.mean(distances))
    std_value = float(np.std(distances, ddof=0))
    cv_value = 0.0 if np.isclose(mean_value, 0.0) else float(std_value / mean_value)
    return {
        "mean_distance": mean_value,
        "distance_std": std_value,
        "coefficient_of_variation": cv_value,
        "relative_distance_contrast": _safe_relative_contrast(distances),
        "nearest_distances": np.asarray(np.sort(distances)[: min(10, distances.size)], dtype=np.float64),
        "farthest_distances": np.asarray(np.sort(distances)[-min(10, distances.size) :], dtype=np.float64),
    }


def _pairwise_distance_summary(train_features: np.ndarray, test_features: np.ndarray) -> dict[str, Any]:
    train_features = np.asarray(train_features, dtype=np.float64)
    test_features = np.asarray(test_features, dtype=np.float64)
    if train_features.ndim != 2 or test_features.ndim != 2:
        raise ValueError("Training and test features must be 2D arrays.")
    if train_features.shape[1] != test_features.shape[1]:
        raise ValueError("Training and test feature dimension mismatch.")

    differences = test_features[:, None, :] - train_features[None, :, :]
    distances = np.linalg.norm(differences, axis=2)
    nearest_distances = distances.min(axis=1)
    farthest_distances = distances.max(axis=1)
    all_distances = distances.ravel()

    summary = _summarize_distance_distribution(all_distances)
    summary["nearest_distances"] = nearest_distances.astype(np.float64)
    summary["farthest_distances"] = farthest_distances.astype(np.float64)
    summary["nearest_distance_summary"] = _summarize_distance_distribution(nearest_distances)
    summary["farthest_distance_summary"] = _summarize_distance_distribution(farthest_distances)
    return summary


def run_synthetic_dimension_experiment(
    *,
    dimensions: tuple[int, ...] = (2, 4, 8, 16, 32, 64, 128, 256),
    samples_per_dimension: int = 2000,
    seed: int = 42,
) -> dict[int, dict[str, Any]]:
    """Generate synthetic random vectors and compare their empirical squared-distance moments to theory."""
    if samples_per_dimension <= 0:
        raise ValueError("samples_per_dimension must be positive.")

    rng = np.random.default_rng(seed)
    results: dict[int, dict[str, Any]] = {}
    for dimension in dimensions:
        if dimension <= 0:
            raise ValueError("Each dimension must be a positive integer.")
        left = rng.random((samples_per_dimension, int(dimension)))
        right = rng.random((samples_per_dimension, int(dimension)))
        squared_distances = np.sum((left - right) ** 2, axis=1)
        ordinary_distances = np.sqrt(squared_distances)

        mean_sq = float(np.mean(squared_distances))
        variance_sq = float(np.var(squared_distances, ddof=0))
        cv_sq = float(np.std(squared_distances, ddof=0) / mean_sq) if not np.isclose(mean_sq, 0.0) else 0.0

        results[int(dimension)] = {
            "dimension": int(dimension),
            "mean_squared_distance": mean_sq,
            "variance_squared_distance": variance_sq,
            "coefficient_of_variation": cv_sq,
            "ordinary_distance_cv": float(coefficient_of_variation(ordinary_distances)),
            "theoretical_mean_squared_distance": theoretical_squared_distance_expectation(int(dimension)),
            "theoretical_variance_squared_distance": theoretical_squared_distance_variance(int(dimension)),
            "theoretical_squared_distance_cv": theoretical_squared_distance_cv(int(dimension)),
            "sample_count": int(samples_per_dimension),
        }
    return results


def _evaluate_distance_knn(train_features: np.ndarray, train_labels: np.ndarray, test_features: np.ndarray, test_labels: np.ndarray, *, k: int = 5) -> dict[str, Any]:
    model = train_knn_classifier(
        DigitsDataset(
            images=np.empty((0, 8, 8), dtype=np.uint8),
            labels=np.array([], dtype=int),
            feature_vectors=np.empty((0, train_features.shape[1]), dtype=np.float64),
            classes=tuple(sorted(set(int(v) for v in train_labels))),
            train_indices=np.array([], dtype=int),
            test_indices=np.array([], dtype=int),
        ),
        k=k,
    )
    model.train_features = train_features
    model.train_labels = train_labels

    predictions = model.predict(test_features)
    distances, _ = model.kneighbors(test_features, n_neighbors=k, return_distance=True)
    distance_distribution = distances.ravel()

    summary = _pairwise_distance_summary(train_features, test_features)
    summary["test_accuracy"] = float(np.mean(predictions == test_labels.astype(int)))
    summary["predicted_labels"] = predictions.astype(int)
    summary["actual_labels"] = test_labels.astype(int)
    summary["nearest_distances"] = np.asarray(summary["nearest_distances"], dtype=np.float64)
    summary["farthest_distances"] = np.asarray(summary["farthest_distances"], dtype=np.float64)
    summary["all_pairwise_distances"] = np.asarray(distance_distribution, dtype=np.float64)
    summary["mean_distance"] = mean_distance(summary["all_pairwise_distances"])
    summary["distance_std"] = distance_standard_deviation(summary["all_pairwise_distances"])
    summary["coefficient_of_variation"] = coefficient_of_variation(summary["all_pairwise_distances"])
    summary["relative_distance_contrast"] = relative_distance_contrast(summary["all_pairwise_distances"])
    summary["k"] = int(k)
    return summary


def _build_augmented_features(data: np.ndarray, *, target_dimension: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    if target_dimension <= data.shape[1]:
        return data.copy()
    noise = rng.uniform(0.0, 16.0, size=(data.shape[0], target_dimension - data.shape[1]))
    return np.concatenate([data, noise], axis=1)


def run_irrelevant_feature_experiment(
    *,
    feature_sizes: tuple[int, ...] = (64, 96, 160, 256),
    seeds: tuple[int, ...] = (0, 1, 2),
    k: int = 5,
) -> dict[int, dict[str, Any]]:
    """Append irrelevant features to the Digits dataset and evaluate how dimensionality changes the distance profile and k-NN performance."""
    dataset = load_digits_dataset()
    results: dict[int, dict[str, Any]] = {}

    for feature_size in feature_sizes:
        if feature_size < 64:
            raise ValueError("feature_size must be at least 64 to preserve the original Digits features.")

        condition_metrics = []
        for seed in seeds:
            rng = np.random.default_rng(seed)
            augmented = _build_augmented_features(dataset.feature_vectors, target_dimension=feature_size, seed=seed)
            x_train = augmented[dataset.train_indices]
            x_test = augmented[dataset.test_indices]
            y_train = dataset.labels[dataset.train_indices]
            y_test = dataset.labels[dataset.test_indices]

            model = train_knn_classifier(
                DigitsDataset(
                    images=np.empty((0, 8, 8), dtype=np.uint8),
                    labels=np.array([], dtype=int),
                    feature_vectors=np.empty((0, x_train.shape[1]), dtype=np.float64),
                    classes=tuple(sorted(set(int(v) for v in y_train))),
                    train_indices=np.array([], dtype=int),
                    test_indices=np.array([], dtype=int),
                ),
                k=k,
            )
            model.train_features = x_train
            model.train_labels = y_train
            predictions = model.predict(x_test)
            distances, _ = model.kneighbors(x_test, n_neighbors=k, return_distance=True)

            summary = _pairwise_distance_summary(x_train, x_test)
            summary["test_accuracy"] = float(np.mean(predictions == y_test.astype(int)))
            summary["seed"] = int(seed)
            summary["feature_size"] = int(feature_size)
            summary["all_pairwise_distances"] = np.asarray(distances.ravel(), dtype=np.float64)
            summary["mean_distance"] = mean_distance(summary["all_pairwise_distances"])
            summary["distance_std"] = distance_standard_deviation(summary["all_pairwise_distances"])
            summary["coefficient_of_variation"] = coefficient_of_variation(summary["all_pairwise_distances"])
            summary["relative_distance_contrast"] = relative_distance_contrast(summary["all_pairwise_distances"])
            summary["nearest_distances"] = np.asarray(summary["nearest_distances"], dtype=np.float64)
            summary["farthest_distances"] = np.asarray(summary["farthest_distances"], dtype=np.float64)
            condition_metrics.append(summary)

        aggregate = {
            "feature_size": int(feature_size),
            "seeds": tuple(int(value) for value in seeds),
            "mean_distance": float(np.mean([item["mean_distance"] for item in condition_metrics])),
            "distance_std": float(np.mean([item["distance_std"] for item in condition_metrics])),
            "coefficient_of_variation": float(np.mean([item["coefficient_of_variation"] for item in condition_metrics])),
            "relative_distance_contrast": float(np.mean([item["relative_distance_contrast"] for item in condition_metrics])),
            "nearest_distances": np.concatenate([item["nearest_distances"] for item in condition_metrics]),
            "farthest_distances": np.concatenate([item["farthest_distances"] for item in condition_metrics]),
            "test_accuracy": float(np.mean([item["test_accuracy"] for item in condition_metrics])),
            "seed_results": condition_metrics,
        }
        results[int(feature_size)] = aggregate

    return results


def run_standardization_pca_experiment(
    *,
    dataset: DigitsDataset | None = None,
    random_state: int = 42,
    k: int = 5,
) -> dict[str, dict[str, Any]]:
    """Compare original, standardized, and PCA-reduced feature spaces while preventing leakage with train-only fitting."""
    if dataset is None:
        dataset = load_digits_dataset()

    x_train = dataset.feature_vectors[dataset.train_indices]
    y_train = dataset.labels[dataset.train_indices]
    x_test = dataset.feature_vectors[dataset.test_indices]
    y_test = dataset.labels[dataset.test_indices]

    results: dict[str, dict[str, Any]] = {}
    preprocessors = {
        "original_64": (x_train.copy(), x_test.copy()),
        "standardized": (
            StandardScaler().fit_transform(x_train),
            StandardScaler().fit(x_train).transform(x_test),
        ),
        "pca_16": (
            PCA(n_components=16, random_state=random_state).fit_transform(x_train),
            PCA(n_components=16, random_state=random_state).fit(x_train).transform(x_test),
        ),
        "pca_32": (
            PCA(n_components=32, random_state=random_state).fit_transform(x_train),
            PCA(n_components=32, random_state=random_state).fit(x_train).transform(x_test),
        ),
    }

    for name, (train_data, test_data) in preprocessors.items():
        model = train_knn_classifier(
            DigitsDataset(
                images=np.empty((0, 8, 8), dtype=np.uint8),
                labels=np.array([], dtype=int),
                feature_vectors=np.empty((0, train_data.shape[1]), dtype=np.float64),
                classes=tuple(sorted(set(int(v) for v in y_train))),
                train_indices=np.array([], dtype=int),
                test_indices=np.array([], dtype=int),
            ),
            k=k,
        )
        model.train_features = train_data
        model.train_labels = y_train
        predictions = model.predict(test_data)
        summary = _pairwise_distance_summary(train_data, test_data)
        summary["test_accuracy"] = float(np.mean(predictions == y_test.astype(int)))
        summary["name"] = name
        summary["k"] = int(k)
        results[name] = summary

    return results


def run_all_dimensionality_experiments() -> dict[str, Any]:
    """Run the full experimental suite and return the synthetic, irrelevant-feature, and PCA comparisons."""
    return {
        "synthetic": run_synthetic_dimension_experiment(),
        "irrelevant_features": run_irrelevant_feature_experiment(),
        "standardization_and_pca": run_standardization_pca_experiment(),
    }
