from pathlib import Path
from PyQt6.QtCore import QObject, QUrl, pyqtProperty, pyqtSignal, pyqtSlot


class FeatureLabViewModel(QObject):
	currentPageChanged = pyqtSignal()
	selectedImageChanged = pyqtSignal()

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

	@pyqtSlot(str)
	def navigateTo(self, page: str) -> None:
		if page in self._pages and page != self._current_page:
			self._current_page = page
			self.currentPageChanged.emit()

	@pyqtSlot(str)
	def setSelectedImage(self, image_url: str) -> None:
		url = QUrl(image_url)
		image_path = url.toLocalFile() if url.isLocalFile() else image_url
		image_path = str(Path(image_path).resolve()) if image_path else ""
		if image_path != self._selected_image_path:
			self._selected_image_path = image_path
			self.selectedImageChanged.emit()

	@pyqtSlot()
	def clearSelectedImage(self) -> None:
		if self._selected_image_path:
			self._selected_image_path = ""
			self.selectedImageChanged.emit()