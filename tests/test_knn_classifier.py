import numpy as np
import pytest

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
    np.testing.assert_array_equal(
        result["nearest_neighbor_labels"],
        dataset.labels[dataset.train_indices[result["nearest_neighbor_indices"]]],
    )


def test_knn_prediction_for_feature_vector_returns_label_and_neighbors():
    dataset = load_digits_dataset()
    sample = dataset.feature_vectors[dataset.train_indices[0]]

    result = predict_knn_for_feature_vector(sample, dataset, k=5)

    assert result["predicted_label"] in dataset.classes
    assert len(result["neighbor_labels"]) == 5
    assert len(result["neighbor_distances"]) == 5
    assert np.all(np.isfinite(result["neighbor_distances"]))
    np.testing.assert_array_equal(
        result["neighbor_labels"],
        dataset.labels[dataset.train_indices[result["neighbor_indices"]]],
    )


def test_batched_neighbors_match_direct_distances():
    from app.backend.machine_learning.knn_classifier import KNNModel

    rng = np.random.default_rng(42)
    training = rng.normal(size=(45, 8))
    queries = rng.normal(size=(37, 8))
    model = KNNModel(training, np.arange(45) % 10, k=5)
    expected_distances = np.linalg.norm(training[None, :, :] - queries[:, None, :], axis=2)
    expected_indices = np.argsort(expected_distances, axis=1)[:, :5]

    distances, indices = model.kneighbors(queries)

    np.testing.assert_array_equal(indices, expected_indices)
    np.testing.assert_allclose(distances, np.take_along_axis(expected_distances, expected_indices, axis=1))


@pytest.mark.parametrize("k", [0, -1, 1.5, True, 4])
def test_knn_rejects_invalid_k(k):
    from app.backend.machine_learning.knn_classifier import KNNModel

    with pytest.raises(ValueError):
        KNNModel(np.zeros((3, 2)), np.array([0, 1, 2]), k=k)


def test_knn_rejects_nonfinite_features_and_malformed_queries():
    from app.backend.machine_learning.knn_classifier import KNNModel

    with pytest.raises(ValueError):
        KNNModel(np.array([[np.nan]]), np.array([0]), k=1)
    model = KNNModel(np.array([[0.0], [1.0]]), np.array([0, 1]), k=1)
    for query in [0, [[[0]]], [[np.nan]], [[np.inf]], [[1, 2]]]:
        with pytest.raises(ValueError):
            model.predict(query)
    with pytest.raises(ValueError):
        model.kneighbors([[0]], n_neighbors=1.5)


def test_knn_ties_use_training_order_then_smallest_label():
    from app.backend.machine_learning.knn_classifier import KNNModel

    model = KNNModel(np.array([[1.0], [-1.0], [1.0], [-1.0]]), np.array([9, 2, 9, 2]), k=4)
    np.testing.assert_array_equal(model.kneighbors([[0]], return_distance=False), [[0, 1, 2, 3]])
    assert model.predict([[0]])[0] == 2
