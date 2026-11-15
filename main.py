import os
import sys
from pathlib import Path

from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtQml import QQmlApplicationEngine

from app.viewmodels.feature_lab_view_model import FeatureLabViewModel
from app.services.gui_fonts import configure_fonts


def main() -> int:
    os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")
    app = QGuiApplication(sys.argv)
    configure_fonts(app)
    app.setApplicationName("FeatureLab")
    view_model = FeatureLabViewModel(app)
    app.aboutToQuit.connect(view_model.shutdown)
    # Load TensorFlow MNIST before constructing QML. The first run downloads
    # the official archive; subsequent starts reuse the verified Keras cache.
    view_model.initializeDataset()
    engine = QQmlApplicationEngine()
    engine.setInitialProperties({"viewModel": view_model})
    qml_file = Path(__file__).resolve().parent / "ui" / "Main.qml"

    engine.load(QUrl.fromLocalFile(str(qml_file)))

    if not engine.rootObjects():
        view_model.shutdown()
        return 1

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
