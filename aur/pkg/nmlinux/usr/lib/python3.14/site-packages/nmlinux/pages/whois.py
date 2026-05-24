from __future__ import annotations

import subprocess

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QPlainTextEdit,
)
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QFont

from nmlinux.core.i18n import tr


class WhoisWorker(QThread):
    result = Signal(str)
    error  = Signal(str)

    def __init__(self, target: str) -> None:
        super().__init__()
        self._target = target

    def run(self) -> None:
        try:
            proc = subprocess.run(
                ['whois', self._target],
                capture_output=True, text=True, timeout=15,
            )
            output = proc.stdout.strip()
            if not output:
                output = proc.stderr.strip() or tr("whois_no_response")
            self.result.emit(output)
        except FileNotFoundError:
            self.error.emit(tr("whois_err_not_found"))
        except subprocess.TimeoutExpired:
            self.error.emit(tr("whois_err_timeout"))
        except Exception as exc:
            self.error.emit(str(exc))


class WhoisPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._worker: WhoisWorker | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel(tr("whois_title"))
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        row = QHBoxLayout()
        self._input = QLineEdit()
        self._input.setPlaceholderText(tr("whois_placeholder"))
        self._input.returnPressed.connect(self._lookup)
        self._btn = QPushButton(tr("whois_search_btn"))
        self._btn.setDefault(True)
        self._btn.clicked.connect(self._lookup)
        row.addWidget(self._input, 1)
        row.addWidget(self._btn)
        layout.addLayout(row)

        self._status = QLabel("")
        layout.addWidget(self._status)

        self._output = QPlainTextEdit()
        self._output.setReadOnly(True)
        mono = QFont("Monospace")
        mono.setStyleHint(QFont.StyleHint.Monospace)
        self._output.setFont(mono)
        layout.addWidget(self._output, 10)

    def _lookup(self) -> None:
        target = self._input.text().strip()
        if not target or (self._worker and self._worker.isRunning()):
            return
        self._btn.setEnabled(False)
        self._status.setText(tr("whois_querying"))
        self._status.setStyleSheet("")
        self._output.clear()
        self._worker = WhoisWorker(target)
        self._worker.result.connect(self._on_result)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_result(self, text: str) -> None:
        self._btn.setEnabled(True)
        self._status.setText("")
        self._output.setPlainText(text)

    def _on_error(self, msg: str) -> None:
        self._btn.setEnabled(True)
        self._status.setText(tr("common_error_prefix", msg=msg))
        self._status.setStyleSheet("color: #f38ba8;")
