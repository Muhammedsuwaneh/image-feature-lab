from pathlib import Path
import logging

import cv2
from PyQt6.QtCore import QObject, QUrl, pyqtProperty, pyqtSignal, pyqtSlot

from app.backend.datasets.digits_dataset import DigitsDataset, load_digits_dataset
from app.backend.image_processing.image_preprocessor import ProcessedImage, preprocess_image
from app.backend.machine_learning.knn_classifier import (
    evaluate_knn_classifier,
    predict_knn_for_feature_vector,
)
from app.services.background_task import BackgroundTask
from app.services.image_preview import digit_image_url
from app.services.research_service import analyze_distance_query, run_experiment_suite


class FeatureLabViewModel(QObject):
    currentPageChanged = pyqtSignal()
    selectedImageChanged = pyqtSignal()
    datasetChanged = pyqtSignal()
    dimensionalityExperimentChanged = pyqtSignal()
    distanceConcentrationChanged = pyqtSignal()

    _pages = {
        "Dashboard": "Dashboard",
        "ImageAnalysis": "Image Analysis",
        "DistanceConcentration": "Distance Concentration",
        "DimensionalityExperiments": "Dimensionality Experiments",
        "Results": "Results",
    }

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._current_page = "Dashboard"
        self._selected_image_path = ""
        self._processed_image_url = ""
        self._feature_vector: list[float] = []
        self._processing_error = ""
        self._preprocessing_summary = ""
        self._original_image_width = 0
        self._original_image_height = 0
        self._knn_k = 5
        self._knn_test_accuracy = 0.0
        self._knn_evaluation_running = False
        self._knn_evaluation_ready = False
        self._knn_evaluation_error = ""
        self._baseline_task = None
        self._knn_prediction = -1
        self._knn_neighbor_labels: list[int] = []
        self._knn_neighbor_distances: list[float] = []
        self._knn_prediction_error = ""
        self._knn_neighbors: list[dict] = []
        self._experiments_running = False
        self._experiment_error = ""
        self._distance_running = False
        self._experiment_task = None
        self._experiment_requested = False
        self._distance_task = None
        self._closing = False
        self._dimensionality_summary = "No dimensionality experiment has been run yet."
        self._dimensionality_results: dict[str, object] = {}
        self._dimensionality_charts: list[dict[str, str]] = []
        self._dimensionality_comparison_rows: list[dict[str, object]] = []
        self._distance_concentration_result: dict[str, object] = {}
        self._distance_concentration_chart = ""
        self._digits_dataset: DigitsDataset | None = None
        self._dataset_error = ""
        self._dataset_loading = False

    @pyqtSlot()
    def initializeDataset(self) -> None:
        if self._closing or self._dataset_loading or self._digits_dataset is not None:
            return
        self._dataset_loading = True
        self._dataset_error = ""
        self.datasetChanged.emit()
        try:
            dataset = load_digits_dataset()
        except Exception as error:
            logging.getLogger(__name__).exception("Could not load sklearn.datasets.load_digits")
            self._on_dataset_failed(str(error) or type(error).__name__)
        else:
            self._on_dataset_available(dataset)

    @pyqtSlot(object)
    def _on_dataset_available(self, dataset: DigitsDataset) -> None:
        if self._closing:
            return
        # Publish the data first. Baseline evaluation must not gate experiments.
        self._on_dataset_loaded(dataset, None, "")
        self.evaluateKnnClassifier()
        if self._experiment_requested:
            self._experiment_requested = False
            self.runDimensionalityExperiments()

    @pyqtSlot(str)
    def _on_dataset_failed(self, error: str) -> None:
        if self._closing:
            return
        self._on_dataset_loaded(None, None, error)
        if self._experiment_requested:
            self._experiment_requested = False
            self._experiment_error = "Could not load the Digits dataset: " + error
            self.dimensionalityExperimentChanged.emit()

    @pyqtSlot(object)
    def _on_baseline_evaluated(self, result: dict) -> None:
        if self._closing:
            return
        self._knn_test_accuracy = float(result["test_accuracy"])
        self._knn_evaluation_running = False
        self._knn_evaluation_ready = True
        self._knn_evaluation_error = ""
        self.datasetChanged.emit()

    @pyqtSlot(str)
    def _on_baseline_failed(self, error: str) -> None:
        if self._closing:
            return
        self._knn_evaluation_running = False
        self._knn_evaluation_ready = False
        self._knn_evaluation_error = error
        self.datasetChanged.emit()

    def _on_dataset_loaded(self, dataset: DigitsDataset | None, accuracy: float | None, error: str) -> None:
        if self._closing:
            return
        self._digits_dataset = dataset
        self._knn_test_accuracy = float(accuracy) if accuracy is not None else 0.0
        self._knn_evaluation_ready = dataset is not None and accuracy is not None
        self._dataset_error = error
        self._dataset_loading = False
        self.datasetChanged.emit()
        if self._feature_vector and dataset is not None:
            self._predict_selected_image()
            self.selectedImageChanged.emit()

    @pyqtSlot()
    def shutdown(self) -> None:
        # A running QThread must finish before its parent QObject is destroyed.
        self._closing = True
        for task in (self._baseline_task, self._experiment_task, self._distance_task):
            if task is not None:
                task.wait()

    @pyqtProperty(bool, notify=datasetChanged)
    def datasetLoading(self) -> bool:
        return self._dataset_loading

    @pyqtProperty(bool, notify=datasetChanged)
    def knnEvaluationRunning(self) -> bool:
        return self._knn_evaluation_running

    @pyqtProperty(bool, notify=datasetChanged)
    def hasKnnEvaluation(self) -> bool:
        return self._knn_evaluation_ready

    @pyqtProperty(str, notify=datasetChanged)
    def knnEvaluationError(self) -> str:
        return self._knn_evaluation_error

    @pyqtProperty(bool, notify=dimensionalityExperimentChanged)
    def experimentsRunning(self) -> bool:
        return self._experiments_running

    @pyqtProperty(str, notify=dimensionalityExperimentChanged)
    def experimentError(self) -> str:
        return self._experiment_error

    @pyqtProperty(bool, notify=distanceConcentrationChanged)
    def distanceAnalysisRunning(self) -> bool:
        return self._distance_running

    @pyqtProperty("QVariantList", notify=selectedImageChanged)
    def knnNeighbors(self) -> list[dict]:
        return list(self._knn_neighbors)

    @pyqtProperty(str, notify=currentPageChanged)
    def currentPage(self) -> str:
        return self._current_page

    @pyqtProperty(str, notify=currentPageChanged)
    def currentPageTitle(self) -> str:
        return self._pages[self._current_page]

    @pyqtProperty(str, notify=selectedImageChanged)
    def selectedImagePath(self) -> str:
        return self._selected_image_path

    @pyqtProperty(str, notify=selectedImageChanged)
    def selectedImageUrl(self) -> str:
        if not self._selected_image_path:
            return ""
        return QUrl.fromLocalFile(self._selected_image_path).toString()

    @pyqtProperty(str, notify=selectedImageChanged)
    def selectedImageName(self) -> str:
        return Path(self._selected_image_path).name if self._selected_image_path else ""

    @pyqtProperty(bool, notify=selectedImageChanged)
    def hasSelectedImage(self) -> bool:
        return bool(self._selected_image_path)

    @pyqtProperty(bool, notify=selectedImageChanged)
    def hasProcessedImage(self) -> bool:
        return bool(self._processed_image_url)

    @pyqtProperty(str, notify=selectedImageChanged)
    def processedImageUrl(self) -> str:
        return self._processed_image_url

    @pyqtProperty("QVariantList", notify=selectedImageChanged)
    def featureVector(self) -> list[float]:
        return self._feature_vector

    @pyqtProperty(int, notify=selectedImageChanged)
    def featureVectorLength(self) -> int:
        return len(self._feature_vector)

    @pyqtProperty(str, notify=selectedImageChanged)
    def processingError(self) -> str:
        return self._processing_error

    @pyqtProperty(str, notify=selectedImageChanged)
    def preprocessingSummary(self) -> str:
        return self._preprocessing_summary

    @pyqtProperty(int, notify=selectedImageChanged)
    def originalImageWidth(self) -> int:
        return self._original_image_width

    @pyqtProperty(int, notify=selectedImageChanged)
    def originalImageHeight(self) -> int:
        return self._original_image_height

    @pyqtProperty(bool, notify=datasetChanged)
    def hasDigitsDataset(self) -> bool:
        return self._digits_dataset is not None

    @pyqtProperty(int, notify=datasetChanged)
    def knnK(self) -> int:
        return self._knn_k

    @pyqtProperty(float, notify=datasetChanged)
    def knnTestAccuracy(self) -> float:
        return self._knn_test_accuracy

    @pyqtProperty(int, notify=selectedImageChanged)
    def knnPredictedLabel(self) -> int:
        return self._knn_prediction

    @pyqtProperty(bool, notify=selectedImageChanged)
    def hasKnnPrediction(self) -> bool:
        return self._digits_dataset is not None and self._knn_prediction >= 0

    @pyqtProperty("QVariantList", notify=selectedImageChanged)
    def knnNeighborLabels(self) -> list[int]:
        return list(self._knn_neighbor_labels)

    @pyqtProperty("QVariantList", notify=selectedImageChanged)
    def knnNeighborDistances(self) -> list[float]:
        return list(self._knn_neighbor_distances)

    @pyqtProperty(str, notify=selectedImageChanged)
    def knnPredictionError(self) -> str:
        return self._knn_prediction_error

    @pyqtProperty(str, notify=dimensionalityExperimentChanged)
    def dimensionalityExperimentSummary(self) -> str:
        return self._dimensionality_summary

    @pyqtProperty("QVariantList", notify=dimensionalityExperimentChanged)
    def dimensionalityCharts(self) -> list[dict[str, str]]:
        return self._dimensionality_charts

    @pyqtProperty("QVariantList", notify=dimensionalityExperimentChanged)
    def dimensionalityComparisonRows(self) -> list[dict[str, object]]:
        return self._dimensionality_comparison_rows

    @pyqtProperty("QVariantMap", notify=distanceConcentrationChanged)
    def distanceConcentrationResult(self) -> dict[str, object]:
        return dict(self._distance_concentration_result)

    @pyqtProperty(str, notify=distanceConcentrationChanged)
    def distanceConcentrationChart(self) -> str:
        return self._distance_concentration_chart

    @pyqtProperty(str, notify=datasetChanged)
    def datasetError(self) -> str:
        return self._dataset_error

    @pyqtProperty(int, notify=datasetChanged)
    def datasetSampleCount(self) -> int:
        return len(self._digits_dataset) if self._digits_dataset else 0

    @pyqtProperty(int, notify=datasetChanged)
    def datasetFeatureCount(self) -> int:
        return int(self._digits_dataset.feature_vectors.shape[1]) if self._digits_dataset else 0

    @pyqtProperty(int, notify=datasetChanged)
    def datasetClassCount(self) -> int:
        return len(self._digits_dataset.classes) if self._digits_dataset else 0

    @pyqtProperty(int, notify=datasetChanged)
    def datasetTrainCount(self) -> int:
        return int(self._digits_dataset.train_indices.size) if self._digits_dataset else 0

    @pyqtProperty(int, notify=datasetChanged)
    def datasetTestCount(self) -> int:
        return int(self._digits_dataset.test_indices.size) if self._digits_dataset else 0

    @pyqtProperty("QVariantList", notify=datasetChanged)
    def datasetClasses(self) -> list[int]:
        return list(self._digits_dataset.classes) if self._digits_dataset else []

    @pyqtSlot(str)
    def navigateTo(self, page: str) -> None:
        if page in self._pages and page != self._current_page:
            self._current_page = page
            self.currentPageChanged.emit()

    @pyqtSlot()
    def evaluateKnnClassifier(self) -> None:
        if self._closing or self._digits_dataset is None or self._knn_evaluation_running:
            return
        if self._baseline_task is not None:
            if self._baseline_task.isRunning():
                return
            self._baseline_task.deleteLater()
        self._knn_evaluation_running = True
        self._knn_evaluation_ready = False
        self._knn_evaluation_error = ""
        self.datasetChanged.emit()
        dataset = self._digits_dataset
        self._baseline_task = BackgroundTask(lambda: evaluate_knn_classifier(dataset, k=self._knn_k), self)
        self._baseline_task.succeeded.connect(self._on_baseline_evaluated)
        self._baseline_task.failed.connect(self._on_baseline_failed)
        self._baseline_task.start()

    @pyqtSlot()
    def runDimensionalityExperiments(self) -> None:
        if self._closing or self._experiments_running or (self._experiment_task and self._experiment_task.isRunning()):
            return
        if self._digits_dataset is None:
            self._experiment_requested = True
            self._experiment_error = ""
            self.dimensionalityExperimentChanged.emit()
            self.initializeDataset()
            return
        self._experiments_running = True
        self._experiment_error = ""
        self.dimensionalityExperimentChanged.emit()
        if self._experiment_task is not None:
            self._experiment_task.deleteLater()
        dataset = self._digits_dataset
        self._experiment_task = BackgroundTask(lambda: run_experiment_suite(dataset), self)
        self._experiment_task.succeeded.connect(self._on_experiments_completed)
        self._experiment_task.failed.connect(self._on_experiments_failed)
        self._experiment_task.start()

    @pyqtSlot(object)
    def _on_experiments_completed(self, payload: dict) -> None:
        if self._closing:
            return
        self._dimensionality_results = payload["results"]
        self._dimensionality_summary = self._format_dimensionality_summary(payload["results"])
        self._dimensionality_charts = payload["visualizations"]["charts"]
        self._dimensionality_comparison_rows = payload["visualizations"]["comparison_rows"]
        self._experiments_running = False
        self.dimensionalityExperimentChanged.emit()

    @pyqtSlot(str)
    def _on_experiments_failed(self, error: str) -> None:
        if self._closing:
            return
        self._experiment_error = error
        self._experiments_running = False
        self.dimensionalityExperimentChanged.emit()

    @pyqtSlot(int)
    def analyzeDistanceConcentration(self, test_position: int) -> None:
        if self._closing or self._distance_running or (self._distance_task and self._distance_task.isRunning()):
            return
        if self._digits_dataset is None:
            self._on_distance_failed("The Digits dataset is unavailable.")
            return
        if test_position < 0 or test_position >= len(self._digits_dataset.test_indices):
            self._on_distance_failed("Select a query from the held-out test split.")
            return
        self._distance_running = True
        self.distanceConcentrationChanged.emit()
        if self._distance_task is not None:
            self._distance_task.deleteLater()
        dataset = self._digits_dataset
        self._distance_task = BackgroundTask(lambda: analyze_distance_query(dataset, test_position), self)
        self._distance_task.succeeded.connect(self._on_distance_completed)
        self._distance_task.failed.connect(self._on_distance_failed)
        self._distance_task.start()

    @pyqtSlot(object)
    def _on_distance_completed(self, payload: dict) -> None:
        if self._closing:
            return
        self._distance_concentration_result = payload["result"]
        self._distance_concentration_chart = payload["chart"]
        self._distance_running = False
        self.distanceConcentrationChanged.emit()

    @pyqtSlot(str)
    def _on_distance_failed(self, error: str) -> None:
        if self._closing:
            return
        self._distance_concentration_result = {"error": error}
        self._distance_concentration_chart = ""
        self._distance_running = False
        self.distanceConcentrationChanged.emit()

    @staticmethod
    def _format_dimensionality_summary(results: dict[str, object]) -> str:
        sections: list[str] = []
        synthetic = results.get("synthetic", {})
        if synthetic:
            entries = [
                f"d={size}: mean D^2={stats['mean_squared_distance']:.3f}, var={stats['variance_squared_distance']:.3f}, CV(D^2)={stats['squared_distance_cv']:.3f}"
                for size, stats in sorted(synthetic.items())
            ]
            sections.append("Synthetic validation:\n" + "; ".join(entries))
        irrelevant = results.get("irrelevant_features", {})
        if irrelevant:
            entries = [
                f"{size} features: acc={stats['test_accuracy']:.3f}, mean dist={stats['mean_distance']:.3f}, CV={stats['coefficient_of_variation']:.3f}"
                for size, stats in sorted(irrelevant.items())
            ]
            sections.append("Irrelevant feature augmentation:\n" + "; ".join(entries))
        pca = results.get("standardization_and_pca", {})
        if pca:
            entries = [
                f"{name}: acc={stats['test_accuracy']:.3f}, mean dist={stats['mean_distance']:.3f}, CV={stats['coefficient_of_variation']:.3f}"
                for name, stats in pca.items()
            ]
            sections.append("Preprocessing comparison:\n" + "; ".join(entries))
        return "\n\n".join(sections) if sections else "No dimensionality experiment output available."

    @pyqtSlot(str)
    def setSelectedImage(self, image_url: str) -> None:
        url = QUrl(image_url)
        image_path = url.toLocalFile() if url.isLocalFile() else image_url
        image_path = str(Path(image_path).expanduser().resolve()) if image_path else ""
        self._selected_image_path = image_path
        self._processed_image_url = ""
        self._feature_vector = []
        self._processing_error = ""
        self._preprocessing_summary = ""
        self._original_image_width = 0
        self._original_image_height = 0
        self._knn_prediction = -1
        self._knn_neighbor_labels = []
        self._knn_neighbor_distances = []
        self._knn_neighbors = []
        self._knn_prediction_error = ""
        if image_path:
            try:
                processed = preprocess_image(image_path, normalize_digit=True)
                self._preprocessing_summary = processed.normalization_summary
                self._processed_image_url = self._processed_preview_url(processed)
                self._feature_vector = processed.feature_vector.tolist()
                self._original_image_width = processed.original_width
                self._original_image_height = processed.original_height
                if self._digits_dataset is not None:
                    self._predict_selected_image()
            except (OSError, ValueError, cv2.error) as error:
                self._processing_error = str(error)
        self.selectedImageChanged.emit()

    @staticmethod
    def _processed_preview_url(processed: ProcessedImage) -> str:
        return digit_image_url(processed.processed_image)

    def _predict_selected_image(self) -> None:
        try:
            prediction = predict_knn_for_feature_vector(self._feature_vector, self._digits_dataset, k=self._knn_k)
            self._knn_prediction = int(prediction["predicted_label"])
            self._knn_neighbor_labels = [int(value) for value in prediction["neighbor_labels"]]
            self._knn_neighbor_distances = [float(value) for value in prediction["neighbor_distances"]]
            self._knn_neighbors = [
                {"index": int(index), "label": int(self._digits_dataset.labels[index]),
                 "distance": float(distance), "source": digit_image_url(self._digits_dataset.images[index])}
                for index, distance in zip(prediction["neighbor_dataset_indices"], prediction["neighbor_distances"])
            ]
            self._knn_prediction_error = ""
        except Exception as error:
            self._knn_prediction_error = str(error)

    @pyqtSlot()
    def clearSelectedImage(self) -> None:
        if self._selected_image_path or self._processed_image_url or self._processing_error:
            self._selected_image_path = ""
            self._processed_image_url = ""
            self._feature_vector = []
            self._processing_error = ""
            self._preprocessing_summary = ""
            self._original_image_width = 0
            self._original_image_height = 0
            self._knn_prediction = -1
            self._knn_neighbor_labels = []
            self._knn_neighbor_distances = []
            self._knn_neighbors = []
            self._knn_prediction_error = ""
            self.selectedImageChanged.emit()
