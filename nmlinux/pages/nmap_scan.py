from __future__ import annotations

import subprocess
import xml.etree.ElementTree as ET

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor

from nmlinux.core.cli_bar import get_cli_bar
from nmlinux.core.i18n import tr


_GREEN = '#a6e3a1'
_RED   = '#f38ba8'

_SCAN_FLAGS = [
    ['-sn'],
    ['-F', '-sT'],
    ['-sT'],
    ['-F', '-sS'],
    ['-sV'],
    ['-O'],
    ['-A'],
]

_COL_HOST, _COL_PORT, _COL_PROTO, _COL_STATE, _COL_SERVICE, _COL_VERSION = range(6)


class NmapWorker(QThread):
    row_ready = Signal(dict)
    finished  = Signal(str)
    error     = Signal(str)

    def __init__(self, target: str, flags: list[str], ports: str) -> None:
        super().__init__()
        self._target = target
        self._flags  = flags
        self._ports  = ports

    def run(self) -> None:
        cmd = ['nmap', '-oX', '-'] + self._flags
        if self._ports:
            cmd += ['-p', self._ports]
        cmd.append(self._target)

        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True, timeout=300,
            )
        except FileNotFoundError:
            self.error.emit(tr("nmap_err_not_found"))
            return
        except subprocess.TimeoutExpired:
            self.error.emit(tr("nmap_err_timeout"))
            return
        except Exception as exc:
            self.error.emit(str(exc))
            return

        if proc.returncode not in (0, 1):
            self.error.emit(proc.stderr.strip() or f"nmap exit {proc.returncode}")
            return

        try:
            root = ET.fromstring(proc.stdout)
        except ET.ParseError as exc:
            self.error.emit(tr("nmap_err_xml", exc=exc))
            return

        hosts_up = 0
        for host in root.findall('host'):
            status = host.find('status')
            if status is None or status.get('state') != 'up':
                continue
            hosts_up += 1

            addr_el = host.find("address[@addrtype='ipv4']") or \
                      host.find("address[@addrtype='ipv6']") or \
                      host.find('address')
            ip = addr_el.get('addr', '—') if addr_el is not None else '—'

            hostname_el = host.find('.//hostname')
            hostname = hostname_el.get('name', '') if hostname_el is not None else ''
            host_label = f"{hostname} ({ip})" if hostname else ip

            ports_el = host.find('ports')
            if ports_el is None:
                self.row_ready.emit({
                    'host': host_label, 'port': '—', 'proto': '—',
                    'state': 'up', 'service': '—', 'version': '—',
                })
                continue

            for port_el in ports_el.findall('port'):
                portid   = port_el.get('portid', '—')
                protocol = port_el.get('protocol', '—')
                state_el = port_el.find('state')
                state    = state_el.get('state', '—') if state_el is not None else '—'
                svc_el   = port_el.find('service')
                service  = svc_el.get('name', '—') if svc_el is not None else '—'
                version  = ''
                if svc_el is not None:
                    parts = [svc_el.get('product', ''), svc_el.get('version', ''),
                             svc_el.get('extrainfo', '')]
                    version = ' '.join(p for p in parts if p)
                self.row_ready.emit({
                    'host': host_label, 'port': portid, 'proto': protocol,
                    'state': state, 'service': service, 'version': version,
                })

        total_el = root.find('runstats/hosts')
        total = int(total_el.get('total', 0)) if total_el is not None else '?'
        self.finished.emit(tr("nmap_done", n=hosts_up, total=total))


class NmapPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._worker: NmapWorker | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel(tr("nmap_title"))
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(8)

        grid.addWidget(QLabel(tr("nmap_target_lbl")), 0, 0)
        self._target = QLineEdit()
        self._target.setPlaceholderText("192.168.1.0/24  |  hostname  |  10.0.0.1-50")
        self._target.returnPressed.connect(self._scan)
        self._target.textChanged.connect(self._update_cli)
        grid.addWidget(self._target, 0, 1)

        grid.addWidget(QLabel(tr("nmap_mode_lbl")), 1, 0)
        self._mode = QComboBox()
        for i in range(7):
            self._mode.addItem(tr(f"nmap_mode_{i}"))
        self._mode.currentIndexChanged.connect(self._update_cli)
        grid.addWidget(self._mode, 1, 1)

        grid.addWidget(QLabel(tr("nmap_ports_lbl")), 2, 0)
        self._ports = QLineEdit()
        self._ports.setPlaceholderText(tr("nmap_ports_ph"))
        self._ports.textChanged.connect(self._update_cli)
        grid.addWidget(self._ports, 2, 1)

        grid.setColumnStretch(1, 1)
        layout.addLayout(grid)

        btn_row = QHBoxLayout()
        self._btn_scan = QPushButton(tr("nmap_scan_btn"))
        self._btn_scan.setDefault(True)
        self._btn_scan.clicked.connect(self._scan)
        self._btn_stop = QPushButton(tr("nmap_stop_btn"))
        self._btn_stop.setEnabled(False)
        self._btn_stop.clicked.connect(self._stop)
        btn_row.addWidget(self._btn_scan)
        btn_row.addWidget(self._btn_stop)
        btn_row.addStretch(1)
        self._status = QLabel("")
        btn_row.addWidget(self._status)
        layout.addLayout(btn_row)

        headers = [
            tr("nmap_col_host"), tr("common_port"), tr("common_proto"),
            tr("nmap_col_state"), tr("common_service"), tr("common_version"),
        ]
        self._table = QTableWidget(0, len(headers))
        self._table.setHorizontalHeaderLabels(headers)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        hdr = self._table.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(_COL_HOST,    QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(_COL_VERSION, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self._table, 10)
        layout.addStretch(1)

    def _update_cli(self) -> None:
        bar = get_cli_bar()
        if not bar:
            return
        target = self._target.text().strip()
        if not target:
            bar.set_cmd('')
            return
        flags = _SCAN_FLAGS[self._mode.currentIndex()]
        ports = self._ports.text().strip()
        cmd = ['nmap'] + flags
        if ports:
            cmd += ['-p', ports]
        cmd.append(target)
        bar.set_cmd(' '.join(cmd))

    def _scan(self) -> None:
        target = self._target.text().strip()
        if not target or (self._worker and self._worker.isRunning()):
            return
        mode_idx = self._mode.currentIndex()
        flags = _SCAN_FLAGS[mode_idx]
        ports = self._ports.text().strip()

        self._table.setRowCount(0)
        self._btn_scan.setEnabled(False)
        self._btn_stop.setEnabled(True)
        self._status.setText(tr("nmap_scanning"))
        self._status.setStyleSheet("")

        self._worker = NmapWorker(target, flags, ports)
        self._worker.row_ready.connect(self._add_row)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _stop(self) -> None:
        if self._worker and self._worker.isRunning():
            self._worker.terminate()
            self._status.setText(tr("nmap_interrupted"))

    def _add_row(self, data: dict) -> None:
        r = self._table.rowCount()
        self._table.insertRow(r)
        for col, key in enumerate(['host', 'port', 'proto', 'state', 'service', 'version']):
            item = QTableWidgetItem(data.get(key, '—'))
            if col == _COL_STATE:
                state = data.get('state', '')
                item.setForeground(QColor(_GREEN if state in ('open', 'up') else _RED))
            self._table.setItem(r, col, item)

    def _on_finished(self, summary: str) -> None:
        self._btn_scan.setEnabled(True)
        self._btn_stop.setEnabled(False)
        self._status.setText(summary)

    def _on_error(self, msg: str) -> None:
        self._btn_scan.setEnabled(True)
        self._btn_stop.setEnabled(False)
        self._status.setText(tr("common_error_prefix", msg=msg))
        self._status.setStyleSheet("color: #f38ba8;")

    def showEvent(self, event) -> None:  # noqa: N802
        self._update_cli()
        super().showEvent(event)
