from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QVBoxLayout, QWidget,
)

from nmlinux.core.help_content import get_help
from nmlinux.core.i18n import tr


class HelpPage(QWidget):
    """Contextual help panel shown when the user clicks the ? badge."""

    back_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._mono = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header bar ────────────────────────────────────────────────────
        header = QFrame()
        header.setFrameShape(QFrame.Shape.StyledPanel)
        header.setStyleSheet("QFrame { border: none; border-bottom: 1px solid palette(mid); }")
        h_row = QHBoxLayout(header)
        h_row.setContentsMargins(12, 8, 12, 8)

        self._btn_back = QPushButton(tr("help_back"))
        self._btn_back.setFlat(True)
        self._btn_back.setStyleSheet("font-size: 12px; color: palette(link);")
        self._btn_back.clicked.connect(self.back_requested)

        self._title_lbl = QLabel()
        self._title_lbl.setStyleSheet("font-size: 15px; font-weight: bold;")
        self._title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        spacer = QWidget()
        spacer.setFixedWidth(80)

        h_row.addWidget(self._btn_back)
        h_row.addWidget(self._title_lbl, 1)
        h_row.addWidget(spacer)
        root.addWidget(header)

        # ── Scrollable content ─────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(32, 24, 32, 32)
        self._content_layout.setSpacing(0)
        self._content_layout.addStretch(1)

        scroll.setWidget(self._content)
        root.addWidget(scroll, 1)

    def load(self, label: str) -> None:
        """Populate the panel for the given module label."""
        self._btn_back.setText(tr("help_back"))
        self._title_lbl.setText(f"?  {label}")

        # Clear previous content (keep the trailing stretch)
        while self._content_layout.count() > 1:
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        data = get_help(label)

        if not data:
            lbl = QLabel(tr("help_no_content"))
            lbl.setStyleSheet("color: palette(mid); font-size: 13px;")
            lbl.setWordWrap(True)
            self._content_layout.insertWidget(0, lbl)
            return

        idx = 0

        # ── Description ───────────────────────────────────────────────────
        sec_lbl = QLabel(tr("help_about"))
        sec_lbl.setStyleSheet("font-size: 13px; font-weight: bold; margin-bottom: 6px;")
        self._content_layout.insertWidget(idx, sec_lbl); idx += 1

        desc = QLabel(data["desc"])
        desc.setWordWrap(True)
        desc.setStyleSheet("font-size: 13px; margin-bottom: 20px;")
        desc.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._content_layout.insertWidget(idx, desc); idx += 1

        # ── Separator ─────────────────────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        sep.setStyleSheet("margin-bottom: 16px;")
        self._content_layout.insertWidget(idx, sep); idx += 1

        # ── Usage examples ────────────────────────────────────────────────
        if data.get("examples"):
            ex_lbl = QLabel(tr("help_examples"))
            ex_lbl.setStyleSheet("font-size: 13px; font-weight: bold; margin-bottom: 10px;")
            self._content_layout.insertWidget(idx, ex_lbl); idx += 1

            for example in data["examples"]:
                row = QWidget()
                row_layout = QHBoxLayout(row)
                row_layout.setContentsMargins(0, 0, 0, 6)
                row_layout.setSpacing(10)

                bullet = QLabel("•")
                bullet.setFixedWidth(14)
                bullet.setStyleSheet("font-size: 14px; color: palette(link); margin-top: 1px;")
                bullet.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

                text = QLabel(example)
                text.setWordWrap(True)
                text.setStyleSheet("font-size: 13px;")
                text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

                row_layout.addWidget(bullet)
                row_layout.addWidget(text, 1)
                self._content_layout.insertWidget(idx, row); idx += 1

        # ── CLI commands ──────────────────────────────────────────────────
        if data.get("cli"):
            spacer = QWidget(); spacer.setFixedHeight(10)
            self._content_layout.insertWidget(idx, spacer); idx += 1

            cli_lbl = QLabel(tr("help_cli"))
            cli_lbl.setStyleSheet("font-size: 13px; font-weight: bold; margin-bottom: 8px;")
            self._content_layout.insertWidget(idx, cli_lbl); idx += 1

            for cmd in data["cli"]:
                cmd_lbl = QLabel(f"$ {cmd}")
                cmd_lbl.setFont(self._mono)
                cmd_lbl.setStyleSheet(
                    "font-size: 12px; background: palette(base); color: #a6e3a1;"
                    " padding: 5px 10px; border-radius: 4px; margin-bottom: 4px;"
                )
                cmd_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                cmd_lbl.setWordWrap(True)
                self._content_layout.insertWidget(idx, cmd_lbl); idx += 1
