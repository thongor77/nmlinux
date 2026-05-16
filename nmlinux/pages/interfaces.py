from __future__ import annotations

import json
import subprocess

from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QGroupBox, QFormLayout,
    QTableWidget, QTableWidgetItem, QHeaderView,
)
from PySide6.QtCore import Qt, QThread, Signal

from nmlinux.core.cli_bar import get_cli_bar
from nmlinux.core.i18n import tr


_GREEN = '#a6e3a1'
_RED   = '#f38ba8'
_GREY  = 'palette(mid)'


def _parse_terse(line: str) -> list[str]:
    parts: list[str] = []
    current = ''
    it = iter(line)
    for ch in it:
        if ch == '\\':
            nxt = next(it, '')
            current += nxt
        elif ch == ':':
            parts.append(current)
            current = ''
        else:
            current += ch
    parts.append(current)
    return parts


class InterfacesWorker(QThread):
    ready = Signal(list)

    def run(self) -> None:
        self.ready.emit(_collect_interfaces())


def _collect_interfaces() -> list[dict]:
    ifaces: list[dict] = []

    type_map: dict[str, str] = {}
    try:
        raw = subprocess.run(
            ['nmcli', '-t', '-f', 'DEVICE,TYPE', 'dev'],
            capture_output=True, text=True, timeout=4,
        ).stdout
        for line in raw.splitlines():
            parts = _parse_terse(line)
            if len(parts) >= 2:
                type_map[parts[0]] = parts[1]
    except Exception:
        pass

    try:
        raw = subprocess.run(
            ['ip', '-j', 'addr', 'show'],
            capture_output=True, text=True, timeout=4,
        ).stdout
        data = json.loads(raw)
    except Exception:
        return ifaces

    for entry in data:
        name = entry.get('ifname', '')
        if name == 'lo':
            continue

        operstate = entry.get('operstate', '').lower()
        # Store raw state key for color logic; translated in UI
        if operstate == 'up':
            state_key = 'up'
        elif operstate == 'down':
            state_key = 'down'
        else:
            state_key = operstate or 'unknown'

        mac = entry.get('address', '—') or '—'

        ipv4_list: list[str] = []
        ipv6_list: list[str] = []
        for addr in entry.get('addr_info', []):
            local  = addr.get('local', '')
            prefix = addr.get('prefixlen', '')
            if addr.get('family') == 'inet':
                ipv4_list.append(f"{local}/{prefix}")
            elif addr.get('family') == 'inet6' and addr.get('scope') == 'global':
                ipv6_list.append(f"{local}/{prefix}")

        ifaces.append({
            'name':      name,
            'type':      type_map.get(name, '—'),
            'state_key': state_key,
            'mac':       mac,
            'ipv4':      '\n'.join(ipv4_list) if ipv4_list else '—',
            'ipv6':      '\n'.join(ipv6_list) if ipv6_list else '—',
        })

    return ifaces


class _DetailPanel(QGroupBox):
    def __init__(self) -> None:
        super().__init__(tr("iface_detail_title"))
        self._form = QFormLayout(self)
        self._form.setHorizontalSpacing(16)
        self._form.setVerticalSpacing(6)
        self._form.setContentsMargins(12, 12, 12, 12)
        self.setVisible(False)

    def show_iface(self, iface: dict) -> None:
        while self._form.rowCount():
            self._form.removeRow(0)

        connected = iface['state_key'] == 'up'
        state_display = tr("iface_state_up") if connected else \
                        (tr("iface_state_down") if iface['state_key'] == 'down' else iface['state_key'])

        def row(label_key: str, value: str, ok: bool | None = None) -> None:
            if ok is None:
                lbl = QLabel(value)
            else:
                color  = _GREEN if ok else _RED
                symbol = '✓' if ok else '✗'
                lbl = QLabel(f'<span style="color:{color}">{symbol}</span>  {value}')
                lbl.setTextFormat(Qt.TextFormat.RichText)
            lbl.setWordWrap(True)
            lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self._form.addRow(tr(label_key) + " :", lbl)

        row("iface_lbl_iface", iface['name'])
        row("iface_lbl_type",  iface['type'])
        row("iface_lbl_state", state_display, ok=connected)
        row("iface_lbl_mac",   iface['mac'])
        row("iface_lbl_ipv4",  iface['ipv4'], ok=iface['ipv4'] != '—')
        row("iface_lbl_ipv6",  iface['ipv6'], ok=iface['ipv6'] != '—')
        self.setVisible(True)


_COL_NAME, _COL_TYPE, _COL_STATE, _COL_MAC, _COL_IPV4, _COL_IPV6 = range(6)


class InterfacesPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._worker: InterfacesWorker | None = None
        self._build_ui()
        self._refresh()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        title  = QLabel(tr("iface_title"))
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        self._btn_refresh = QPushButton(tr("common_refresh"))
        self._btn_refresh.setFixedWidth(100)
        self._btn_refresh.clicked.connect(self._refresh)
        bar = get_cli_bar()
        if bar:
            bar.set_cmd('ip -j addr show  |  nmcli device show')
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(self._btn_refresh)
        layout.addLayout(header)

        headers = [
            tr("iface_col_iface"), tr("iface_col_type"), tr("iface_col_state"),
            tr("iface_col_mac"),   tr("iface_col_ipv4"), tr("iface_col_ipv6"),
        ]
        self._table = QTableWidget(0, len(headers))
        self._table.setHorizontalHeaderLabels(headers)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        hdr = self._table.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(_COL_IPV4, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(_COL_IPV6, QHeaderView.ResizeMode.Stretch)
        self._table.currentCellChanged.connect(
            lambda row, *_: self._on_row_changed(row)
        )
        layout.addWidget(self._table, 10)

        self._detail = _DetailPanel()
        layout.addWidget(self._detail)

        layout.addStretch(1)

    def _refresh(self) -> None:
        if self._worker and self._worker.isRunning():
            return
        self._btn_refresh.setEnabled(False)
        self._table.setRowCount(0)
        self._detail.setVisible(False)
        self._worker = InterfacesWorker()
        self._worker.ready.connect(self._on_ready)
        self._worker.start()

    def _on_ready(self, ifaces: list) -> None:
        self._btn_refresh.setEnabled(True)
        self._ifaces = ifaces
        t = self._table
        t.setRowCount(0)
        for row_idx, iface in enumerate(ifaces):
            t.insertRow(row_idx)
            connected = iface['state_key'] == 'up'
            state_display = tr("iface_state_up") if connected else \
                            (tr("iface_state_down") if iface['state_key'] == 'down' else iface['state_key'])

            for col, val in enumerate([
                iface['name'], iface['type'], state_display,
                iface['mac'],  iface['ipv4'], iface['ipv6'],
            ]):
                item = QTableWidgetItem(val)
                if col == _COL_STATE:
                    item.setForeground(QColor(_GREEN if connected else _RED))
                t.setItem(row_idx, col, item)

        t.resizeRowsToContents()

    def _on_row_changed(self, row: int) -> None:
        if hasattr(self, '_ifaces') and 0 <= row < len(self._ifaces):
            self._detail.show_iface(self._ifaces[row])
        else:
            self._detail.setVisible(False)
