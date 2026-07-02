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

_LOCATION_MSG = (
    "⚠  Wi-Fi names hidden — macOS requires Location Services.  "
    "Open: System Settings › Privacy & Security › Location Services → enable NMLinux"
)


_YELLOW = '#f9e2af'
_MACOS_REDACTED = '<redacted>'
_LOCATION_SENTINEL = '(macos_location_sentinel)'


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
    location_restricted = (ssid == _MACOS_REDACTED)
    if location_restricted:
        ssid = _LOCATION_SENTINEL
    bssid_raw = net.get('spairport_network_bssid', '—')
    bssid = '—' if bssid_raw == _MACOS_REDACTED else bssid_raw

    rssi = 0
    m = re.search(r'(-\d+)\s*dBm', net.get('spairport_signal_noise', ''))
    if m:
        rssi = int(m.group(1))
    pct = max(0, min(100, 2 * (rssi + 100)))
    if location_restricted and rssi == 0:
        pct = 50

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
        'connected':           connected,
        'ssid':                ssid,
        'bssid':               bssid,
        'chan':                 str(chan_num) if chan_num else '—',
        'freq':                 freq,
        'signal':               str(pct),
        'signal_pct':           pct,
        'bar':                  bar_str,
        'security':             security,
        'mode':                 '—',
        'location_restricted': location_restricted,
    }


# CWSecurityMode enum values (CoreWLAN private)
_CW_SEC_NAMES: dict[int, str] = {
    0: '', 1: 'WEP', 2: 'WPA', 3: 'WPA2', 4: 'WPA-Ent.', 5: 'WPA2-Ent.',
    8: 'WPA3', 9: 'WPA3-Ent.',
}
# CWChannelBand enum values
_CW_BAND_NAMES: dict[int, str] = {1: '2.4 GHz', 2: '5 GHz', 3: '6 GHz'}


def _cw_network_to_entry(n, connected: bool) -> dict:
    ssid  = n.ssid() or '(hidden_sentinel)'
    bssid = n.bssid() or '—'
    rssi  = n.rssiValue()
    pct   = max(0, min(100, 2 * (rssi + 100)))

    ch       = n.wlanChannel()
    chan_num = ch.channelNumber() if ch else 0
    band_val = ch.channelBand()   if ch else 0
    freq     = _CW_BAND_NAMES.get(band_val, '?')

    try:
        sec_mode = n.securityMode()
    except Exception:
        sec_mode = 0
    security = _CW_SEC_NAMES.get(sec_mode, '')

    bars    = '▂▄▆█'
    bar_str = ''.join(bars[i] if pct >= (i + 1) * 25 else '░' for i in range(4)) + f'  {pct}%'

    return {
        'connected':           connected,
        'ssid':                ssid,
        'bssid':               bssid,
        'chan':                 str(chan_num) if chan_num else '—',
        'freq':                 freq,
        'signal':               str(pct),
        'signal_pct':           pct,
        'bar':                  bar_str,
        'security':             security,
        'mode':                 '—',
        'location_restricted': False,
    }


def _collect_wifi_macos_corewlan(wifi_iface: str) -> dict | None:
    """Primary collection via CoreWLAN — works when Location Services is granted.
    Returns None if unavailable or LS not yet granted."""
    try:
        import objc
        from CoreWLAN import CWWiFiClient

        client   = CWWiFiClient.sharedWiFiClient()
        cw_iface = client.interface()
        if not cw_iface:
            return None

        connected_ssid = cw_iface.ssid()
        if not connected_ssid:
            return None  # Not connected or LS not granted

        # Prefer cached results (fast); fall back to active scan
        networks: set = cw_iface.cachedScanResults() or set()
        if not networks:
            networks, _ = cw_iface.scanForNetworksWithName_error_(None, objc.nil)
        if not networks:
            return None

        seen: set[str] = set()
        ssids: list[dict] = []
        for n in networks:
            bssid = n.bssid() or '—'
            if bssid in seen:
                continue
            seen.add(bssid)
            ssid = n.ssid() or '(hidden_sentinel)'
            ssids.append(_cw_network_to_entry(n, connected=(ssid == connected_ssid)))

        ssids.sort(key=lambda x: (not x['connected'], -x['signal_pct']))

        return {
            'iface':               wifi_iface,
            'connected_ssid':      connected_ssid,
            'ssids':               ssids,
            'location_restricted': False,
        }
    except Exception:
        return None


def _collect_wifi_macos() -> dict:
    result: dict = {'iface': '—', 'connected_ssid': '', 'ssids': [],
                    'location_restricted': False}

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

    # Try CoreWLAN first (works when Location Services granted)
    cw_result = _collect_wifi_macos_corewlan(wifi_iface)
    if cw_result:
        return cw_result

    # Fallback: system_profiler (returns <redacted> on macOS 26 without LS)
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
            result['location_restricted'] = any(
                s.get('location_restricted') for s in ssids
            )
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

        self._lbl_location = QLabel("")
        self._lbl_location.setWordWrap(True)
        self._lbl_location.setStyleSheet(
            "color: #f9e2af; background: rgba(249,226,175,0.08); "
            "border-radius: 4px; padding: 6px 10px;"
        )
        self._lbl_location.setVisible(False)
        layout.addWidget(self._lbl_location)

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

        location_restricted = data.get('location_restricted', False)
        self._lbl_location.setVisible(location_restricted)
        if location_restricted:
            self._lbl_location.setText(_LOCATION_MSG)

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

            if ap['ssid'] == _LOCATION_SENTINEL:
                ssid_display = '— (Location Services)'
            elif ap['ssid'] == '(hidden_sentinel)':
                ssid_display = hidden_label
            else:
                ssid_display = ap['ssid']
            ssid_item = QTableWidgetItem(ssid_display)
            if ap['connected']:
                font = ssid_item.font()
                font.setBold(True)
                ssid_item.setFont(font)
            if ap.get('location_restricted'):
                ssid_item.setForeground(QColor(_YELLOW))
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
