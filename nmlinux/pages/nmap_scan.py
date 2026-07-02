from __future__ import annotations

import re
import subprocess
import xml.etree.ElementTree as ET

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QFileDialog, QMessageBox,
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor

from nmlinux.core.cli_bar import get_cli_bar
from nmlinux.core.host_actions import HostActionMenu
from nmlinux.core.i18n import tr
from nmlinux.core.theme import color_ok, color_err

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
    action_requested = Signal(str, str, str)

    def __init__(self) -> None:
        super().__init__()
        self._worker: NmapWorker | None = None
        self._last_scan_hosts: list[dict] = []
        self._scan_agg: dict[str, dict] = {}  # host_label -> {ip, hostname, ports}
        self._build_ui()

    @staticmethod
    def _parse_host_label(label: str) -> tuple[str, str]:
        """'hostname (1.2.3.4)' -> (ip, hostname); '1.2.3.4' -> (ip, '')"""
        m = re.match(r'^(.*)\s+\((\d+\.\d+\.\d+\.\d+)\)$', label)
        if m:
            return m.group(2), m.group(1).strip()
        return label, ''

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
        self._btn_csv = QPushButton(tr("common_export_csv"))
        self._btn_csv.setVisible(False)
        self._btn_csv.clicked.connect(self._export_csv)
        self._btn_txt = QPushButton(tr("common_export_txt"))
        self._btn_txt.setVisible(False)
        self._btn_txt.clicked.connect(self._export_txt)
        btn_row.addSpacing(12)
        btn_row.addWidget(self._btn_csv)
        btn_row.addWidget(self._btn_txt)
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
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._on_right_click)
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

        self._scan_agg = {}
        self._last_scan_hosts = []
        self._table.setRowCount(0)
        self._btn_scan.setEnabled(False)
        self._btn_stop.setEnabled(True)
        self._btn_csv.setVisible(False)
        self._btn_txt.setVisible(False)
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
        # Aggregation for _last_scan_hosts
        host_label = data.get('host', '')
        if host_label not in self._scan_agg:
            ip, hostname = self._parse_host_label(host_label)
            self._scan_agg[host_label] = {'ip': ip, 'hostname': hostname, 'ports': []}
        try:
            port_num = int(data.get('port', ''))
            if data.get('state', '') == 'open':
                self._scan_agg[host_label]['ports'].append(port_num)
        except ValueError:
            pass

        r = self._table.rowCount()
        self._table.insertRow(r)
        for col, key in enumerate(['host', 'port', 'proto', 'state', 'service', 'version']):
            item = QTableWidgetItem(data.get(key, '—'))
            if col == _COL_STATE:
                state = data.get('state', '')
                item.setForeground(QColor(color_ok() if state in ('open', 'up') else color_err()))
            self._table.setItem(r, col, item)

    def _on_finished(self, summary: str) -> None:
        self._last_scan_hosts = list(self._scan_agg.values())
        self._scan_agg = {}
        self._btn_scan.setEnabled(True)
        self._btn_stop.setEnabled(False)
        self._status.setText(summary)
        has_rows = self._table.rowCount() > 0
        self._btn_csv.setVisible(has_rows)
        self._btn_txt.setVisible(has_rows)

    def _on_error(self, msg: str) -> None:
        self._btn_scan.setEnabled(True)
        self._btn_stop.setEnabled(False)
        self._status.setText(tr("common_error_prefix", msg=msg))
        self._status.setStyleSheet(f"color: {color_err()};")

    def _on_right_click(self, pos) -> None:
        row = self._table.rowAt(pos.y())
        if row < 0:
            return
        host_item = self._table.item(row, _COL_HOST)
        if not host_item:
            return
        host_label = host_item.text()
        ip, hostname = self._parse_host_label(host_label)
        # Start with the port from the clicked row
        port_item = self._table.item(row, _COL_PORT)
        ports: list[int] = []
        if port_item:
            try:
                ports = [int(port_item.text())]
            except ValueError:
                pass
        # Prefer the full aggregated port list (during scan use _scan_agg, after scan use _last_scan_hosts)
        agg_entry = self._scan_agg.get(host_label)
        if agg_entry and agg_entry['ports']:
            ports = agg_entry['ports']
        else:
            for entry in self._last_scan_hosts:
                if entry['ip'] == ip:
                    if entry['ports']:
                        ports = entry['ports']
                    break
        menu = HostActionMenu(ip or host_label, hostname, ports or None, parent=self)
        menu.action_chosen.connect(self.action_requested)
        menu.exec(self._table.viewport().mapToGlobal(pos))

    def _table_rows(self) -> list[tuple[str, ...]]:
        keys = ['host', 'port', 'proto', 'state', 'service', 'version']
        rows = []
        for r in range(self._table.rowCount()):
            rows.append(tuple(
                (self._table.item(r, c).text() if self._table.item(r, c) else '')
                for c in range(len(keys))
            ))
        return rows

    def _export_csv(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, tr("common_export_csv"), "nmap_result.csv",
            "CSV (*.csv);;All (*)",
        )
        if not path:
            return
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write("Host,Port,Protocol,State,Service,Version\n")
                for row in self._table_rows():
                    safe = [v.replace('"', '""') for v in row]
                    f.write(','.join(f'"{v}"' if ',' in v else v for v in safe) + '\n')
        except OSError as exc:
            QMessageBox.critical(self, "Error", str(exc))

    def _export_txt(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, tr("common_export_txt"), "nmap_result.txt",
            "Text (*.txt);;All (*)",
        )
        if not path:
            return
        try:
            rows = self._table_rows()
            headers = [
                tr("nmap_col_host"), tr("common_port"), tr("common_proto"),
                tr("nmap_col_state"), tr("common_service"), tr("common_version"),
            ]
            widths = [
                max(len(h), max((len(r[i]) for r in rows), default=0))
                for i, h in enumerate(headers)
            ]
            sep  = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
            hrow = "| " + " | ".join(f"{h:<{w}}" for h, w in zip(headers, widths)) + " |"
            target = self._target.text().strip()
            with open(path, 'w', encoding='utf-8') as f:
                if target:
                    f.write(f"Target: {target}\n{self._status.text()}\n\n")
                f.write(sep + "\n" + hrow + "\n" + sep + "\n")
                for row in rows:
                    f.write("| " + " | ".join(f"{v:<{w}}" for v, w in zip(row, widths)) + " |\n")
                f.write(sep + "\n")
        except OSError as exc:
            QMessageBox.critical(self, "Error", str(exc))

    def showEvent(self, event) -> None:  # noqa: N802
        self._update_cli()
        super().showEvent(event)
