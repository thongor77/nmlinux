"""Global CLI preview bar — pedagogical feature shared across all pages."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QPushButton, QWidget

from nmlinux.core.i18n import tr

_instance: CliBar | None = None


def get_cli_bar() -> CliBar | None:
    return _instance


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
        self.setStyleSheet('background-color: #11111b;')

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 8, 0)
        layout.setSpacing(6)

        mono = QFont('Monospace', 9)

        prompt = QLabel('$')
        prompt.setFont(mono)
        prompt.setStyleSheet('color: #a6e3a1; font-weight: bold; background: transparent;')
        layout.addWidget(prompt)

        self._lbl = QLabel(tr('cli_bar_idle'))
        self._lbl.setFont(mono)
        self._lbl.setStyleSheet('color: #cdd6f4; background: transparent;')
        self._lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self._lbl, 1)

        btn_copy = QPushButton(tr('cli_bar_copy'))
        btn_copy.setFlat(True)
        btn_copy.setFixedHeight(22)
        btn_copy.setStyleSheet(
            'color: #585b70; font-size: 10px; background: transparent;'
            'border: none; padding: 0 4px;'
        )
        btn_copy.clicked.connect(self._copy)
        layout.addWidget(btn_copy)

        lbl_about = QLabel(tr('cli_bar_about'))
        lbl_about.setStyleSheet(
            'color: #313244; font-size: 9px; font-style: italic; background: transparent;'
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
