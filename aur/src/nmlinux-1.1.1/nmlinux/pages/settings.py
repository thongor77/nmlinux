from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout,
    QLabel, QGroupBox, QRadioButton,
    QButtonGroup, QFrame,
)
from PySide6.QtCore import Signal

from nmlinux.core.settings import _SUPPORTED_LANGUAGES, get as get_settings, save as save_settings
from nmlinux.core.i18n import tr


class SettingsPage(QWidget):
    language_changed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        self._title = QLabel(tr("settings_title"))
        self._title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self._title)

        self._grp_lang = QGroupBox(tr("settings_lang_section"))
        lang_layout = QVBoxLayout(self._grp_lang)
        lang_layout.setSpacing(8)
        lang_layout.setContentsMargins(16, 12, 16, 12)

        self._lang_group = QButtonGroup(self)
        current = get_settings().language

        for code, label in _SUPPORTED_LANGUAGES.items():
            rb = QRadioButton(label)
            rb.setProperty("lang_code", code)
            if code == current:
                rb.setChecked(True)
            self._lang_group.addButton(rb)
            lang_layout.addWidget(rb)

        self._lang_saved = QLabel("")
        self._lang_saved.setStyleSheet("color: #a6e3a1;")
        lang_layout.addSpacing(4)
        lang_layout.addWidget(self._lang_saved)

        layout.addWidget(self._grp_lang)

        # Restart info banner — hidden until language is changed
        self._restart_banner = QFrame()
        self._restart_banner.setFrameShape(QFrame.Shape.StyledPanel)
        self._restart_banner.setStyleSheet(
            "QFrame { background: #1e3a5f; border: 1px solid #4a9eff; border-radius: 6px; padding: 4px; }"
        )
        banner_layout = QVBoxLayout(self._restart_banner)
        banner_layout.setContentsMargins(12, 8, 12, 8)
        self._restart_label = QLabel(tr("settings_lang_note"))
        self._restart_label.setWordWrap(True)
        self._restart_label.setStyleSheet("color: #a8d4ff; font-size: 12px; border: none;")
        banner_layout.addWidget(self._restart_label)
        self._restart_banner.setVisible(False)
        layout.addWidget(self._restart_banner)

        self._lang_group.buttonClicked.connect(self._on_lang_changed)

        layout.addStretch(1)

    def _on_lang_changed(self, btn: QRadioButton) -> None:
        code = btn.property("lang_code")
        settings = get_settings()
        settings.language = code
        save_settings()

        self._title.setText(tr("settings_title"))
        self._grp_lang.setTitle(tr("settings_lang_section"))
        self._lang_saved.setText(tr("settings_saved"))
        self._restart_label.setText(tr("settings_lang_note"))
        self._restart_banner.setVisible(True)

        self.language_changed.emit()
