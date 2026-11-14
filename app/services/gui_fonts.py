"""Register local fallback fonts when Qt's platform font discovery is unavailable."""

import os
from importlib.util import find_spec
from pathlib import Path

from PyQt6.QtGui import QFont, QFontDatabase, QGuiApplication


def configure_fonts(application: QGuiApplication) -> None:
    families = set(QFontDatabase.families())
    if os.name == "nt":
        font_directory = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
        for family, filenames in {
            "Segoe UI": ("segoeui.ttf", "segoeuib.ttf"),
            "Bahnschrift": ("bahnschrift.ttf",),
            "Consolas": ("consola.ttf", "consolab.ttf"),
        }.items():
            if family not in families:
                for filename in filenames:
                    path = font_directory / filename
                    if path.is_file():
                        QFontDatabase.addApplicationFont(str(path))
    if not QFontDatabase.families():
        # Matplotlib is already a project dependency; finding its data does not
        # import pyplot or initialize the charting stack during startup.
        package = find_spec("matplotlib")
        if package and package.origin:
            path = Path(package.origin).parent / "mpl-data/fonts/ttf/DejaVuSans.ttf"
            if path.is_file():
                QFontDatabase.addApplicationFont(str(path))
    families = QFontDatabase.families()
    if families:
        fallback = "Segoe UI" if "Segoe UI" in families else families[0]
        for family in ("Segoe UI", "Bahnschrift", "Consolas"):
            if family not in families:
                QFont.insertSubstitution(family, fallback)
        application.setFont(QFont(fallback, 10))
