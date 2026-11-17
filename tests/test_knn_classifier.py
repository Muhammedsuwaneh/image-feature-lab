import numpy as np
import pytest
from dataclasses import replace
import json

from app.backend.datasets.mnist_dataset import load_mnist_dataset
from app.backend.machine_learning import (
    evaluate_knn_classifier,
    predict_knn_for_feature_vector,
)


def test_knn_classifier_has_good_mnist_subset_accuracy(small_mnist):
    dataset = small_mnist

    result = evaluate_knn_classifier(dataset, k=5)

    assert result["k"] == 5
    assert result["test_accuracy"] > 0.80
    assert result["prediction_count"] == len(dataset.test_indices)
    assert result["nearest_neighbor_labels"].shape[0] == len(dataset.test_indices)
    assert result["nearest_neighbor_distances"].shape[0] == len(dataset.test_indices)

    np.testing.assert_array_equal(
        result["nearest_neighbor_labels"],
        dataset.labels[dataset.train_indices[result["nearest_neighbor_indices"]]],
    )


def test_knn_prediction_for_feature_vector_returns_label_and_neighbors(small_mnist):
    dataset = small_mnist
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
    np.testing.assert_allclose(
        distances, np.take_along_axis(expected_distances, expected_indices, axis=1)
    )


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


def test_partial_selection_resolves_cutoff_ties_by_training_order():
    from app.backend.machine_learning.knn_classifier import KNNModel

    model = KNNModel(np.array([[1.0], [-1.0], [1.0], [-1.0]]), np.array([9, 2, 9, 2]), k=2)
    np.testing.assert_array_equal(model.kneighbors([[0]], return_distance=False), [[0, 1]])


def test_float32_mnist_distances_match_direct_distances_across_reference_blocks():
    from app.backend.machine_learning.knn_classifier import KNNModel

    rng = np.random.default_rng(42)
    training = rng.random((4100, 28), dtype=np.float32)
    queries = training[4094:4099].copy()
    model = KNNModel(training, np.arange(len(training)) % 10, k=5)
    distances, indices = model.kneighbors(queries)
    direct = np.linalg.norm(
        training.astype(np.float64)[None, :, :] - queries.astype(np.float64)[:, None, :], axis=2
    )
    expected = np.argsort(direct, axis=1, kind="stable")[:, :5]
    np.testing.assert_array_equal(indices, expected)
    np.testing.assert_allclose(distances, np.take_along_axis(direct, expected, axis=1), atol=1e-12)
    np.testing.assert_array_equal(distances[:, 0], 0)


def test_long_evaluation_can_be_cancelled(small_mnist):
    with pytest.raises(InterruptedError):
        evaluate_knn_classifier(small_mnist, cancel_requested=lambda: True)


def test_accuracy_cache_is_validated_against_values_labels_and_k(
    small_mnist, tmp_path, monkeypatch
):
    from app.backend.machine_learning import knn_classifier as module

    monkeypatch.setattr(module, "CACHE_DIRECTORY", tmp_path)
    monkeypatch.setattr(module, "supports_baseline_cache", lambda dataset: True)
    measured = module.evaluate_knn_classifier(small_mnist)

    def forbid_recalculation(*args, **kwargs):
        raise RuntimeError("Cache miss")

    monkeypatch.setattr(module, "train_knn_classifier", forbid_recalculation)
    cached = module.evaluate_knn_classifier(small_mnist, accuracy_only=True)

    assert cached["cached"]
    assert cached["test_accuracy"] == measured["test_accuracy"]

    labels = small_mnist.labels.copy()
    labels[0] = (labels[0] + 1) % 10
    labels.setflags(write=False)
    altered = replace(small_mnist, labels=labels)

    with pytest.raises(RuntimeError, match="Cache miss"):
        module.evaluate_knn_classifier(altered, accuracy_only=True)

    with pytest.raises(RuntimeError, match="Cache miss"):
        module.evaluate_knn_classifier(small_mnist, k=3, accuracy_only=True)

    path = tmp_path / "knn-baseline-k5.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    record["fingerprint"] = "stale"
    path.write_text(json.dumps(record), encoding="utf-8")

    with pytest.raises(RuntimeError, match="Cache miss"):
        module.evaluate_knn_classifier(small_mnist, accuracy_only=True)


def test_accuracy_cache_is_reserved_for_full_mnist(mnist_data, small_mnist):
    from app.backend.machine_learning.knn_classifier import supports_baseline_cache

    assert supports_baseline_cache(mnist_data)
    assert not supports_baseline_cache(small_mnist)
