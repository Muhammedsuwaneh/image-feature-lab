import numpy as np

from app.backend.datasets.digits_dataset import load_digits_dataset
from app.backend.machine_learning import (
    evaluate_knn_classifier,
    predict_knn_for_feature_vector,
)


def test_knn_classifier_has_strong_digits_test_accuracy():
    dataset = load_digits_dataset()

    result = evaluate_knn_classifier(dataset, k=5)

    assert result["k"] == 5
    assert result["test_accuracy"] > 0.96
    assert result["prediction_count"] == len(dataset.test_indices)
    assert result["nearest_neighbor_labels"].shape[0] == len(dataset.test_indices)
    assert result["nearest_neighbor_distances"].shape[0] == len(dataset.test_indices)


def test_knn_prediction_for_feature_vector_returns_label_and_neighbors():
    dataset = load_digits_dataset()
    sample = dataset.feature_vectors[dataset.train_indices[0]]

    result = predict_knn_for_feature_vector(sample, dataset, k=5)

    assert result["predicted_label"] in dataset.classes
    assert len(result["neighbor_labels"]) == 5
    assert len(result["neighbor_distances"]) == 5
    assert np.all(np.isfinite(result["neighbor_distances"]))
