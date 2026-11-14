import json
from pathlib import Path

import cv2
import numpy as np
import pytest
from PyQt6 import sip
from PyQt6.QtCore import QObject, QTimer, QUrl, Qt, QMetaObject, qInstallMessageHandler
from PyQt6.QtGui import QFontDatabase, QRawFont, QWindow
from PyQt6.QtQml import QQmlApplicationEngine, QQmlExpression
from PyQt6.QtQuick import QQuickWindow

from app.backend.datasets.mnist_dataset import load_mnist_dataset
from app.backend.machine_learning.knn_classifier import evaluate_knn_classifier
from app.services.experiment_export import export_experiment_results
from app.viewmodels.feature_lab_view_model import FeatureLabViewModel


@pytest.fixture
def window(qt_app, small_mnist, monkeypatch):
    import app.viewmodels.feature_lab_view_model as module
    monkeypatch.setattr(module, "load_mnist_dataset", lambda: small_mnist)
    messages = []
    previous = qInstallMessageHandler(lambda kind, context, message: messages.append(message))
    engine = QQmlApplicationEngine()
    view_model = FeatureLabViewModel()
    try:
        engine.setInitialProperties({"viewModel": view_model})
        engine.load(QUrl.fromLocalFile(str(Path(__file__).resolve().parents[1] / "ui" / "Main.qml")))
        assert engine.rootObjects(), messages
        root = engine.rootObjects()[0]
        assert isinstance(root, QQuickWindow)
        yield root, view_model, engine, messages
    finally:
        view_model.shutdown()
        sip.delete(engine)
        qInstallMessageHandler(previous)


def assert_no_qml_errors(messages):
    assert not [message for message in messages if any(word in message for word in (
        "TypeError", "ReferenceError", "Unable to assign", "Binding loop", "failed to load", "Cannot load", "is not defined",
    ))], messages


def visual_items(item, name):
    """Repeater delegates belong to the visual tree, not always the QObject tree."""
    found = [item] if item.objectName() == name else []
    for child in item.childItems():
        found.extend(visual_items(child, name))
    return found


def test_maximized_window_preserves_work_area_and_custom_close_control(window, wait_until, tmp_path):
    root, _, _, messages = window
    wait_until(lambda: root.visibility() == QWindow.Visibility.Maximized)
    assert root.screen().availableGeometry().contains(root.geometry())
    assert root.flags() & Qt.WindowType.FramelessWindowHint
    assert not root.flags() & Qt.WindowType.WindowMinimizeButtonHint
    assert not root.flags() & Qt.WindowType.WindowMaximizeButtonHint
    assert root.findChild(QObject, "customTitleBar") is not None
    close_button = root.findChild(QObject, "closeWindowButton")
    assert close_button is not None
    assert close_button.property("visible")
    root.showNormal()
    wait_until(lambda: root.visibility() == QWindow.Visibility.Maximized)
    root.showMinimized()
    wait_until(lambda: root.visibility() == QWindow.Visibility.Maximized)
    root.showFullScreen()
    wait_until(lambda: root.visibility() == QWindow.Visibility.Maximized)
    assert root.screen().availableGeometry().contains(root.geometry())
    wait_until(lambda: not root.grabWindow().isNull())
    assert root.grabWindow().save(str(tmp_path / "maximized-window.png"))
    QMetaObject.invokeMethod(close_button, "clicked")
    wait_until(lambda: not root.isVisible())
    assert_no_qml_errors(messages)


def test_qml_navigation_after_scikit_learn_initialization(window, wait_until):
    root, view_model, _, messages = window
    assert root.isVisible()
    assert QFontDatabase.families()
    assert QRawFont.fromFont(root.property("font")).supportsCharacter("A")
    assert not view_model.hasMNISTDataset
    view_model.initializeDataset()
    # Navigation and dataset bindings must agree after initialization.
    for page in view_model._pages:
        view_model.navigateTo(page)
        name = page[0].lower() + page[1:] + "Page"
        wait_until(lambda: root.findChild(QObject, name) is not None)
    wait_until(lambda: not view_model.datasetLoading)
    wait_until(lambda: not view_model.knnEvaluationRunning)
    assert view_model.datasetSampleCount == 700
    assert view_model.knnTestAccuracy > 0.80
    assert_no_qml_errors(messages)


def test_uploaded_image_predicts_when_dataset_finishes_loading(window, tmp_path, wait_until, small_mnist):
    root, view_model, engine, messages = window
    dataset = small_mnist
    sample_index = int(dataset.test_indices[0])
    image = np.rint(dataset.images[sample_index]).astype(np.uint8)
    image_path = tmp_path / "digit.png"
    success, encoded = cv2.imencode(".png", image)
    assert success
    encoded.tofile(image_path)
    view_model.navigateTo("ImageAnalysis")
    view_model.setSelectedImage(image_path.as_uri())
    assert view_model.hasProcessedImage
    assert not view_model.hasKnnPrediction
    view_model._on_dataset_loaded(dataset, evaluate_knn_classifier(dataset)["test_accuracy"], "")
    wait_until(lambda: view_model.hasKnnPrediction)
    assert view_model.knnPredictedLabel == dataset.labels[sample_index]
    assert len(view_model.knnNeighbors) == 5
    for neighbor in view_model.knnNeighbors:
        assert neighbor["index"] in dataset.train_indices
        assert neighbor["label"] == dataset.labels[neighbor["index"]]
        assert neighbor["source"].startswith("data:image/png;base64,")
    assert root.findChild(QObject, "predictionText") is not None
    assert root.findChild(QObject, "predictionText").property("text") == f"Predicted digit: {view_model.knnPredictedLabel}"
    wait_until(lambda: len(visual_items(root.contentItem(), "neighborImagePreview")) == 5)
    previews = visual_items(root.contentItem(), "neighborImagePreview")
    previews += visual_items(root.contentItem(), "originalImagePreview")
    previews += visual_items(root.contentItem(), "processedImagePreview")
    assert len(previews) == 7
    wait_until(lambda: all(QQmlExpression(engine.rootContext(), item, "Number(status)").evaluate()[0] == 1 for item in previews))
    assert root.grabWindow().save(str(tmp_path / "image-analysis-window.png"))
    view_model.clearSelectedImage()
    assert not view_model.hasKnnPrediction
    assert view_model.knnNeighbors == []
    view_model.setSelectedImage(str(tmp_path / "missing.png"))
    assert view_model.processingError
    assert not view_model.hasProcessedImage
    assert_no_qml_errors(messages)


def test_complete_experiments_render_without_blocking_gui(window, wait_until, tmp_path, qt_app, small_mnist):
    root, view_model, engine, messages = window
    view_model._on_dataset_loaded(small_mnist, 0.98, "")
    heartbeats = []
    timer = QTimer()
    timer.setInterval(10)
    timer.timeout.connect(lambda: heartbeats.append(1))
    timer.start()
    try:
        view_model.runDimensionalityExperiments()
        task = view_model._experiment_task
        view_model.runDimensionalityExperiments()
        assert view_model._experiment_task is task  # Repeated clicks cannot start duplicate jobs.
        assert view_model.experimentsRunning
        view_model.navigateTo("Results")
        wait_until(lambda: not view_model.experimentsRunning, timeout=90)
        assert not view_model.experimentError
        assert len(view_model.dimensionalityCharts) == 6
        assert len(view_model.dimensionalityComparisonRows) == 8
        assert len(heartbeats) > 5
        # QML must instantiate the completed chart and table delegates.
        wait_until(lambda: len(visual_items(root.contentItem(), "resultChartImage")) == 6)
        chart_images = visual_items(root.contentItem(), "resultChartImage")
        def images_ready():
            return all(QQmlExpression(engine.rootContext(), item, "Number(status)").evaluate()[0] == 1 for item in chart_images)
        wait_until(images_ready)
        screenshot = root.grabWindow()
        assert not screenshot.isNull()
        assert screenshot.save(str(tmp_path / "results-window.png"))
        path = export_experiment_results(view_model._dimensionality_results, tmp_path / "records")
        record = json.loads(path.read_text(encoding="utf-8"))
        assert record["metadata"]["subset_seed"] == 42
        assert len(record["metadata"]["train_indices"]) == 600
        assert len(record["comparison_rows"]) == 8
        assert len(list(path.parent.glob("*.png"))) == 6
        assert (path.parent / "comparison.csv").is_file()
        assert_no_qml_errors(messages)
    finally:
        timer.stop()


def test_experiment_failure_is_reported_and_previous_results_survive(window, wait_until, monkeypatch, small_mnist):
    import app.viewmodels.feature_lab_view_model as module

    _, view_model, _, _ = window
    view_model._on_dataset_loaded(small_mnist, 0.98, "")
    view_model._dimensionality_comparison_rows = [{"label": "previous result"}]
    def fail(dataset, **kwargs):
        raise RuntimeError("Experiment failed deliberately")
    monkeypatch.setattr(module, "run_experiment_suite", fail)
    view_model.runDimensionalityExperiments()
    wait_until(lambda: not view_model.experimentsRunning)
    assert view_model.experimentError == "Experiment failed deliberately"
    assert view_model.dimensionalityComparisonRows == [{"label": "previous result"}]


def test_supplied_two_is_predicted_in_image_analysis_ui(window, wait_until, small_mnist):
    root, view_model, _, messages = window
    dataset = small_mnist
    view_model._on_dataset_loaded(dataset, evaluate_knn_classifier(dataset)["test_accuracy"], "")
    image = Path(__file__).parent / "fixtures" / "digit_2.png"
    view_model.navigateTo("ImageAnalysis")
    view_model.setSelectedImage(image.resolve().as_uri())
    wait_until(lambda: view_model.hasKnnPrediction)
    assert view_model.knnPredictedLabel == 2
    assert root.findChild(QObject, "predictionText").property("text") == "Predicted digit: 2"
    assert "inverted" in view_model.preprocessingSummary
    assert len(view_model.knnNeighbors) == 5
    view_model.clearSelectedImage()
    assert view_model.preprocessingSummary == ""
    assert not view_model.hasKnnPrediction
    assert_no_qml_errors(messages)
