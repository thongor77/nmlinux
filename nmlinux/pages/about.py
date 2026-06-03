from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QPushButton,
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices

from nmlinux import __version__
from nmlinux.core.i18n import tr
from nmlinux.core.icons import themed_icon

_ORIGINAL_URL = "https://github.com/BornToBeRoot/NETworkManager"


def _section(title: str, body: str) -> QFrame:
    frame = QFrame()
    frame.setFrameShape(QFrame.Shape.StyledPanel)
    frame.setStyleSheet("QFrame { border-radius: 6px; padding: 2px; }")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(16, 10, 16, 10)
    layout.setSpacing(4)

    lbl_title = QLabel(title)
    lbl_title.setStyleSheet("font-weight: bold; font-size: 12px;")
    layout.addWidget(lbl_title)

    lbl_body = QLabel(body)
    lbl_body.setWordWrap(True)
    lbl_body.setStyleSheet("font-size: 12px;")
    layout.addWidget(lbl_body)

    return frame


class AboutPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addStretch(1)

        center = QVBoxLayout()
        center.setSpacing(16)
        center.setContentsMargins(60, 24, 60, 24)

        # ── Header ────────────────────────────────────────────────────────
        icon_lbl = QLabel()
        icon_lbl.setPixmap(themed_icon("network-wired", "network-server").pixmap(48, 48))
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        center.addWidget(icon_lbl)

        name_lbl = QLabel("NMLinux")
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        name_lbl.setStyleSheet("font-size: 22px; font-weight: bold;")
        center.addWidget(name_lbl)

        self._version_lbl = QLabel(f"Version {__version__}")
        self._version_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self._version_lbl.setStyleSheet("font-size: 12px; color: gray;")
        center.addWidget(self._version_lbl)

        self._desc_lbl = QLabel(tr("about_description"))
        self._desc_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self._desc_lbl.setStyleSheet("font-size: 13px;")
        center.addWidget(self._desc_lbl)

        center.addSpacing(4)

        # ── Inspired by ───────────────────────────────────────────────────
        self._inspired_frame = _section(tr("about_inspired_title"), tr("about_inspired_text"))
        center.addWidget(self._inspired_frame)

        # Original project link
        link_row = QHBoxLayout()
        link_row.setContentsMargins(16, 0, 16, 0)
        self._link_label = QLabel(tr("about_original_label"))
        self._link_label.setStyleSheet("font-size: 11px; color: palette(mid);")
        link_row.addWidget(self._link_label)

        btn_link = QPushButton("BornToBeRoot / NETworkManager")
        btn_link.setFlat(True)
        btn_link.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_link.setStyleSheet("color: palette(link); text-decoration: underline; font-size: 11px;")
        btn_link.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(_ORIGINAL_URL)))
        link_row.addWidget(btn_link)
        link_row.addStretch(1)
        center.addLayout(link_row)

        # ── Credits ───────────────────────────────────────────────────────
        self._credits_frame = _section(tr("about_credits_title"), tr("about_credits_text"))
        center.addWidget(self._credits_frame)

        # ── Tech ──────────────────────────────────────────────────────────
        self._tech_frame = _section(tr("about_tech_title"), tr("about_tech_text"))
        center.addWidget(self._tech_frame)

        # ── Tools & services ──────────────────────────────────────────────
        self._tools_frame = _section(tr("about_tools_title"), tr("about_tools_text"))
        center.addWidget(self._tools_frame)

        outer.addLayout(center)
        outer.addStretch(1)
