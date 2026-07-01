from __future__ import annotations

import subprocess

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView,
)
from PySide6.QtCore import Qt, QThread, Signal

from nmlinux.core.cli_bar import get_cli_bar
from nmlinux.core.i18n import tr
from nmlinux.core.theme import color_err


_RTYPES = ["A", "AAAA", "MX", "TXT", "NS", "CNAME", "PTR", "SOA", "ANY"]

_SERVERS = [
    ("system",                None),
    ("8.8.8.8  — Google",     "8.8.8.8"),
    ("8.8.4.4  — Google",     "8.8.4.4"),
    ("1.1.1.1  — Cloudflare", "1.1.1.1"),
    ("9.9.9.9  — Quad9",      "9.9.9.9"),
]


class DnsWorker(QThread):
    done  = Signal(list)
    error = Signal(str)

    def __init__(self, host: str, rtype: str, nameserver: str | None) -> None:
        super().__init__()
        self._host       = host
        self._rtype      = rtype
        self._nameserver = nameserver

    def run(self) -> None:
        cmd = ['dig', '+noall', '+answer', '+nocmd']
        if self._nameserver:
            cmd += [f'@{self._nameserver}']

        if self._rtype == 'PTR':
            cmd += ['-x', self._host]
        else:
            cmd += [self._host, self._rtype]

        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True, timeout=10,
            )
        except FileNotFoundError:
            self.error.emit(tr("dns_err_no_dig"))
            return
        except subprocess.TimeoutExpired:
            self.error.emit(tr("dns_err_timeout"))
            return
        except Exception as exc:
            self.error.emit(str(exc))
            return

        rows = _parse_dig(proc.stdout)

        if not rows:
            stderr = proc.stderr.strip()
            if 'NXDOMAIN' in (proc.stdout + stderr):
                self.error.emit(tr("dns_err_nxdomain", host=self._host))
            elif 'SERVFAIL' in (proc.stdout + stderr):
                self.error.emit(tr("dns_err_servfail"))
            elif proc.returncode != 0:
                self.error.emit(stderr or tr("dns_err_no_answer"))
            else:
                self.error.emit(tr("dns_err_no_records", type=self._rtype, host=self._host))
            return

        self.done.emit(rows)


def _parse_dig(output: str) -> list[tuple[str, str, str]]:
    rows = []
    for line in output.splitlines():
        line = line.strip()
        if not line or line.startswith(';'):
            continue
        parts = line.split()
        if len(parts) < 5:
            continue
        ttl   = parts[1]
        rtype = parts[3]
        value = ' '.join(parts[4:]).rstrip('.')
        rows.append((rtype, ttl, value))
    return rows


class DnsPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._worker: DnsWorker | None = None
        self._result_rows: list = []
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel(tr("dns_title"))
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        bar = QHBoxLayout()

        self._input = QLineEdit()
        self._input.setPlaceholderText(tr("dns_placeholder"))
        self._input.returnPressed.connect(self._on_query)
        self._input.textChanged.connect(self._update_cli)

        self._rtype_cb = QComboBox()
        self._rtype_cb.addItems(_RTYPES)
        self._rtype_cb.setFixedWidth(72)
        self._rtype_cb.currentIndexChanged.connect(self._update_cli)

        self._server_cb = QComboBox()
        self._server_cb.setEditable(True)
        for key, _ in _SERVERS:
            label = tr("dns_server_system") if key == "system" else key
            self._server_cb.addItem(label)
        self._server_cb.setFixedWidth(210)
        self._server_cb.currentIndexChanged.connect(self._update_cli)

        self._btn = QPushButton(tr("dns_resolve_btn"))
        self._btn.setDefault(True)
        self._btn.clicked.connect(self._on_query)

        self._btn_export = QPushButton("Export")
        self._btn_export.setFixedWidth(80)
        self._btn_export.clicked.connect(self._export)

        bar.addWidget(self._input, 1)
        bar.addWidget(self._rtype_cb)
        bar.addWidget(QLabel(tr("dns_server_lbl")))
        bar.addWidget(self._server_cb)
        bar.addWidget(self._btn)
        bar.addWidget(self._btn_export)
        layout.addLayout(bar)

        self._table = QTableWidget(0, 3)
        self._table.setHorizontalHeaderLabels(["Type", "TTL (s)", tr("dns_col_value")])
        hdr = self._table.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.verticalHeader().setVisible(False)
        self._table.setVisible(False)
        layout.addWidget(self._table, 10)

        self._status = QLabel("")
        self._status.setWordWrap(True)
        layout.addWidget(self._status)
        layout.addStretch(1)

    def set_target(self, host: str) -> None:
        self._input.setText(host)

    def _update_cli(self) -> None:
        bar = get_cli_bar()
        if not bar:
            return
        host = self._input.text().strip()
        rtype = self._rtype_cb.currentText()
        ns = self._nameserver()
        if not host:
            bar.set_cmd('')
            return
        parts = ['dig']
        if ns:
            parts.append(f'@{ns}')
        if rtype == 'PTR':
            parts += ['-x', host]
        else:
            parts += [host, rtype]
        bar.set_cmd(' '.join(parts))

    def _nameserver(self) -> str | None:
        text = self._server_cb.currentText().strip()
        system_label = tr("dns_server_system")
        if text == system_label:
            return None
        for key, ns in _SERVERS:
            label = system_label if key == "system" else key
            if text == label:
                return ns
        return text if text else None

    def _on_query(self) -> None:
        host = self._input.text().strip()
        if not host:
            return

        if self._worker and self._worker.isRunning():
            self._worker.done.disconnect()
            self._worker.error.disconnect()
            self._worker.terminate()

        self._btn.setEnabled(False)
        self._table.setVisible(False)
        self._status.setStyleSheet("color: palette(mid);")
        self._status.setText(tr("dns_resolving"))

        self._worker = DnsWorker(host, self._rtype_cb.currentText(), self._nameserver())
        self._worker.done.connect(self._on_done)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_error(self, msg: str) -> None:
        self._btn.setEnabled(True)
        self._table.setVisible(False)
        self._status.setStyleSheet(f"color: {color_err()};")
        self._status.setText(tr("common_error_prefix", msg=msg))

    def _on_done(self, rows: list) -> None:
        self._btn.setEnabled(True)
        self._result_rows = rows
        self._status.setStyleSheet("color: palette(mid);")
        self._status.setText(tr("dns_records_found", n=len(rows)))

        self._table.setRowCount(0)
        for rtype, ttl, value in rows:
            r = self._table.rowCount()
            self._table.insertRow(r)
            self._table.setItem(r, 0, QTableWidgetItem(rtype))
            ttl_item = QTableWidgetItem(ttl)
            ttl_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(r, 1, ttl_item)
            self._table.setItem(r, 2, QTableWidgetItem(value))

        self._table.setVisible(True)

    def _export(self) -> None:
        from PySide6.QtWidgets import QMessageBox
        from datetime import datetime
        from nmlinux.export_manager import save_export
        from nmlinux.core.export_dialog import open_export_dialog

        filepath, fmt = open_export_dialog(self, "Export DNS Results", "dns-results")
        if not filepath:
            return

        records = [{"type": t, "ttl": ttl, "value": v} for t, ttl, v in self._result_rows]
        data = {
            "timestamp": datetime.now().isoformat(),
            "module": "DNS",
            "query": self._input.text().strip(),
            "record_type": self._rtype_cb.currentText(),
            "server": self._server_cb.currentText(),
            "records": records,
        }
        error = save_export(data, fmt, filepath)
        if error:
            QMessageBox.warning(self, "Export Error", error)
        else:
            QMessageBox.information(self, "Export", f"Saved to:\n{filepath}")

    def showEvent(self, event) -> None:  # noqa: N802
        self._update_cli()
        super().showEvent(event)
