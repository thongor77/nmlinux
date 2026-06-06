from __future__ import annotations

import json
import platform
import re
import subprocess

_IS_MACOS = platform.system() == 'Darwin'

from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
)
from PySide6.QtCore import Qt, QThread, Signal

from nmlinux.core.cli_bar import get_cli_bar
from nmlinux.core.i18n import tr
from nmlinux.core.theme import color_ok, color_err


_YELLOW = '#f9e2af'


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


class WifiWorker(QThread):
    ready = Signal(dict)

    def run(self) -> None:
        self.ready.emit(_collect_wifi())


def _collect_wifi() -> dict:
    return _collect_wifi_macos() if _IS_MACOS else _collect_wifi_linux()


def _collect_wifi_linux() -> dict:
    result: dict = {'iface': '—', 'connected_ssid': '', 'ssids': []}

    wifi_iface = '—'
    try:
        raw = subprocess.run(
            ['nmcli', '-t', '-f', 'DEVICE,TYPE', 'dev'],
            capture_output=True, text=True, timeout=4,
        ).stdout
        for line in raw.splitlines():
            parts = _parse_terse(line)
            if len(parts) >= 2 and parts[1] == 'wifi':
                wifi_iface = parts[0]
                break
    except Exception:
        pass

    result['iface'] = wifi_iface
    if wifi_iface == '—':
        return result

    try:
        subprocess.run(
            ['nmcli', 'dev', 'wifi', 'rescan', 'ifname', wifi_iface],
            capture_output=True, timeout=6,
        )
    except Exception:
        pass

    try:
        raw = subprocess.run(
            ['nmcli', '-t', '-f',
             'IN-USE,SSID,BSSID,CHAN,FREQ,SIGNAL,SECURITY,MODE',
             'dev', 'wifi', 'list', 'ifname', wifi_iface],
            capture_output=True, text=True, timeout=8,
        ).stdout

        seen: set[str] = set()
        ssids: list[dict] = []
        for line in raw.splitlines():
            parts = _parse_terse(line)
            if len(parts) < 8:
                continue
            in_use, ssid, bssid, chan, freq, signal, security, mode = (
                parts[0], parts[1], parts[2], parts[3],
                parts[4], parts[5], parts[6], parts[7],
            )
            if not ssid:
                ssid = '(hidden_sentinel)'
            if bssid in seen:
                continue
            seen.add(bssid)

            connected = in_use == '*'
            if connected:
                result['connected_ssid'] = ssid

            try:
                pct = int(signal)
            except ValueError:
                pct = 0
            bars = '▂▄▆█'
            bar_str = ''.join(
                bars[i] if pct >= (i + 1) * 25 else '░'
                for i in range(4)
            ) + f'  {signal}%'

            ssids.append({
                'connected':  connected,
                'ssid':       ssid,
                'bssid':      bssid,
                'chan':       chan,
                'freq':       freq,
                'signal':     signal,
                'signal_pct': pct,
                'bar':        bar_str,
                'security':   security,
                'mode':       mode,
            })

        ssids.sort(key=lambda x: (not x['connected'], -x['signal_pct']))
        result['ssids'] = ssids
    except Exception:
        pass

    return result


def _parse_sp_security(raw: str) -> str:
    """'spairport_security_mode_wpa2_personal' → 'WPA2', empty/none → ''."""
    if not raw or 'none' in raw:
        return ''
    s = raw.replace('spairport_security_mode_', '')
    if s.startswith('wpa3'):
        return 'WPA3'
    if s.startswith('wpa2'):
        return 'WPA2'
    if s.startswith('wpa'):
        return 'WPA'
    return s


def _sp_network_to_entry(net: dict, connected: bool) -> dict:
    ssid  = net.get('_name', '') or '(hidden_sentinel)'
    bssid = net.get('spairport_network_bssid', '—')

    rssi = 0
    m = re.search(r'(-\d+)\s*dBm', net.get('spairport_signal_noise', ''))
    if m:
        rssi = int(m.group(1))
    pct = max(0, min(100, 2 * (rssi + 100)))

    chan_raw = net.get('spairport_network_channel', '')
    chan_m   = re.search(r'(\d+)', chan_raw)
    chan_num = int(chan_m.group(1)) if chan_m else 0
    freq     = '2.4 GHz' if 0 < chan_num <= 14 else '5 GHz'

    security = _parse_sp_security(net.get('spairport_security_mode', ''))

    bars    = '▂▄▆█'
    bar_str = ''.join(
        bars[i] if pct >= (i + 1) * 25 else '░'
        for i in range(4)
    ) + f'  {pct}%'

    return {
        'connected':  connected,
        'ssid':       ssid,
        'bssid':      bssid,
        'chan':        str(chan_num) if chan_num else '—',
        'freq':        freq,
        'signal':      str(pct),
        'signal_pct':  pct,
        'bar':         bar_str,
        'security':    security,
        'mode':        '—',
    }


def _collect_wifi_macos() -> dict:
    result: dict = {'iface': '—', 'connected_ssid': '', 'ssids': []}

    wifi_iface = '—'
    try:
        raw = subprocess.run(
            ['networksetup', '-listallhardwareports'],
            capture_output=True, text=True, timeout=4,
        ).stdout
        in_wifi = False
        for line in raw.splitlines():
            s = line.strip()
            if s.startswith('Hardware Port:') and 'Wi-Fi' in s:
                in_wifi = True
            elif in_wifi and s.startswith('Device:'):
                wifi_iface = s.split(':', 1)[1].strip()
                break
            elif in_wifi and s == '':
                in_wifi = False
    except Exception:
        pass

    result['iface'] = wifi_iface
    if wifi_iface == '—':
        return result

    try:
        raw = subprocess.run(
            ['system_profiler', 'SPAirPortDataType', '-json'],
            capture_output=True, text=True, timeout=15,
        ).stdout
        data = json.loads(raw)

        interfaces = (data.get('SPAirPortDataType', [{}])[0]
                         .get('spairport_airport_interfaces', []))

        for iface_data in interfaces:
            if iface_data.get('_name') != wifi_iface:
                continue

            current = iface_data.get('spairport_current_network_information', {})
            connected_ssid = current.get('_name', '')
            result['connected_ssid'] = connected_ssid

            ssids: list[dict] = []
            if current:
                ssids.append(_sp_network_to_entry(current, connected=True))

            for net in iface_data.get('spairport_airport_other_local_wireless_networks', []):
                ssids.append(_sp_network_to_entry(net, connected=False))

            ssids.sort(key=lambda x: (not x['connected'], -x['signal_pct']))
            result['ssids'] = ssids
            break

    except Exception:
        pass

    return result


_COL_DOT, _COL_SSID, _COL_BSSID, _COL_CHAN, _COL_FREQ, _COL_SIGNAL, _COL_SEC = range(7)


class WifiPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._worker: WifiWorker | None = None
        self._build_ui()
        self._refresh()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        title  = QLabel(tr("wifi_title"))
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        self._btn_refresh = QPushButton(tr("wifi_scan_btn"))
        self._btn_refresh.setFixedWidth(100)
        self._btn_refresh.clicked.connect(self._refresh)
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(self._btn_refresh)
        layout.addLayout(header)

        info_row = QHBoxLayout()
        self._lbl_iface  = QLabel(tr("wifi_iface_label", iface="—"))
        self._lbl_status = QLabel("")
        info_row.addWidget(self._lbl_iface)
        info_row.addStretch(1)
        info_row.addWidget(self._lbl_status)
        layout.addLayout(info_row)

        headers = [
            "●",
            "SSID",
            "BSSID",
            tr("wifi_col_chan"),
            tr("wifi_col_freq"),
            tr("wifi_col_signal"),
            tr("wifi_col_sec"),
        ]
        self._table = QTableWidget(0, len(headers))
        self._table.setHorizontalHeaderLabels(headers)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)

        hdr = self._table.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(_COL_SSID, QHeaderView.ResizeMode.Stretch)
        self._table.setColumnWidth(_COL_DOT, 28)
        hdr.setSectionResizeMode(_COL_DOT, QHeaderView.ResizeMode.Fixed)

        layout.addWidget(self._table, 10)
        layout.addStretch(1)

    def _refresh(self) -> None:
        if self._worker and self._worker.isRunning():
            return
        self._btn_refresh.setEnabled(False)
        self._lbl_status.setText(tr("wifi_scanning"))
        self._table.setRowCount(0)
        self._worker = WifiWorker()
        self._worker.ready.connect(self._on_ready)
        self._worker.start()

    def _on_ready(self, data: dict) -> None:
        self._btn_refresh.setEnabled(True)
        iface = data.get('iface', '—')
        ssids = data.get('ssids', [])

        self._lbl_iface.setText(tr("wifi_iface_label", iface=iface))

        if iface == '—':
            self._lbl_status.setText(tr("wifi_no_iface"))
            self._lbl_status.setStyleSheet(f"color: {color_err()};")
            return

        count = len(ssids)
        self._lbl_status.setText(tr("wifi_networks", count=count))
        self._lbl_status.setStyleSheet("")

        t = self._table
        t.setRowCount(0)
        hidden_label = tr("wifi_hidden")
        open_label   = tr("wifi_open")

        for row_idx, ap in enumerate(ssids):
            t.insertRow(row_idx)

            dot_item = QTableWidgetItem('●' if ap['connected'] else '')
            dot_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if ap['connected']:
                dot_item.setForeground(QColor(color_ok()))
            t.setItem(row_idx, _COL_DOT, dot_item)

            ssid_display = hidden_label if ap['ssid'] == '(hidden_sentinel)' else ap['ssid']
            ssid_item = QTableWidgetItem(ssid_display)
            if ap['connected']:
                font = ssid_item.font()
                font.setBold(True)
                ssid_item.setFont(font)
            t.setItem(row_idx, _COL_SSID, ssid_item)

            t.setItem(row_idx, _COL_BSSID, QTableWidgetItem(ap['bssid']))
            t.setItem(row_idx, _COL_CHAN,  QTableWidgetItem(ap['chan']))
            t.setItem(row_idx, _COL_FREQ,  QTableWidgetItem(ap['freq']))

            signal_item = QTableWidgetItem(ap['bar'])
            pct = ap['signal_pct']
            if pct >= 66:
                signal_item.setForeground(QColor(color_ok()))
            elif pct >= 33:
                signal_item.setForeground(QColor(_YELLOW))
            else:
                signal_item.setForeground(QColor(color_err()))
            t.setItem(row_idx, _COL_SIGNAL, signal_item)

            sec_display = open_label if not ap['security'] else ap['security']
            sec_item = QTableWidgetItem(sec_display)
            if not ap['security']:
                sec_item.setForeground(QColor(_YELLOW))
            t.setItem(row_idx, _COL_SEC, sec_item)

        t.resizeRowsToContents()

    def showEvent(self, event) -> None:  # noqa: N802
        bar = get_cli_bar()
        if bar:
            bar.set_cmd("system_profiler SPAirPortDataType -json" if _IS_MACOS else "nmcli dev wifi list")
        super().showEvent(event)
