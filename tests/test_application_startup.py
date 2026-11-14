import time
import os
import subprocess
import sys
from pathlib import Path
from threading import Event

from app.viewmodels import feature_lab_view_model as view_models


def wait_for_dataset(qt_app, view_model):
    deadline = time.monotonic() + 5
    while (view_model.datasetLoading or view_model.knnEvaluationRunning) and time.monotonic() < deadline:
        qt_app.processEvents()
        time.sleep(0.005)
    assert not view_model.datasetLoading, "Dataset loader did not finish"
    assert not view_model.knnEvaluationRunning, "Baseline evaluation did not finish"


def test_mnist_dataset_is_ready_when_initialization_returns(qt_app, monkeypatch):
    calls = []
    dataset = object()
    monkeypatch.setattr(view_models, "load_mnist_dataset", lambda: calls.append("load") or dataset)
    monkeypatch.setattr(view_models, "evaluate_knn_classifier", lambda dataset, k, **kwargs: {"test_accuracy": 0.98})
    view_model = view_models.FeatureLabViewModel()
    try:
        assert calls == []
        assert not view_model.hasMNISTDataset
        view_model.initializeDataset()
        assert not view_model.datasetLoading
        assert view_model.hasMNISTDataset
        wait_for_dataset(qt_app, view_model)
        assert calls == ["load"]
        assert view_model.hasMNISTDataset
        assert view_model.knnTestAccuracy == 0.98
        assert view_model.datasetError == ""
        view_model.initializeDataset()
        assert calls == ["load"]
    finally:
        view_model.shutdown()


def test_dataset_failure_is_reported_without_crashing(qt_app, monkeypatch):
    def fail_loading():
        raise RuntimeError("Dataset could not load")

    monkeypatch.setattr(view_models, "load_mnist_dataset", fail_loading)
    view_model = view_models.FeatureLabViewModel()
    try:
        view_model.initializeDataset()
        wait_for_dataset(qt_app, view_model)
        assert not view_model.hasMNISTDataset
        assert view_model.datasetError == "Dataset could not load"
    finally:
        view_model.shutdown()


def test_baseline_failure_does_not_discard_dataset_or_block_experiments(qt_app, wait_until, monkeypatch):
    dataset = object()
    monkeypatch.setattr(view_models, "load_mnist_dataset", lambda: dataset)
    def fail_evaluation(dataset, k, **kwargs):
        raise RuntimeError("Baseline evaluation failed")
    monkeypatch.setattr(view_models, "evaluate_knn_classifier", fail_evaluation)
    calls = []
    monkeypatch.setattr(view_models, "run_experiment_suite", lambda data, **kwargs: calls.append(data) or {
        "results": {}, "visualizations": {"charts": [], "comparison_rows": []},
    })
    view_model = view_models.FeatureLabViewModel()
    try:
        view_model.initializeDataset()
        wait_for_dataset(qt_app, view_model)
        assert view_model.hasMNISTDataset
        assert view_model.datasetError == ""
        assert view_model.knnEvaluationError == "Baseline evaluation failed"
        assert not view_model.hasKnnEvaluation
        view_model.runDimensionalityExperiments()
        wait_until(lambda: not view_model.experimentsRunning)
        assert calls == [dataset]
        assert view_model.experimentError == ""
    finally:
        view_model.shutdown()


def test_dataset_is_available_and_experiments_run_before_baseline_finishes(wait_until, monkeypatch):
    dataset = object()
    release_evaluation = Event()
    monkeypatch.setattr(view_models, "load_mnist_dataset", lambda: dataset)
    def evaluate(data, k, **kwargs):
        if not release_evaluation.wait(10):
            raise TimeoutError("Test did not release baseline evaluation")
        return {"test_accuracy": 0.98}
    monkeypatch.setattr(view_models, "evaluate_knn_classifier", evaluate)
    calls = []
    monkeypatch.setattr(view_models, "run_experiment_suite", lambda data, **kwargs: calls.append(data) or {
        "results": {}, "visualizations": {"charts": [], "comparison_rows": []},
    })
    view_model = view_models.FeatureLabViewModel()
    try:
        # Running experiments with no dataset must load it and continue automatically.
        view_model.runDimensionalityExperiments()
        wait_until(lambda: view_model.hasMNISTDataset and not view_model.datasetLoading)
        wait_until(lambda: not view_model.experimentsRunning and bool(calls))
        assert view_model.knnEvaluationRunning
        assert calls == [dataset]
        release_evaluation.set()
        wait_until(lambda: not view_model.knnEvaluationRunning)
        assert view_model.knnTestAccuracy == 0.98
    finally:
        release_evaluation.set()
        view_model.shutdown()


def test_dataset_loading_can_be_retried_after_failure(qt_app, monkeypatch):
    def fail():
        raise RuntimeError("Dataset load failed")
    monkeypatch.setattr(view_models, "load_mnist_dataset", fail)
    view_model = view_models.FeatureLabViewModel()
    try:
        view_model.initializeDataset()
        wait_for_dataset(qt_app, view_model)
        assert not view_model.hasMNISTDataset
        assert view_model.datasetError == "Dataset load failed"
        monkeypatch.setattr(view_models, "load_mnist_dataset", lambda: object())
        monkeypatch.setattr(view_models, "evaluate_knn_classifier", lambda dataset, k, **kwargs: {"test_accuracy": 0.98})
        view_model.initializeDataset()
        wait_for_dataset(qt_app, view_model)
        assert view_model.hasMNISTDataset
        assert view_model.datasetError == ""
    finally:
        view_model.shutdown()


def test_main_entry_point_opens_and_closes_safely_from_another_directory(tmp_path):
    project = Path(__file__).resolve().parents[1]
    script = """
import runpy
import sys
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QGuiApplication
project = sys.argv[1]
sys.path.insert(0, project)
original_exec = QGuiApplication.exec
def bounded_exec():
    from app.viewmodels.feature_lab_view_model import FeatureLabViewModel
    vm = QGuiApplication.instance().findChild(FeatureLabViewModel)
    assert vm.hasMNISTDataset, vm.datasetError
    assert not vm.datasetLoading
    assert vm.datasetSampleCount == 70000
    assert vm.datasetFeatureCount == 784
    def close():
        assert any(window.isVisible() for window in QGuiApplication.allWindows())
        print('WINDOW_VISIBLE', flush=True)
        QGuiApplication.instance().quit()
    QTimer.singleShot(100, close)
    return original_exec()
QGuiApplication.exec = staticmethod(bounded_exec)
runpy.run_path(project + '/main.py', run_name='__main__')
"""
    result = subprocess.run([sys.executable, "-c", script, str(project)], cwd=tmp_path, env=os.environ.copy(), capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "WINDOW_VISIBLE" in result.stdout


def test_real_entry_point_loads_dataset_and_qml_button_runs_experiments(tmp_path):
    project = Path(__file__).resolve().parents[1]
    script = """
import runpy
import sys
import time
from PyQt6.QtCore import QObject, QMetaObject, QTimer
from PyQt6.QtGui import QGuiApplication
project = sys.argv[1]
sys.path.insert(0, project)
from app.viewmodels.feature_lab_view_model import FeatureLabViewModel
original_exec = QGuiApplication.exec
deadline = time.monotonic() + 150
errors = []
clicked = False
def inspect():
    global clicked
    app = QGuiApplication.instance()
    try:
        vm = app.findChild(FeatureLabViewModel)
        assert time.monotonic() < deadline, 'Dataset/experiments timed out: ' + vm.datasetError + vm.experimentError
        assert not vm.datasetError, vm.datasetError
        if vm.hasMNISTDataset and not clicked:
            assert vm.datasetSampleCount == 70000
            vm.navigateTo('Results')
            root = next(window for window in app.allWindows() if window.isVisible())
            button = root.findChild(QObject, 'runExperimentsButton')
            assert button is not None
            assert button.property('enabled'), 'Run button remained disabled after dataset became ready'
            QMetaObject.invokeMethod(button, 'clicked')
            assert vm.experimentsRunning
            clicked = True
            print('DATASET_READY_AND_RUN_BUTTON_CLICKED', flush=True)
        if clicked and not vm.experimentsRunning:
            assert not vm.experimentError, vm.experimentError
            assert len(vm.dimensionalityCharts) == 6
            assert len(vm.dimensionalityComparisonRows) == 8
            print('SIX_CHARTS_AND_EIGHT_ROWS', flush=True)
            app.quit()
            return
        QTimer.singleShot(50, inspect)
    except Exception as error:
        errors.append(str(error))
        app.quit()
def instrumented_exec():
    app = QGuiApplication.instance()
    vm = app.findChild(FeatureLabViewModel)
    assert vm.hasMNISTDataset, 'Dataset must be ready before entering the GUI event loop'
    assert not vm.datasetLoading
    root = next(window for window in app.allWindows() if window.isVisible())
    assert not root.findChild(QObject, 'datasetStatusText').property('visible'), 'Loading banner must be hidden on the first window'
    QTimer.singleShot(0, inspect)
    result = original_exec()
    if errors:
        raise RuntimeError('; '.join(errors))
    return result
QGuiApplication.exec = staticmethod(instrumented_exec)
runpy.run_path(project + '/main.py', run_name='__main__')
"""
    result = subprocess.run([sys.executable, "-c", script, str(project)], cwd=tmp_path, env=os.environ.copy(), capture_output=True, text=True, timeout=180)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "DATASET_READY_AND_RUN_BUTTON_CLICKED" in result.stdout
    assert "SIX_CHARTS_AND_EIGHT_ROWS" in result.stdout
