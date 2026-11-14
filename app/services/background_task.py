"""Run backend work without mutating Qt properties from a worker thread."""

from collections.abc import Callable
import logging

from PyQt6.QtCore import QThread, pyqtSignal


class BackgroundTask(QThread):
    succeeded = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, operation: Callable, parent=None):
        super().__init__(parent)
        self._operation = operation

    def run(self) -> None:
        try:
            result = self._operation()
        except InterruptedError:
            return
        except Exception as error:
            logging.getLogger(__name__).exception("Background operation failed")
            self.failed.emit(str(error) or type(error).__name__)
        else:
            self.succeeded.emit(result)
