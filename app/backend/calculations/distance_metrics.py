from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np

from app.backend.validation import positive_integer
from app.backend.calculations.pairwise import distance_batches


def _as_1d_numeric_array(values: Sequence[float] | np.ndarray, *, name: str) -> np.ndarray:
    array = np.asarray(values, dtype=np.float64)

    if array.ndim == 0:
        array = array.reshape(1)

    if array.size == 0:
        raise ValueError(f"{name} must not be empty.")

    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} contains non-finite values.")

    return array.ravel()


def _distances(values) -> np.ndarray:
    result = _as_1d_numeric_array(values, name="Distance values")

    if np.any(result < 0):
        raise ValueError("Distance values must be non-negative.")

    return result


def euclidean_distance(x: Sequence[float] | np.ndarray, y: Sequence[float] | np.ndarray) -> float:
    x_array = _as_1d_numeric_array(x, name="First vector")
    y_array = _as_1d_numeric_array(y, name="Second vector")

    if x_array.shape != y_array.shape:
        raise ValueError(
            f"Vectors must have identical shapes; got {x_array.shape} and {y_array.shape}."
        )

    return float(np.linalg.norm(x_array - y_array))


def squared_euclidean_distance(
    x: Sequence[float] | np.ndarray, y: Sequence[float] | np.ndarray
) -> float:
    x_array = _as_1d_numeric_array(x, name="First vector")
    y_array = _as_1d_numeric_array(y, name="Second vector")

    if x_array.shape != y_array.shape:
        raise ValueError(
            f"Vectors must have identical shapes; got {x_array.shape} and {y_array.shape}."
        )

    return float(np.sum((x_array - y_array) ** 2))


def mean_distance(values: Sequence[float] | np.ndarray) -> float:
    distances = _distances(values)

    return float(np.mean(distances))


def distance_variance(values: Sequence[float] | np.ndarray) -> float:
    distances = _distances(values)

    return float(np.var(distances, ddof=0))


def distance_standard_deviation(values: Sequence[float] | np.ndarray) -> float:
    distances = _distances(values)

    return float(np.std(distances, ddof=0))


def variance_distance(values: Sequence[float] | np.ndarray) -> float:
    """Backward-compatible alias for the population variance of a distance array."""
    return distance_variance(values)


def std_distance(values: Sequence[float] | np.ndarray) -> float:
    """Backward-compatible alias for the population standard deviation of a distance array."""
    return distance_standard_deviation(values)


def coefficient_of_variation(values: Sequence[float] | np.ndarray) -> float:
    """Compute the coefficient of variation for ordinary distances: sigma / mu."""
    distances = _distances(values)
    mean_value = float(np.mean(distances))
    std_value = float(np.std(distances, ddof=0))

    if mean_value == 0.0:
        return 0.0 if std_value == 0.0 else math.inf

    return float(std_value / mean_value)


def ordinary_distance_cv(values: Sequence[float] | np.ndarray) -> float:
    """Alias that exposes the ordinary-distance CV explicitly."""
    return coefficient_of_variation(values)


def squared_distance_coefficient_of_variation(values: Sequence[float] | np.ndarray) -> float:
    """Compute CV for squared distances: sqrt(Var(D^2)) / E[D^2]."""
    distances = _distances(values)
    squared_values = distances**2
    mean_value = float(np.mean(squared_values))
    std_value = float(np.std(squared_values, ddof=0))

    if mean_value == 0.0:
        return 0.0 if std_value == 0.0 else math.inf

    return float(std_value / mean_value)


def squared_distance_cv(values: Sequence[float] | np.ndarray) -> float:
    """Alias that exposes the squared-distance CV explicitly."""
    return squared_distance_coefficient_of_variation(values)


def relative_distance_contrast(values: Sequence[float] | np.ndarray) -> float:
    """Return C(x) = (D_max - D_min) / D_min with safe handling of zero minima."""
    distances = _distances(values)
    minimum = float(np.min(distances))
    maximum = float(np.max(distances))

    if minimum == 0.0:
        return 0.0 if maximum == 0.0 else math.inf

    return float((maximum - minimum) / minimum)


def analyze_distance_to_samples(
    query_vector: Sequence[float] | np.ndarray,
    reference_samples: Sequence[Sequence[float]] | np.ndarray,
) -> dict[str, float | int | np.ndarray]:
    """Analyze Euclidean distances from a query vector to a set of reference samples."""
    query = _as_1d_numeric_array(query_vector, name="Query vector")
    references = np.asarray(reference_samples, dtype=np.float64)

    if references.size == 0:
        raise ValueError("Reference samples must not be empty.")

    if references.ndim == 1:
        references = references.reshape(1, -1)

    if references.ndim != 2 or not np.all(np.isfinite(references)):
        raise ValueError("Reference samples must be a finite 2D array.")

    if query.shape[0] != references.shape[1]:
        raise ValueError(
            f"Query vector dimension {query.shape[0]} does not match reference dimension {references.shape[1]}."
        )

    distances = next(distance_batches(references, query.reshape(1, -1)))[1][0]
    nearest_index = int(np.argmin(distances))
    farthest_index = int(np.argmax(distances))

    return {
        "minimum_distance": float(np.min(distances)),
        "maximum_distance": float(np.max(distances)),
        "mean_distance": float(np.mean(distances)),
        "std_distance": float(np.std(distances, ddof=0)),
        "distance_distribution": distances,
        "nearest_sample_index": nearest_index,
        "farthest_sample_index": farthest_index,
        "nearest_distance": float(distances[nearest_index]),
        "farthest_distance": float(distances[farthest_index]),
    }


def theoretical_squared_distance_expectation(dimension: int) -> float:
    """Expected squared Euclidean distance under U[0,1]^d coordinates."""
    dimension = positive_integer(dimension, "Dimension")

    return float(dimension / 6.0)


def theoretical_squared_distance_variance(dimension: int) -> float:
    """Variance of squared Euclidean distance under U[0,1]^d coordinates."""
    dimension = positive_integer(dimension, "Dimension")

    return float(7.0 * dimension / 180.0)


def theoretical_squared_distance_cv(dimension: int) -> float:
    """Coefficient of variation for squared distances under U[0,1]^d coordinates."""
    dimension = positive_integer(dimension, "Dimension")

    return float(math.sqrt(7.0 / (5.0 * dimension)))


def validate_squared_distance_theory(
    *,
    dimensions: Sequence[int] = (2, 10, 100),
    samples_per_dimension: int = 10000,
    random_state: int | None = 42,
) -> dict[int, dict[str, float]]:
    """Validate empirical squared-distance behavior against theoretical moments."""
    samples_per_dimension = positive_integer(samples_per_dimension, "samples_per_dimension")

    rng = np.random.default_rng(random_state)
    summary: dict[int, dict[str, float]] = {}

    for dimension in dimensions:
        dimension = positive_integer(dimension, "Dimension")
        sample_a = rng.random((samples_per_dimension, int(dimension)))
        sample_b = rng.random((samples_per_dimension, int(dimension)))
        squared_distances = np.sum((sample_a - sample_b) ** 2, axis=1)
        ordinary_distances = np.sqrt(squared_distances)

        summary[int(dimension)] = {
            "dimension": float(dimension),
            "mean_squared_distance": float(np.mean(squared_distances)),
            "variance_squared_distance": float(np.var(squared_distances, ddof=0)),
            "coefficient_of_variation": float(
                np.std(ordinary_distances, ddof=0) / np.mean(ordinary_distances)
            ),
            "squared_distance_cv": float(
                squared_distance_coefficient_of_variation(ordinary_distances)
            ),
            "ordinary_distance_cv": float(coefficient_of_variation(ordinary_distances)),
            "theoretical_mean_squared_distance": theoretical_squared_distance_expectation(
                int(dimension)
            ),
            "theoretical_variance_squared_distance": theoretical_squared_distance_variance(
                int(dimension)
            ),
            "theoretical_squared_distance_cv": theoretical_squared_distance_cv(int(dimension)),
        }

    return summary


__all__ = [
    "analyze_distance_to_samples",
    "coefficient_of_variation",
    "distance_standard_deviation",
    "distance_variance",
    "euclidean_distance",
    "mean_distance",
    "ordinary_distance_cv",
    "relative_distance_contrast",
    "squared_distance_coefficient_of_variation",
    "squared_distance_cv",
    "squared_euclidean_distance",
    "std_distance",
    "theoretical_squared_distance_cv",
    "theoretical_squared_distance_expectation",
    "theoretical_squared_distance_variance",
    "validate_squared_distance_theory",
    "variance_distance",
]
