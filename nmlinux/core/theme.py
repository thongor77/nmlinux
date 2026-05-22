"""Theme helpers — adapts colours to the current KDE/Qt palette."""
from __future__ import annotations

from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication


def is_dark() -> bool:
    return QApplication.palette().color(QPalette.ColorRole.Window).lightness() < 128


def color_ok() -> str:
    return '#a6e3a1' if is_dark() else '#1a7f37'


def color_err() -> str:
    return '#f38ba8' if is_dark() else '#d1242f'
