import os
import sys
from pathlib import Path

from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtQml import QQmlApplicationEngine

from app.viewmodels.feature_lab_view_model import FeatureLabViewModel


def main() -> int:
	os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")
	app = QGuiApplication(sys.argv)
	app.setApplicationName("FeatureLab")
	engine = QQmlApplicationEngine()
	view_model = FeatureLabViewModel(app)
	engine.setInitialProperties({"viewModel": view_model})
	qml_file = Path(__file__).resolve().parent / "ui" / "Main.qml"

	engine.load(QUrl.fromLocalFile(str(qml_file)))
	if not engine.rootObjects():
		return 1

	return app.exec()


if __name__ == "__main__":
	sys.exit(main())
