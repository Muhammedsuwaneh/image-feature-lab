import base64

import numpy as np
import pytest

from app.backend.datasets.mnist_dataset import load_mnist_dataset, experiment_subset
from app.backend.experiments import dimensionality_experiments as experiments

from app.backend.experiments.dimensionality_experiments import (
    run_irrelevant_feature_experiment,
    run_standardization_pca_experiment,
    run_synthetic_dimension_experiment,
)
from app.backend.experiments.result_visualizations import build_result_visualizations


def test_synthetic_dimension_experiment_matches_theoretical_moments():
    results = run_synthetic_dimension_experiment(
        dimensions=(2, 4, 8), samples_per_dimension=800, seed=42
    )

    assert set(results) >= {2, 4, 8}

    for dimension, stats in results.items():
        assert np.isclose(stats["mean_squared_distance"], dimension / 6.0, rtol=0.2)
        assert np.isclose(stats["variance_squared_distance"], 7.0 * dimension / 180.0, rtol=0.25)
        assert stats["coefficient_of_variation"] > 0.0


def test_irrelevant_feature_experiment_preserves_original_dataset_shape(small_mnist):
    results = run_irrelevant_feature_experiment(
        dataset=small_mnist, feature_sizes=(784, 1024), seeds=(0, 1)
    )

    assert set(results) == {784, 1024}

    for _, metrics in results.items():
        assert metrics["mean_distance"] >= 0.0
        assert metrics["distance_std"] >= 0.0
        assert metrics["test_accuracy"] > 0.0
        assert len(metrics["nearest_distances"]) > 0
        assert len(metrics["farthest_distances"]) > 0


def test_standardization_and_pca_experiment_uses_train_only_preprocessing(small_mnist):
    results = run_standardization_pca_experiment(dataset=small_mnist, random_state=7)

    assert set(results) == {"original", "standardized", "pca_16", "pca_32"}
    assert results["original"]["test_accuracy"] > 0.0
    assert results["pca_16"]["test_accuracy"] > 0.0
    assert results["pca_32"]["test_accuracy"] > 0.0


def test_result_visualizations_use_real_experiment_outputs(small_mnist):
    experiment_results = {
        "synthetic": run_synthetic_dimension_experiment(
            dimensions=(2, 4, 8), samples_per_dimension=400, seed=42
        ),
        "irrelevant_features": run_irrelevant_feature_experiment(
            dataset=small_mnist, feature_sizes=(784, 1024), seeds=(0, 1)
        ),
        "standardization_and_pca": run_standardization_pca_experiment(dataset=small_mnist),
    }
    visualizations = build_result_visualizations(experiment_results)
    charts = visualizations["charts"]
    rows = {row["label"]: row for row in visualizations["comparison_rows"]}

    assert [chart["title"] for chart in charts] == [
        "Dimensionality comparison",
        "Distance concentration",
        "Relative distance contrast",
        "Classification performance",
        "Nearest-distance distributions",
        "Synthetic theoretical validation",
    ]
    assert len(rows) == 6
    assert set(rows) >= {"Irrelevant 1024", "Original", "Standardized", "PCA 16", "PCA 32"}
    assert np.isclose(
        rows["PCA 16"]["test_accuracy"],
        experiment_results["standardization_and_pca"]["pca_16"]["test_accuracy"],
    )
    assert np.isclose(
        rows["Irrelevant 1024"]["test_accuracy"],
        experiment_results["irrelevant_features"][1024]["test_accuracy"],
    )

    for label, metrics in [
        ("Irrelevant 1024", experiment_results["irrelevant_features"][1024]),
        ("PCA 16", experiment_results["standardization_and_pca"]["pca_16"]),
    ]:
        for key in ("mean_distance", "distance_std", "coefficient_of_variation"):
            assert rows[label][key] == pytest.approx(metrics[key])

        assert rows[label]["relative_contrast"] == pytest.approx(
            metrics["relative_distance_contrast"]
        )

    assert all(
        base64.b64decode(chart["source"].split(",", 1)[1]).startswith(b"\x89PNG\r\n\x1a\n")
        for chart in charts
    )


def test_experiment_statistics_use_every_training_reference():
    training = np.array([[0, 0], [3, 0], [0, 4], [30, 40]], dtype=float)
    queries = np.array([[1, 1], [2, 2], [4, 2]], dtype=float)
    distances = np.linalg.norm(queries[:, None, :] - training[None, :, :], axis=2)
    result = experiments._evaluate_distance_knn(
        training, np.array([0, 1, 1, 0]), queries, np.array([0, 1, 1]), k=2
    )

    assert result["distance_count"] == 12
    assert result["mean_distance"] == pytest.approx(distances.mean())
    assert result["distance_variance"] == pytest.approx(distances.var())
    assert result["distance_std"] == pytest.approx(distances.std())
    assert result["coefficient_of_variation"] == pytest.approx(distances.std() / distances.mean())

    query_contrasts = (distances.max(axis=1) - distances.min(axis=1)) / distances.min(axis=1)

    assert result["relative_distance_contrast"] == pytest.approx(query_contrasts.mean())

    np.testing.assert_allclose(result["nearest_distances"], distances.min(axis=1))
    np.testing.assert_allclose(result["farthest_distances"], distances.max(axis=1))


def test_preprocessors_fit_once_and_only_on_training_samples(monkeypatch, small_mnist):
    dataset = experiment_subset(small_mnist, train_limit=500, test_limit=80, random_state=7)
    expected_training = dataset.feature_vectors[dataset.train_indices]
    expected_test = dataset.feature_vectors[dataset.test_indices]
    fitted_ids, transformed_ids = [], []

    for transformer_type in (experiments.StandardScaler, experiments.PCA):
        original_fit, original_transform = transformer_type.fit, transformer_type.transform

        def fit(self, values, *args, _original=original_fit, **kwargs):
            np.testing.assert_array_equal(values, expected_training)
            fitted_ids.append(id(self))

            return _original(self, values, *args, **kwargs)

        def transform(self, values, *args, _original=original_transform, **kwargs):
            assert id(self) in fitted_ids
            assert np.array_equal(values, expected_training) or np.array_equal(
                values, expected_test
            )

            transformed_ids.append(id(self))

            return _original(self, values, *args, **kwargs)

        monkeypatch.setattr(transformer_type, "fit", fit)
        monkeypatch.setattr(transformer_type, "transform", transform)

    results = run_standardization_pca_experiment(dataset=dataset)

    assert len(fitted_ids) == len(set(fitted_ids)) == 3
    assert all(transformed_ids.count(identity) == 2 for identity in fitted_ids)
    assert all(len(row["actual_labels"]) == len(dataset.test_indices) for row in results.values())


def test_augmentation_preserves_features_and_is_reproducible(small_mnist):
    data = small_mnist.feature_vectors
    first = experiments._build_augmented_features(data, target_dimension=1024, seed=0)
    second = experiments._build_augmented_features(data, target_dimension=1024, seed=0)
    different = experiments._build_augmented_features(data, target_dimension=1024, seed=1)
    np.testing.assert_array_equal(first[:, :784], data)
    np.testing.assert_array_equal(first, second)

    assert not np.array_equal(first[:, 784:], different[:, 784:])
    assert np.all((first[:, 784:] >= 0) & (first[:, 784:] <= 1))


@pytest.mark.parametrize(
    "kwargs",
    [{"seeds": ()}, {"feature_sizes": ()}, {"feature_sizes": (783,)}, {"feature_sizes": (784.5,)}],
)
def test_irrelevant_experiment_rejects_invalid_conditions(kwargs, small_mnist):
    with pytest.raises(ValueError):
        run_irrelevant_feature_experiment(dataset=small_mnist, **kwargs)


def test_seed_aggregation_preserves_actual_metrics(small_mnist):
    result = run_irrelevant_feature_experiment(
        dataset=small_mnist, feature_sizes=(784, 1024), seeds=(0, 1)
    )

    for metrics in result.values():
        for key in (
            "mean_distance",
            "coefficient_of_variation",
            "relative_distance_contrast",
            "test_accuracy",
        ):
            assert metrics[key] == pytest.approx(
                np.mean([seed[key] for seed in metrics["seed_results"]])
            )

        assert metrics["test_accuracy_std"] == pytest.approx(
            np.std([seed["test_accuracy"] for seed in metrics["seed_results"]])
        )

    np.testing.assert_array_equal(
        result[784]["seed_results"][0]["predicted_labels"],
        result[784]["seed_results"][1]["predicted_labels"],
    )
