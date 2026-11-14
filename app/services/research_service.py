"""Application operations independent of QML and Qt object lifetimes."""

import numpy as np

from app.backend.calculations.distance_metrics import analyze_distance_to_samples, coefficient_of_variation, relative_distance_contrast
from app.backend.datasets.mnist_dataset import MNISTDataset


def run_experiment_suite(dataset: MNISTDataset, *, cancel_requested=None) -> dict:
    from app.backend.experiments.dimensionality_experiments import run_all_dimensionality_experiments
    from app.backend.experiments.result_visualizations import build_result_visualizations

    results = run_all_dimensionality_experiments(dataset=dataset, cancel_requested=cancel_requested)
    return {"results": results, "visualizations": build_result_visualizations(results)}


def analyze_distance_query(dataset: MNISTDataset, test_position: int) -> dict:
    from app.backend.experiments.result_visualizations import render_distance_distribution_chart

    if test_position < 0 or test_position >= len(dataset.test_indices):
        raise ValueError("Select a query from the held-out test split.")
    query_index = int(dataset.test_indices[test_position])
    training_indices = dataset.train_indices
    analysis = analyze_distance_to_samples(dataset.feature_vectors[query_index], dataset.feature_vectors[training_indices])
    distances = analysis["distance_distribution"]
    nearest = int(training_indices[analysis["nearest_sample_index"]])
    farthest = int(training_indices[analysis["farthest_sample_index"]])
    return {
        "result": {
            "query_position": test_position + 1, "query_index": query_index,
            "query_label": int(dataset.labels[query_index]), "reference_count": len(training_indices),
            "minimum_distance": analysis["minimum_distance"], "maximum_distance": analysis["maximum_distance"],
            "mean_distance": analysis["mean_distance"], "standard_deviation": analysis["std_distance"],
            "variance": float(np.var(distances)), "coefficient_of_variation": coefficient_of_variation(distances),
            "relative_distance_contrast": relative_distance_contrast(distances),
            "nearest_sample_index": nearest, "nearest_sample_label": int(dataset.labels[nearest]),
            "nearest_distance": analysis["nearest_distance"],
            "farthest_sample_index": farthest, "farthest_sample_label": int(dataset.labels[farthest]),
            "farthest_distance": analysis["farthest_distance"],
        },
        "chart": render_distance_distribution_chart(distances),
    }
