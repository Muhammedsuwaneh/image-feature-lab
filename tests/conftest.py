import os
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")

import pytest
from PyQt6.QtGui import QGuiApplication
from app.services.gui_fonts import configure_fonts


@pytest.fixture(scope="session")
def qt_app():
    application = QGuiApplication.instance() or QGuiApplication([])
    configure_fonts(application)
    return application


@pytest.fixture
def wait_until(qt_app):
    def wait(predicate, timeout=30):
        deadline = time.monotonic() + timeout
        while not predicate() and time.monotonic() < deadline:
            qt_app.processEvents()
            time.sleep(0.005)
        qt_app.processEvents()
        assert predicate(), "Timed out waiting for Qt operation"
    return wait
