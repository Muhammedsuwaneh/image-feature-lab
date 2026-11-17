"""Reproducible experiments using the same held-out queries and training references."""

from __future__ import annotations

from typing import Any
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from app.backend.calculations.distance_metrics import (
    coefficient_of_variation,
    relative_distance_contrast,
    validate_squared_distance_theory,
)
from app.backend.calculations.pairwise import distance_batches
from app.backend.datasets.mnist_dataset import MNISTDataset, load_mnist_dataset, experiment_subset
from app.backend.machine_learning.knn_classifier import KNNModel
from app.backend.validation import feature_matrix, positive_integer


def _summarize_distance_distribution(distances: np.ndarray) -> dict[str, Any]:
    distances = np.asarray(distances, dtype=np.float64).ravel()

    return {
        "mean_distance": float(np.mean(distances)),
        "distance_std": float(np.std(distances, ddof=0)),
        "distance_variance": float(np.var(distances, ddof=0)),
        "coefficient_of_variation": coefficient_of_variation(distances),
        "relative_distance_contrast": relative_distance_contrast(distances),
    }


def _evaluate_distance_knn(
    train_features, train_labels, test_features, test_labels, *, k: int = 5, cancel_requested=None
) -> dict[str, Any]:
    """Measure every test-to-training distance once, without a full distance cube.

    Mean/std/CV describe pooled distances to ALL training references.
    Relative contrast is the mean of (max-min)/min computed per test query.
    """
    model = KNNModel(train_features, train_labels, k=k)
    queries = feature_matrix(test_features, "Test features")
    test_labels = np.asarray(test_labels)

    if len(queries) == 0 or test_labels.ndim != 1 or len(test_labels) != len(queries):
        raise ValueError("Test features and labels must contain matching, non-empty samples.")

    nearest, farthest, query_cvs, contrasts, neighbor_indices = [], [], [], [], []
    count, mean, m2 = 0, 0.0, 0.0

    for _, distances in distance_batches(model.train_features, queries):
        if cancel_requested is not None and cancel_requested():
            raise InterruptedError("MNIST experiments cancelled.")

        batch_count = distances.size
        batch_mean = float(np.mean(distances))
        delta = batch_mean - mean
        total = count + batch_count
        m2 += float(np.sum((distances - batch_mean) ** 2)) + delta**2 * count * batch_count / total
        mean += delta * batch_count / total
        count = total

        nearest.extend(distances.min(axis=1))
        farthest.extend(distances.max(axis=1))
        query_cvs.extend(coefficient_of_variation(row) for row in distances)
        contrasts.extend(relative_distance_contrast(row) for row in distances)
        neighbor_indices.append(model.neighbor_indices(distances, model.k))

    predictions = model.predict_from_neighbors(np.concatenate(neighbor_indices))
    nearest, farthest = np.asarray(nearest), np.asarray(farthest)
    variance = max(0.0, m2 / count)

    return {
        "feature_size": int(queries.shape[1]),
        "mean_distance": float(mean),
        "distance_std": float(np.sqrt(variance)),
        "distance_variance": float(variance),
        "coefficient_of_variation": float(np.sqrt(variance) / mean) if mean else 0.0,
        "mean_query_cv": float(np.mean(query_cvs)),
        "relative_distance_contrast": float(np.mean(contrasts)),
        "query_relative_contrasts": np.asarray(contrasts),
        "nearest_distances": nearest,
        "farthest_distances": farthest,
        "nearest_distance_summary": _summarize_distance_distribution(nearest),
        "farthest_distance_summary": _summarize_distance_distribution(farthest),
        "test_accuracy": float(np.mean(predictions == test_labels)),
        "predicted_labels": predictions,
        "actual_labels": test_labels.copy(),
        "distance_count": int(count),
        "k": model.k,
    }


def run_synthetic_dimension_experiment(
    *, dimensions=(2, 4, 8, 16, 32, 64, 128, 256), samples_per_dimension=2000, seed=42
):
    if not dimensions:
        raise ValueError("Select at least one synthetic dimension.")

    results = validate_squared_distance_theory(
        dimensions=dimensions, samples_per_dimension=samples_per_dimension, random_state=seed
    )

    for dimension, stats in results.items():
        stats.update(
            dimension=dimension,
            coefficient_of_variation=stats["squared_distance_cv"],
            sample_count=samples_per_dimension,
            seed=seed,
        )

    return results


def _build_augmented_features(data: np.ndarray, *, target_dimension: int, seed: int) -> np.ndarray:
    target_dimension = positive_integer(target_dimension, "target_dimension")

    if target_dimension < data.shape[1]:
        raise ValueError("target_dimension must preserve all original features.")

    rng = np.random.default_rng(seed)
    noise = rng.uniform(0.0, 1.0, size=(len(data), target_dimension - data.shape[1]))

    return np.concatenate([data, noise], axis=1)


def run_irrelevant_feature_experiment(
    *,
    dataset=None,
    feature_sizes=(784, 1024, 1568, 2352),
    seeds=(0, 1, 2),
    k=5,
    cancel_requested=None,
):
    if not feature_sizes or not seeds:
        raise ValueError("At least one feature size and one seed are required.")

    dataset = experiment_subset(load_mnist_dataset()) if dataset is None else dataset

    results = {}

    for feature_size in feature_sizes:
        condition_metrics = []

        for seed in seeds:
            augmented = _build_augmented_features(
                dataset.feature_vectors, target_dimension=feature_size, seed=seed
            )
            summary = _evaluate_distance_knn(
                augmented[dataset.train_indices],
                dataset.labels[dataset.train_indices],
                augmented[dataset.test_indices],
                dataset.labels[dataset.test_indices],
                k=k,
                cancel_requested=cancel_requested,
            )
            summary["seed"] = int(seed)
            condition_metrics.append(summary)

        scalar_metrics = (
            "mean_distance",
            "distance_std",
            "distance_variance",
            "coefficient_of_variation",
            "mean_query_cv",
            "relative_distance_contrast",
            "test_accuracy",
        )
        aggregate = {
            key: float(np.mean([item[key] for item in condition_metrics])) for key in scalar_metrics
        }
        aggregate.update(
            {
                "feature_size": int(feature_size),
                "k": int(k),
                "seeds": tuple(int(seed) for seed in seeds),
                "test_accuracy_std": float(
                    np.std([item["test_accuracy"] for item in condition_metrics])
                ),
                "nearest_distances": np.concatenate(
                    [item["nearest_distances"] for item in condition_metrics]
                ),
                "farthest_distances": np.concatenate(
                    [item["farthest_distances"] for item in condition_metrics]
                ),
                "seed_results": condition_metrics,
            }
        )
        results[int(feature_size)] = aggregate

    return results


def run_standardization_pca_experiment(
    *, dataset=None, random_state=42, k=5, cancel_requested=None
):
    """Fit each transformer ONCE on training data and reuse it for held-out data."""

    dataset = experiment_subset(load_mnist_dataset()) if dataset is None else dataset
    x_train, x_test = (
        dataset.feature_vectors[dataset.train_indices],
        dataset.feature_vectors[dataset.test_indices],
    )
    y_train, y_test = dataset.labels[dataset.train_indices], dataset.labels[dataset.test_indices]
    transformers = {
        "original": None,
        "standardized": StandardScaler(),
        "pca_16": PCA(n_components=16, svd_solver="randomized", random_state=random_state),
        "pca_32": PCA(n_components=32, svd_solver="randomized", random_state=random_state),
    }

    results = {}

    for name, transformer in transformers.items():
        if transformer is None:
            train_data, test_data = x_train, x_test
        else:
            transformer.fit(x_train)
            train_data, test_data = transformer.transform(x_train), transformer.transform(x_test)

        summary = _evaluate_distance_knn(
            train_data, y_train, test_data, y_test, k=k, cancel_requested=cancel_requested
        )
        summary["name"] = name

        if isinstance(transformer, PCA):
            summary["explained_variance_ratio"] = transformer.explained_variance_ratio_.copy()

        results[name] = summary

    return results


def run_all_dimensionality_experiments(
    *, dataset: MNISTDataset | None = None, train_limit=5000, test_limit=1000, cancel_requested=None
) -> dict[str, Any]:
    """Run all conditions against precisely the same dataset and split."""
    source = load_mnist_dataset() if dataset is None else dataset
    dataset = experiment_subset(source, train_limit=train_limit, test_limit=test_limit)

    return {
        "metadata": {
            "dataset": "tf.keras.datasets.mnist.load_data",
            "sample_count": len(dataset),
            "source_sample_count": len(source),
            "source_train_count": len(source.train_indices),
            "source_test_count": len(source.test_indices),
            "split": "official MNIST training/test partitions",
            "subset_seed": dataset.split_random_state,
            "train_indices": dataset.train_indices.copy(),
            "test_indices": dataset.test_indices.copy(),
            "train_source_indices": dataset.source_indices[dataset.train_indices],
            "test_source_indices": dataset.source_indices[dataset.test_indices],
            "k": 5,
            "metric": "euclidean",
            "synthetic_seed": 42,
            "noise_seeds": [0, 1, 2],
            "synthetic_pairs_per_dimension": 2000,
            "pca_solver": "randomized",
            "distance_statistics": "All held-out-query to training-reference distances; population variance.",
            "relative_contrast": "Mean over queries of (farthest - nearest) / nearest; positive/zero is infinity.",
            "seed_aggregation": "Arithmetic means of per-seed scalar metrics; population std of accuracy.",
        },
        "synthetic": run_synthetic_dimension_experiment(),
        "irrelevant_features": run_irrelevant_feature_experiment(
            dataset=dataset, cancel_requested=cancel_requested
        ),
        "standardization_and_pca": run_standardization_pca_experiment(
            dataset=dataset, cancel_requested=cancel_requested
        ),
    }
