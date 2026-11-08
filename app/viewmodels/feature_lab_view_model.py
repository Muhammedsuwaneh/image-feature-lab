import base64
from pathlib import Path

import cv2
import numpy as np
from PyQt6.QtCore import QObject, QUrl, pyqtProperty, pyqtSignal, pyqtSlot

from app.backend.calculations.distance_metrics import (
	analyze_distance_to_samples,
	coefficient_of_variation,
	relative_distance_contrast,
)
from app.backend.datasets.digits_dataset import DigitsDataset, load_digits_dataset
from app.backend.experiments.dimensionality_experiments import run_all_dimensionality_experiments
from app.backend.experiments.result_visualizations import (
	build_result_visualizations,
	render_distance_distribution_chart,
)
from app.backend.image_processing.image_preprocessor import ProcessedImage, preprocess_image
from app.backend.machine_learning.knn_classifier import (
    evaluate_knn_classifier,
    predict_image_with_knn,
)


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
		self._original_image_width = 0
		self._original_image_height = 0
		self._knn_k = 5
		self._knn_test_accuracy = 0.0
		self._knn_prediction = -1
		self._knn_neighbor_labels: list[int] = []
		self._knn_neighbor_distances: list[float] = []
		self._knn_prediction_error = ""
		self._dimensionality_summary = "No dimensionality experiment has been run yet."
		self._dimensionality_results: dict[str, object] = {}
		self._dimensionality_charts: list[dict[str, str]] = []
		self._dimensionality_comparison_rows: list[dict[str, object]] = []
		self._distance_concentration_result: dict[str, object] = {}
		self._distance_concentration_chart = ""
		try:
			self._digits_dataset: DigitsDataset | None = load_digits_dataset()
			self._dataset_error = ""
			self.evaluateKnnClassifier()
		except Exception as error:
			self._digits_dataset = None
			self._dataset_error = str(error)

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
		if self._digits_dataset is None:
			self._knn_test_accuracy = 0.0
			self.datasetChanged.emit()
			return
		result = evaluate_knn_classifier(self._digits_dataset, k=self._knn_k)
		self._knn_test_accuracy = float(result["test_accuracy"])
		self.datasetChanged.emit()

	@pyqtSlot()
	def runDimensionalityExperiments(self) -> None:
		if self._digits_dataset is None:
			self._dimensionality_summary = "The Digits dataset is unavailable, so no experiments can run."
			self.dimensionalityExperimentChanged.emit()
			return
		results = run_all_dimensionality_experiments()
		self._dimensionality_results = results
		self._dimensionality_summary = self._format_dimensionality_summary(results)
		visualizations = build_result_visualizations(results)
		self._dimensionality_charts = visualizations["charts"]
		self._dimensionality_comparison_rows = visualizations["comparison_rows"]
		self.dimensionalityExperimentChanged.emit()

	@pyqtSlot(int)
	def analyzeDistanceConcentration(self, test_position: int) -> None:
		if self._digits_dataset is None:
			self._distance_concentration_result = {"error": "The Digits dataset is unavailable."}
			self._distance_concentration_chart = ""
			self.distanceConcentrationChanged.emit()
			return

		if test_position < 0 or test_position >= self._digits_dataset.test_indices.size:
			self._distance_concentration_result = {"error": "Select a query from the held-out test split."}
			self._distance_concentration_chart = ""
			self.distanceConcentrationChanged.emit()
			return

		try:
			dataset = self._digits_dataset
			query_index = int(dataset.test_indices[test_position])
			training_indices = dataset.train_indices
			analysis = analyze_distance_to_samples(
				dataset.feature_vectors[query_index],
				dataset.feature_vectors[training_indices],
			)
			distances = np.asarray(analysis["distance_distribution"], dtype=np.float64)
			nearest_dataset_index = int(training_indices[int(analysis["nearest_sample_index"])])
			farthest_dataset_index = int(training_indices[int(analysis["farthest_sample_index"])])
			self._distance_concentration_result = {
				"query_position": int(test_position + 1),
				"query_index": query_index,
				"query_label": int(dataset.labels[query_index]),
				"reference_count": int(training_indices.size),
				"minimum_distance": float(analysis["minimum_distance"]),
				"maximum_distance": float(analysis["maximum_distance"]),
				"mean_distance": float(analysis["mean_distance"]),
				"standard_deviation": float(analysis["std_distance"]),
				"variance": float(np.var(distances, ddof=0)),
				"coefficient_of_variation": float(coefficient_of_variation(distances)),
				"relative_distance_contrast": float(relative_distance_contrast(distances)),
				"nearest_sample_index": nearest_dataset_index,
				"nearest_sample_label": int(dataset.labels[nearest_dataset_index]),
				"nearest_distance": float(analysis["nearest_distance"]),
				"farthest_sample_index": farthest_dataset_index,
				"farthest_sample_label": int(dataset.labels[farthest_dataset_index]),
				"farthest_distance": float(analysis["farthest_distance"]),
			}
			self._distance_concentration_chart = render_distance_distribution_chart(distances)
		except Exception as error:
			self._distance_concentration_result = {"error": str(error)}
			self._distance_concentration_chart = ""
		self.distanceConcentrationChanged.emit()

	@staticmethod
	def _format_dimensionality_summary(results: dict[str, object]) -> str:
		sections: list[str] = []
		synthetic = results.get("synthetic", {})
		if synthetic:
			entries = [
				f"d={size}: mean D²={stats['mean_squared_distance']:.3f}, var={stats['variance_squared_distance']:.3f}, CV={stats['coefficient_of_variation']:.3f}"
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
		self._original_image_width = 0
		self._original_image_height = 0
		self._knn_prediction = -1
		self._knn_neighbor_labels = []
		self._knn_neighbor_distances = []
		self._knn_prediction_error = ""
		if image_path:
			try:
				processed = preprocess_image(image_path)
				self._processed_image_url = self._processed_preview_url(processed)
				self._feature_vector = processed.feature_vector.tolist()
				self._original_image_width = processed.original_width
				self._original_image_height = processed.original_height
				if self._digits_dataset is not None:
					try:
						prediction = predict_image_with_knn(image_path, self._digits_dataset, k=self._knn_k)
						self._knn_prediction = int(prediction["predicted_label"])
						self._knn_neighbor_labels = [int(value) for value in prediction["neighbor_labels"]]
						self._knn_neighbor_distances = [float(value) for value in prediction["neighbor_distances"]]
					except Exception as error:
						self._knn_prediction_error = str(error)
			except (OSError, ValueError, cv2.error) as error:
				self._processing_error = str(error)
		self.selectedImageChanged.emit()

	@staticmethod
	def _processed_preview_url(processed: ProcessedImage) -> str:
		visible_pixels = np.rint(
			processed.processed_image.astype(np.float32) * (255.0 / 16.0)
		).astype(np.uint8)
		preview = cv2.resize(visible_pixels, (256, 256), interpolation=cv2.INTER_NEAREST)
		encoded, png_data = cv2.imencode(".png", preview)
		if not encoded:
			raise ValueError("Could not encode the processed image preview.")
		payload = base64.b64encode(png_data).decode("ascii")
		return f"data:image/png;base64,{payload}"

	@pyqtSlot()
	def clearSelectedImage(self) -> None:
		if self._selected_image_path or self._processed_image_url or self._processing_error:
			self._selected_image_path = ""
			self._processed_image_url = ""
			self._feature_vector = []
			self._processing_error = ""
			self._original_image_width = 0
			self._original_image_height = 0
			self._knn_prediction = -1
			self._knn_neighbor_labels = []
			self._knn_neighbor_distances = []
			self._knn_prediction_error = ""
			self.selectedImageChanged.emit()