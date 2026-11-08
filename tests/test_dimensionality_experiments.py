import base64

import numpy as np

from app.backend.experiments.dimensionality_experiments import (
    run_irrelevant_feature_experiment,
    run_standardization_pca_experiment,
    run_synthetic_dimension_experiment,
)
from app.backend.experiments.result_visualizations import build_result_visualizations


def test_synthetic_dimension_experiment_matches_theoretical_moments():
    results = run_synthetic_dimension_experiment(dimensions=(2, 4, 8), samples_per_dimension=800, seed=42)

    assert set(results) >= {2, 4, 8}
    for dimension, stats in results.items():
        assert np.isclose(stats["mean_squared_distance"], dimension / 6.0, rtol=0.2)
        assert np.isclose(stats["variance_squared_distance"], 7.0 * dimension / 180.0, rtol=0.25)
        assert stats["coefficient_of_variation"] > 0.0


def test_irrelevant_feature_experiment_preserves_original_dataset_shape():
    results = run_irrelevant_feature_experiment(feature_sizes=(64, 96), seeds=(0, 1))

    assert set(results) == {64, 96}
    for _, metrics in results.items():
        assert metrics["mean_distance"] >= 0.0
        assert metrics["distance_std"] >= 0.0
        assert metrics["test_accuracy"] > 0.0
        assert len(metrics["nearest_distances"]) > 0
        assert len(metrics["farthest_distances"]) > 0


def test_standardization_and_pca_experiment_uses_train_only_preprocessing():
    results = run_standardization_pca_experiment(random_state=7)

    assert set(results) == {"original_64", "standardized", "pca_16", "pca_32"}
    assert results["original_64"]["test_accuracy"] > 0.0
    assert results["pca_16"]["test_accuracy"] > 0.0
    assert results["pca_32"]["test_accuracy"] > 0.0


def test_result_visualizations_use_real_experiment_outputs():
    experiment_results = {
        "synthetic": run_synthetic_dimension_experiment(
            dimensions=(2, 4, 8), samples_per_dimension=400, seed=42
        ),
        "irrelevant_features": run_irrelevant_feature_experiment(
            feature_sizes=(64, 96), seeds=(0, 1)
        ),
        "standardization_and_pca": run_standardization_pca_experiment(),
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
    assert set(rows) >= {"Irrelevant 96", "Original", "Standardized", "PCA 16", "PCA 32"}
    assert np.isclose(
        rows["PCA 16"]["test_accuracy"],
        experiment_results["standardization_and_pca"]["pca_16"]["test_accuracy"],
    )
    assert np.isclose(
        rows["Irrelevant 96"]["test_accuracy"],
        experiment_results["irrelevant_features"][96]["test_accuracy"],
    )
    assert all(
        base64.b64decode(chart["source"].split(",", 1)[1]).startswith(b"\x89PNG\r\n\x1a\n")
        for chart in charts
    )
