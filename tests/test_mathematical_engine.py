import numpy as np
import pytest

from app.backend.calculations import (
    analyze_distance_to_samples,
    coefficient_of_variation,
    distance_standard_deviation,
    distance_variance,
    euclidean_distance,
    mean_distance,
    relative_distance_contrast,
    squared_distance_coefficient_of_variation,
    squared_euclidean_distance,
    validate_squared_distance_theory,
    theoretical_squared_distance_cv,
)


def test_euclidean_and_squared_distance_metrics():
    x = np.array([1.0, 2.0, 3.0])
    y = np.array([4.0, 6.0, 3.0])

    assert np.isclose(euclidean_distance(x, y), 5.0)
    assert np.isclose(squared_euclidean_distance(x, y), 25.0)


def test_distance_statistics_and_cv():
    distances = np.array([1.0, 3.0, 5.0])

    assert np.isclose(mean_distance(distances), 3.0)
    assert np.isclose(distance_variance(distances), 8.0 / 3.0)
    assert np.isclose(distance_standard_deviation(distances), np.std(distances, ddof=0))
    assert np.isclose(coefficient_of_variation(distances), np.std(distances) / np.mean(distances))


def test_relative_distance_contrast_handles_zero_minimum():
    assert np.isinf(relative_distance_contrast(np.array([0.0, 0.0, 3.0])))
    assert np.isclose(relative_distance_contrast(np.array([1.0, 2.0, 4.0])), 3.0)


def test_distance_analysis_reports_minimum_and_nearest_samples():
    query = np.array([0.0, 0.0])
    references = np.array([[0.0, 0.0], [3.0, 0.0], [0.0, 4.0]])

    result = analyze_distance_to_samples(query, references)

    assert result["minimum_distance"] == 0.0
    assert result["maximum_distance"] == 4.0
    assert np.isclose(result["mean_distance"], 7.0 / 3.0)
    assert result["nearest_sample_index"] == 0
    assert result["farthest_sample_index"] == 2
    assert result["distance_distribution"].shape == (3,)


def test_squared_distance_theory_matches_theoretical_expectations():
    summary = validate_squared_distance_theory(dimensions=(2, 10, 100), samples_per_dimension=4000, random_state=42)

    for dimension, stats in summary.items():
        mean_theory = dimension / 6.0
        variance_theory = 7.0 * dimension / 180.0
        cv_theory = np.sqrt(7.0 / (5.0 * dimension))

        assert np.isclose(stats["mean_squared_distance"], mean_theory, rtol=0.15)
        assert np.isclose(stats["variance_squared_distance"], variance_theory, rtol=0.15)
        assert np.isclose(stats["squared_distance_cv"], cv_theory, rtol=0.15)
        assert np.isfinite(stats["ordinary_distance_cv"])
        assert np.isclose(stats["ordinary_distance_cv"], stats["coefficient_of_variation"])


def test_squared_distance_cv_is_not_the_same_as_ordinary_cv():
    values = np.array([1.0, 2.0, 3.0, 4.0])

    assert np.isclose(squared_distance_coefficient_of_variation(values), np.std(np.square(values)) / np.mean(np.square(values)))
    assert not np.isclose(
        squared_distance_coefficient_of_variation(values),
        coefficient_of_variation(values),
    )


@pytest.mark.parametrize("metric", [mean_distance, distance_variance, distance_standard_deviation, coefficient_of_variation, relative_distance_contrast, squared_distance_coefficient_of_variation])
@pytest.mark.parametrize("values", [[], [np.nan], [np.inf], [-1.0, 2.0]])
def test_distance_statistics_reject_invalid_values(metric, values):
    with pytest.raises(ValueError):
        metric(values)


def test_small_nonzero_distances_are_not_treated_as_zero():
    values = np.array([1e-12, 3e-12])
    assert coefficient_of_variation(values) == pytest.approx(0.5)
    assert relative_distance_contrast(values) == pytest.approx(2.0)
    assert squared_distance_coefficient_of_variation(values) == pytest.approx(0.8)
    assert coefficient_of_variation([0, 0]) == 0
    assert relative_distance_contrast([0, 0]) == 0


@pytest.mark.parametrize("dimension", [0, -1, 1.5, True])
def test_theory_rejects_invalid_dimensions(dimension):
    with pytest.raises(ValueError):
        theoretical_squared_distance_cv(dimension)


@pytest.mark.parametrize("values", [[], [np.nan], [np.inf]])
def test_vector_distances_reject_empty_or_nonfinite_inputs(values):
    with pytest.raises(ValueError):
        euclidean_distance(values, values)
    with pytest.raises(ValueError):
        squared_euclidean_distance(values, values)


def test_query_analysis_rejects_invalid_shapes_and_nonfinite_data():
    for query, references in [([0, 1], [[[1, 2]]]), ([0, np.nan], [[0, 1]]), ([0, 1], [[np.inf, 0]]), ([0, 1], [[0]])]:
        with pytest.raises(ValueError):
            analyze_distance_to_samples(query, references)
