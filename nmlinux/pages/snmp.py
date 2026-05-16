from __future__ import annotations

import subprocess

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
)
from PySide6.QtCore import QThread, Signal

from nmlinux.core.cli_bar import get_cli_bar
from nmlinux.core.i18n import tr


_OID_VALUES = [
    "",
    "1.3.6.1.2.1.1.1.0",
    "1.3.6.1.2.1.1.5.0",
    "1.3.6.1.2.1.1.4.0",
    "1.3.6.1.2.1.1.6.0",
    "1.3.6.1.2.1.1.3.0",
    "1.3.6.1.2.1.2.2",
    "1.3.6.1.2.1.2.1.0",
    "1.3.6.1.2.1.4.21",
    "1.3.6.1.2.1.6.13",
    "1.3.6.1.2.1.7.5",
    "1.3.6.1.2.1",
]

_COL_OID, _COL_TYPE, _COL_VALUE = range(3)


class SnmpWorker(QThread):
    row_ready = Signal(str, str, str)
    finished  = Signal(int)
    error     = Signal(str)

    def __init__(self, host: str, port: str, community: str,
                 version: str, oid: str, mode: str) -> None:
        super().__init__()
        self._host      = host
        self._port      = port
        self._community = community
        self._version   = version
        self._oid       = oid
        self._mode      = mode

    def run(self) -> None:
        cmd_name = 'snmpwalk' if self._mode == 'walk' else 'snmpget'
        cmd = [
            cmd_name,
            '-v', self._version,
            '-c', self._community,
            '-On',
            '-Oe',
        ]
        if self._port and self._port != '161':
            cmd.append(f"{self._host}:{self._port}")
        else:
            cmd.append(self._host)
        cmd.append(self._oid)

        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30,
            )
        except FileNotFoundError:
            self.error.emit(tr("snmp_err_not_found", cmd=cmd_name))
            return
        except subprocess.TimeoutExpired:
            self.error.emit(tr("snmp_err_timeout"))
            return
        except Exception as exc:
            self.error.emit(str(exc))
            return

        if proc.returncode not in (0, 1):
            stderr = proc.stderr.strip()
            self.error.emit(stderr or f"Error {proc.returncode}")
            return

        count = 0
        for line in proc.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            if ' = ' not in line:
                continue
            oid_part, rest = line.split(' = ', 1)
            if ': ' in rest:
                typ, val = rest.split(': ', 1)
            else:
                typ, val = rest, ''
            self.row_ready.emit(oid_part.strip(), typ.strip(), val.strip())
            count += 1

        self.finished.emit(count)


class SnmpPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._worker: SnmpWorker | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel(tr("snmp_title"))
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(8)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)

        grid.addWidget(QLabel(tr("snmp_host_lbl")), 0, 0)
        self._host = QLineEdit()
        self._host.setPlaceholderText("192.168.1.1")
        self._host.textChanged.connect(self._update_cli)
        grid.addWidget(self._host, 0, 1)

        grid.addWidget(QLabel(tr("snmp_port_lbl")), 0, 2)
        self._port = QLineEdit("161")
        self._port.setFixedWidth(70)
        self._port.textChanged.connect(self._update_cli)
        grid.addWidget(self._port, 0, 3)

        grid.addWidget(QLabel(tr("snmp_community_lbl")), 1, 0)
        self._community = QLineEdit("public")
        self._community.textChanged.connect(self._update_cli)
        grid.addWidget(self._community, 1, 1)

        grid.addWidget(QLabel(tr("snmp_version_lbl")), 1, 2)
        self._version = QComboBox()
        self._version.addItems(["2c", "1"])
        self._version.setFixedWidth(70)
        self._version.currentIndexChanged.connect(self._update_cli)
        grid.addWidget(self._version, 1, 3)

        grid.addWidget(QLabel(tr("snmp_oid_lbl")), 2, 0)
        oid_row = QHBoxLayout()
        self._oid_input = QLineEdit()
        self._oid_input.setPlaceholderText("1.3.6.1.2.1.1.1.0")
        self._oid_input.textChanged.connect(self._update_cli)
        self._oid_preset = QComboBox()
        self._oid_preset.addItem(tr("snmp_oid_preset_0"))
        for i in range(1, 12):
            self._oid_preset.addItem(tr(f"snmp_oid_{i}"))
        self._oid_preset.currentIndexChanged.connect(self._on_preset)
        oid_row.addWidget(self._oid_input, 1)
        oid_row.addWidget(self._oid_preset)
        grid.addLayout(oid_row, 2, 1, 1, 3)

        grid.addWidget(QLabel(tr("snmp_mode_lbl")), 3, 0)
        self._mode = QComboBox()
        self._mode.addItems([tr("snmp_mode_walk"), tr("snmp_mode_get")])
        self._mode.currentIndexChanged.connect(self._update_cli)
        grid.addWidget(self._mode, 3, 1)

        layout.addLayout(grid)

        btn_row = QHBoxLayout()
        self._btn = QPushButton(tr("snmp_exec_btn"))
        self._btn.setDefault(True)
        self._btn.clicked.connect(self._execute)
        btn_row.addWidget(self._btn)
        btn_row.addStretch(1)
        self._status = QLabel("")
        btn_row.addWidget(self._status)
        layout.addLayout(btn_row)

        self._table = QTableWidget(0, 3)
        self._table.setHorizontalHeaderLabels(["OID", "Type", tr("snmp_col_value")])
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        hdr = self._table.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(_COL_VALUE, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self._table, 10)
        layout.addStretch(1)

    def _update_cli(self) -> None:
        bar = get_cli_bar()
        if not bar:
            return
        host = self._host.text().strip()
        oid  = self._oid_input.text().strip()
        if not host or not oid:
            bar.set_cmd('')
            return
        mode = 'snmpwalk' if self._mode.currentIndex() == 0 else 'snmpget'
        ver  = self._version.currentText()
        comm = self._community.text().strip() or 'public'
        port = self._port.text().strip()
        target = f'{host}:{port}' if port and port != '161' else host
        bar.set_cmd(f'{mode} -v{ver} -c {comm} {target} {oid}')

    def _on_preset(self, idx: int) -> None:
        if idx > 0:
            self._oid_input.setText(_OID_VALUES[idx])

    def _execute(self) -> None:
        host = self._host.text().strip()
        oid  = self._oid_input.text().strip()
        if not host or not oid or (self._worker and self._worker.isRunning()):
            return

        mode = 'walk' if self._mode.currentIndex() == 0 else 'get'
        self._table.setRowCount(0)
        self._btn.setEnabled(False)
        self._status.setText(tr("snmp_querying"))
        self._status.setStyleSheet("")

        self._worker = SnmpWorker(
            host, self._port.text().strip(),
            self._community.text().strip(),
            self._version.currentText(),
            oid, mode,
        )
        self._worker.row_ready.connect(self._add_row)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _add_row(self, oid: str, typ: str, val: str) -> None:
        r = self._table.rowCount()
        self._table.insertRow(r)
        self._table.setItem(r, _COL_OID,   QTableWidgetItem(oid))
        self._table.setItem(r, _COL_TYPE,  QTableWidgetItem(typ))
        self._table.setItem(r, _COL_VALUE, QTableWidgetItem(val))

    def _on_finished(self, count: int) -> None:
        self._btn.setEnabled(True)
        self._status.setText(
            tr("snmp_results_n", n=count) if count else tr("snmp_no_results")
        )

    def _on_error(self, msg: str) -> None:
        self._btn.setEnabled(True)
        self._status.setText(tr("common_error_prefix", msg=msg))
        self._status.setStyleSheet("color: #f38ba8;")
