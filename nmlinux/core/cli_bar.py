"""Global CLI preview bar — pedagogical feature shared across all pages."""
from __future__ import annotations

from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QPushButton, QWidget

from nmlinux.core.i18n import tr

_instance: CliBar | None = None


def get_cli_bar() -> CliBar | None:
    return _instance


def _dark_mode() -> bool:
    return QApplication.palette().color(QPalette.ColorRole.Window).lightness() < 128


def _cli_colors(dark: bool) -> tuple[str, str, str, str, str]:
    """Return (bg, prompt, text, muted, subtle) for current mode."""
    if dark:
        return '#11111b', '#a6e3a1', '#cdd6f4', '#7f849c', '#585b70'
    return '#dce0e8', '#40a02b', '#4c4f69', '#7c7f93', '#9ca0b0'


class CliBar(QWidget):
    """Terminal-style bar at the bottom of MainWindow.

    Pages call ``get_cli_bar().set_cmd(cmd)`` whenever their parameters change
    so the user always sees the equivalent shell command.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        global _instance
        _instance = self

        self.setFixedHeight(34)
        self.setAutoFillBackground(True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 8, 0)
        layout.setSpacing(6)

        mono = QFont('Monospace', 9)

        self._prompt_lbl = QLabel('$')
        self._prompt_lbl.setFont(mono)
        layout.addWidget(self._prompt_lbl)

        self._lbl = QLabel(tr('cli_bar_idle'))
        self._lbl.setFont(mono)
        self._lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self._lbl, 1)

        self._btn_copy = QPushButton(tr('cli_bar_copy'))
        self._btn_copy.setFlat(True)
        self._btn_copy.setFixedHeight(22)
        self._btn_copy.clicked.connect(self._copy)
        layout.addWidget(self._btn_copy)

        self._lbl_about = QLabel(tr('cli_bar_about'))
        layout.addWidget(self._lbl_about)

        self._apply_colors()

    # ── Public API ────────────────────────────────────────────────────────────

    def set_cmd(self, cmd: str) -> None:
        self._lbl.setText(cmd or tr('cli_bar_idle'))

    def get_cmd(self) -> str:
        return self._lbl.text()

    # ── Theme ─────────────────────────────────────────────────────────────────

    def _apply_colors(self) -> None:
        dark = _dark_mode()
        bg, prompt, text, muted, subtle = _cli_colors(dark)

        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, QColor(bg))
        self.setPalette(pal)

        self._prompt_lbl.setStyleSheet(f'color: {prompt}; font-weight: bold; background: transparent;')
        self._lbl.setStyleSheet(f'color: {text}; background: transparent;')
        self._btn_copy.setStyleSheet(
            f'color: {muted}; font-size: 10px; background: transparent;'
            'border: none; padding: 0 4px;'
        )
        self._lbl_about.setStyleSheet(
            f'color: {subtle}; font-size: 9px; font-style: italic; background: transparent;'
        )

    def changeEvent(self, event: QEvent) -> None:  # noqa: N802
        if event.type() == QEvent.Type.ApplicationPaletteChange:
            self._apply_colors()
        super().changeEvent(event)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _copy(self) -> None:
        text = self._lbl.text()
        if text != tr('cli_bar_idle'):
            QApplication.clipboard().setText(text)
