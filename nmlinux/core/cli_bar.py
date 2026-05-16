"""Global CLI preview bar — pedagogical feature shared across all pages."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QPushButton, QWidget

from nmlinux.core.i18n import tr

_instance: CliBar | None = None


def get_cli_bar() -> CliBar | None:
    return _instance


def _dark_mode() -> bool:
    return QApplication.palette().color(QPalette.ColorRole.Window).lightness() < 128


class CliBar(QWidget):
    """Terminal-style bar at the bottom of MainWindow.

    Pages call ``get_cli_bar().set_cmd(cmd)`` whenever their parameters change
    so the user always sees the equivalent shell command.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        global _instance
        _instance = self

        dark = _dark_mode()

        # colours — Catppuccin Mocha (dark) / Latte (light)
        bg     = '#11111b' if dark else '#dce0e8'   # crust
        prompt = '#a6e3a1' if dark else '#40a02b'   # green
        text   = '#cdd6f4' if dark else '#4c4f69'   # text
        muted  = '#7f849c' if dark else '#7c7f93'   # overlay1
        subtle = '#585b70' if dark else '#9ca0b0'   # surface2 / overlay0

        self.setFixedHeight(34)
        # Use QPalette for background — always respected unlike stylesheet background-color on QWidget
        self.setAutoFillBackground(True)
        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, QColor(bg))
        self.setPalette(pal)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 8, 0)
        layout.setSpacing(6)

        mono = QFont('Monospace', 9)

        prompt_lbl = QLabel('$')
        prompt_lbl.setFont(mono)
        prompt_lbl.setStyleSheet(f'color: {prompt}; font-weight: bold; background: transparent;')
        layout.addWidget(prompt_lbl)

        self._lbl = QLabel(tr('cli_bar_idle'))
        self._lbl.setFont(mono)
        self._lbl.setStyleSheet(f'color: {text}; background: transparent;')
        self._lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self._lbl, 1)

        btn_copy = QPushButton(tr('cli_bar_copy'))
        btn_copy.setFlat(True)
        btn_copy.setFixedHeight(22)
        btn_copy.setStyleSheet(
            f'color: {muted}; font-size: 10px; background: transparent;'
            'border: none; padding: 0 4px;'
        )
        btn_copy.clicked.connect(self._copy)
        layout.addWidget(btn_copy)

        lbl_about = QLabel(tr('cli_bar_about'))
        lbl_about.setStyleSheet(
            f'color: {subtle}; font-size: 9px; font-style: italic; background: transparent;'
        )
        layout.addWidget(lbl_about)

    # ── Public API ────────────────────────────────────────────────────────────

    def set_cmd(self, cmd: str) -> None:
        self._lbl.setText(cmd or tr('cli_bar_idle'))

    def get_cmd(self) -> str:
        return self._lbl.text()

    # ── Internal ──────────────────────────────────────────────────────────────

    def _copy(self) -> None:
        text = self._lbl.text()
        if text != tr('cli_bar_idle'):
            QApplication.clipboard().setText(text)
