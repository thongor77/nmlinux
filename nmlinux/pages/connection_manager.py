"""Connection Manager — view and control NetworkManager / macOS network services."""

from __future__ import annotations

import platform
import re
import shutil
import subprocess
from ipaddress import IPv4Network
from typing import NamedTuple

_IS_MACOS = platform.system() == 'Darwin'

from PySide6.QtCore import Qt, QThread, QTimer, Signal
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QComboBox, QFormLayout, QFrame, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QMessageBox, QPushButton, QScrollArea,
    QSplitter, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from nmlinux.core.cli_bar import get_cli_bar
from nmlinux.core.i18n import tr
from nmlinux.core.theme import color_ok

_CMD_NMCLI = shutil.which('nmcli')
_CMD_NMED  = shutil.which('nm-connection-editor')

_TYPE_MAP: dict[str, str] = {
    '802-11-wireless': 'Wi-Fi',
    '802-3-ethernet':  'Ethernet',
    'vpn':             'VPN',
    'wireguard':       'WireGuard',
    'bridge':          'Bridge',
    'bond':            'Bond',
    'vlan':            'VLAN',
    'tun':             'Tunnel',
    'loopback':        'Loopback',
    'gsm':             'Mobile',
    'cdma':            'Mobile',
    'pppoe':           'PPPoE',
}

_YELLOW = QColor('#f9e2af')
_ORANGE = QColor('#fab387')
_MID    = QColor('#6c7086')

_C_DOT, _C_NAME, _C_TYPE, _C_DEV, _C_STATE = range(5)

# Details fields shown in the right panel (nmcli key → label key)
_DETAIL_FIELDS = [
    ('GENERAL.STATE',                      'conn_det_state'),
    ('GENERAL.DEVICES',                    'conn_det_device'),
    ('connection.autoconnect',             'conn_det_autoconn'),
    ('IP4.ADDRESS[1]',                     'conn_det_ip4'),
    ('IP4.GATEWAY',                        'conn_det_gw4'),
    ('IP4.DNS[1]',                         'conn_det_dns'),
    ('IP6.ADDRESS[1]',                     'conn_det_ip6'),
    ('802-11-wireless.ssid',               'conn_det_ssid'),
    ('802-11-wireless-security.key-mgmt',  'conn_det_security'),
    ('connection.uuid',                    'conn_det_uuid'),
]


class _Conn(NamedTuple):
    name:        str
    uuid:        str
    type:        str
    device:      str
    state:       str
    autoconnect: str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_terse(output: str, n: int) -> list[list[str]]:
    rows = []
    for line in output.strip().splitlines():
        parts = re.split(r'(?<!\\):', line)
        parts = [p.replace('\\:', ':') for p in parts]
        if len(parts) >= n:
            rows.append(parts[:n])
    return rows


def _parse_details(output: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in output.splitlines():
        m = re.match(r'^([^:]+):\s+(.*)', line)
        if m:
            result[m.group(1).strip()] = m.group(2).strip()
    return result


def _friendly_type(t: str) -> str:
    return _TYPE_MAP.get(t, t)


def _state_color(state: str) -> QColor:
    if state == 'activated':   return QColor(color_ok())
    if 'activat' in state:     return _YELLOW
    if 'deactivat' in state:   return _ORANGE
    return _MID


def _macos_type_key(name: str) -> str:
    t = name.lower()
    if 'wi-fi' in t or 'airport' in t or 'wireless' in t:
        return '802-11-wireless'
    if 'ethernet' in t or 'thunderbolt' in t:
        return '802-3-ethernet'
    if 'vpn' in t or 'ikev2' in t or 'l2tp' in t or 'pptp' in t:
        return 'vpn'
    if 'wireguard' in t:
        return 'wireguard'
    if 'bluetooth' in t:
        return 'tun'
    return name


# ── Workers ───────────────────────────────────────────────────────────────────

class _ListWorker(QThread):
    result = Signal(list)
    error  = Signal(str)

    def run(self) -> None:
        try:
            proc = subprocess.run(
                [_CMD_NMCLI, '-t', '-f',
                 'NAME,UUID,TYPE,DEVICE,STATE,AUTOCONNECT',
                 'connection', 'show'],
                capture_output=True, text=True, timeout=10,
            )
            rows  = _parse_terse(proc.stdout, 6)
            conns = [_Conn(*r) for r in rows]
            self.result.emit(conns)
        except Exception as exc:
            self.error.emit(str(exc))


class _DetailWorker(QThread):
    result = Signal(str)

    def __init__(self, name: str) -> None:
        super().__init__()
        self._name = name

    def run(self) -> None:
        try:
            proc = subprocess.run(
                [_CMD_NMCLI, 'connection', 'show', self._name],
                capture_output=True, text=True, timeout=5,
            )
            self.result.emit(proc.stdout)
        except Exception:
            self.result.emit('')


class _ActionWorker(QThread):
    done = Signal(int, str, str)    # returncode, stdout, stderr

    def __init__(self, cmd: list[str]) -> None:
        super().__init__()
        self._cmd = cmd

    def run(self) -> None:
        try:
            proc = subprocess.run(
                self._cmd, capture_output=True, text=True, timeout=30,
            )
            self.done.emit(proc.returncode, proc.stdout, proc.stderr)
        except Exception as exc:
            self.done.emit(-1, '', str(exc))


class _ListWorkerMacos(QThread):
    result = Signal(list)
    error  = Signal(str)

    def run(self) -> None:
        try:
            svc_proc = subprocess.run(
                ['networksetup', '-listallnetworkservices'],
                capture_output=True, text=True, timeout=10,
            )
            services: list[tuple[str, bool]] = []
            for line in svc_proc.stdout.splitlines():
                if line.startswith('An asterisk'):
                    continue
                disabled = line.startswith('*')
                name = line.lstrip('* ').strip()
                if name:
                    services.append((name, disabled))

            hw_proc = subprocess.run(
                ['networksetup', '-listallhardwareports'],
                capture_output=True, text=True, timeout=10,
            )
            port_device: dict[str, str] = {}
            cur_port = None
            for line in hw_proc.stdout.splitlines():
                if line.startswith('Hardware Port:'):
                    cur_port = line.split(':', 1)[1].strip()
                elif line.startswith('Device:') and cur_port:
                    port_device[cur_port] = line.split(':', 1)[1].strip()
                    cur_port = None

            ifc_proc = subprocess.run(
                ['ifconfig', '-a'], capture_output=True, text=True, timeout=5,
            )
            active_devs: set[str] = set()
            cur_dev = None
            for line in ifc_proc.stdout.splitlines():
                m = re.match(r'^(\w+):', line)
                if m:
                    cur_dev = m.group(1)
                elif cur_dev and re.search(r'\binet\s+\d', line):
                    active_devs.add(cur_dev)

            conns: list[_Conn] = []
            for name, disabled in services:
                dev = port_device.get(name, '')
                type_key = _macos_type_key(name)
                if disabled:
                    state = 'disabled'
                elif dev and dev in active_devs:
                    state = 'activated'
                else:
                    state = 'inactive'
                conns.append(_Conn(name=name, uuid=dev, type=type_key,
                                   device=dev, state=state, autoconnect=''))
            self.result.emit(conns)
        except Exception as exc:
            self.error.emit(str(exc))


class _DetailWorkerMacos(QThread):
    result = Signal(str)

    def __init__(self, name: str, device: str) -> None:
        super().__init__()
        self._name   = name
        self._device = device

    def run(self) -> None:
        try:
            self.result.emit(self._collect())
        except Exception:
            self.result.emit('')

    def _collect(self) -> str:
        name, dev = self._name, self._device

        info = subprocess.run(
            ['networksetup', '-getinfo', name],
            capture_output=True, text=True, timeout=5,
        )
        ip4 = subnet = router = ''
        for line in info.stdout.splitlines():
            if line.startswith('IP address:'):
                ip4 = line.split(':', 1)[1].strip()
            elif line.startswith('Subnet mask:'):
                subnet = line.split(':', 1)[1].strip()
            elif line.startswith('Router:'):
                router = line.split(':', 1)[1].strip()

        ip4_cidr = ''
        if ip4 and ip4 not in ('none', 'None'):
            if subnet and subnet not in ('none', 'None'):
                try:
                    prefix = IPv4Network(f'0.0.0.0/{subnet}', strict=False).prefixlen
                    ip4_cidr = f'{ip4}/{prefix}'
                except Exception:
                    ip4_cidr = ip4
            else:
                ip4_cidr = ip4

        dns_proc = subprocess.run(
            ['networksetup', '-getdnsservers', name],
            capture_output=True, text=True, timeout=5,
        )
        dns_lines = dns_proc.stdout.strip().splitlines()
        dns = (', '.join(dns_lines)
               if dns_lines and "There aren" not in dns_lines[0] else '')

        v6_proc = subprocess.run(
            ['networksetup', '-getv6info', name],
            capture_output=True, text=True, timeout=5,
        )
        ip6 = ''
        for line in v6_proc.stdout.splitlines():
            if line.startswith('IPv6 IP address:'):
                ip6 = line.split(':', 1)[1].strip()
                break

        ifc_out = ''
        if dev:
            ifc = subprocess.run(
                ['ifconfig', dev], capture_output=True, text=True, timeout=5,
            )
            ifc_out = ifc.stdout

        mac = ''
        m = re.search(r'ether\s+([0-9a-f:]+)', ifc_out)
        if m:
            mac = m.group(1)
        has_inet = bool(re.search(r'\binet\s+\d', ifc_out))
        state_str = 'activated' if has_inet else 'inactive'

        ssid = ''
        if dev:
            ssid_proc = subprocess.run(
                ['networksetup', '-getairportnetwork', dev],
                capture_output=True, text=True, timeout=5,
            )
            out = ssid_proc.stdout.strip()
            if 'Current Wi-Fi Network:' in out:
                ssid = out.split(':', 1)[1].strip()

        lines = [
            f'GENERAL.STATE:                          {state_str}',
            f'GENERAL.DEVICES:                        {dev or "—"}',
            f'connection.autoconnect:                 --',
        ]
        if ip4_cidr:
            lines.append(f'IP4.ADDRESS[1]:                         {ip4_cidr}')
        if router and router not in ('none', 'None'):
            lines.append(f'IP4.GATEWAY:                            {router}')
        if dns:
            lines.append(f'IP4.DNS[1]:                             {dns}')
        if ip6 and ip6 not in ('none', 'None'):
            lines.append(f'IP6.ADDRESS[1]:                         {ip6}')
        if ssid:
            lines.append(f'802-11-wireless.ssid:                   {ssid}')
        lines.append('802-11-wireless-security.key-mgmt:      --')
        if mac:
            lines.append(f'connection.uuid:                        {mac}')
        return '\n'.join(lines)


# ── CLI bar ───────────────────────────────────────────────────────────────────

class _CliButton(QPushButton):
    """Button that previews its nmcli command in the global CLI bar when hovered."""

    def __init__(self, label: str, cmd_fn,
                 parent: QWidget | None = None) -> None:
        super().__init__(label, parent)
        self._cmd_fn = cmd_fn
        self._saved  = ''

    def enterEvent(self, event) -> None:                    # noqa: N802
        bar = get_cli_bar()
        if bar:
            self._saved = bar.get_cmd()
            cmd = self._cmd_fn()
            if cmd:
                bar.set_cmd(cmd)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:                    # noqa: N802
        bar = get_cli_bar()
        if bar:
            bar.set_cmd(self._saved)
        super().leaveEvent(event)


# ── Page ─────────────────────────────────────────────────────────────────────

class ConnectionManagerPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._conns:   list[_Conn] = []
        self._current: _Conn | None = None
        self._workers: list[QThread] = []
        self._build_ui()

        if not _IS_MACOS and not _CMD_NMCLI:
            self._status.setText(tr('conn_err_nmcli'))
            return

        self._timer = QTimer(self)
        self._timer.setInterval(5000)
        self._timer.timeout.connect(self._refresh)
        self._timer.start()
        self._refresh()

    # ── UI ───────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Toolbar
        bar = QHBoxLayout()
        bar.setContentsMargins(12, 10, 12, 8)
        bar.setSpacing(8)

        self._filter = QComboBox()
        for key in ('conn_filter_all', 'conn_filter_wifi',
                    'conn_filter_eth', 'conn_filter_vpn', 'conn_filter_other'):
            self._filter.addItem(tr(key), key)
        self._filter.currentIndexChanged.connect(self._apply_filter)
        bar.addWidget(self._filter)

        self._search = QLineEdit()
        self._search.setPlaceholderText(tr('conn_search_ph'))
        self._search.textChanged.connect(self._apply_filter)
        bar.addWidget(self._search, 1)

        self._btn_refresh = _CliButton(
            tr('conn_refresh_btn'),
            lambda: ('networksetup -listallnetworkservices' if _IS_MACOS
                     else 'nmcli connection show'),
        )
        self._btn_refresh.clicked.connect(self._refresh)
        bar.addWidget(self._btn_refresh)

        self._btn_export = QPushButton("Export")
        self._btn_export.setFixedWidth(80)
        self._btn_export.clicked.connect(self._export)
        bar.addWidget(self._btn_export)

        root.addLayout(bar)

        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        # ── Left — connection list ───────────────────────────────────────────
        left = QFrame()
        left.setFrameShape(QFrame.Shape.NoFrame)
        lv = QVBoxLayout(left)
        lv.setContentsMargins(0, 0, 0, 0)

        self._table = QTableWidget(0, 5)
        self._table.setHorizontalHeaderLabels([
            '', tr('conn_col_name'), tr('conn_col_type'),
            tr('conn_col_device'), tr('conn_col_state'),
        ])
        hh = self._table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(_C_NAME, QHeaderView.ResizeMode.Stretch)
        self._table.setColumnWidth(_C_DOT, 24)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)
        self._table.currentCellChanged.connect(
            lambda cur_row, _cur_col, _prev_row, _prev_col: self._on_select(cur_row)
        )
        lv.addWidget(self._table)
        splitter.addWidget(left)

        # ── Right — details + actions ────────────────────────────────────────
        right = QWidget()
        rv = QVBoxLayout(right)
        rv.setContentsMargins(16, 12, 16, 12)
        rv.setSpacing(10)

        self._det_title = QLabel('—')
        self._det_title.setStyleSheet('font-size: 15px; font-weight: bold;')
        rv.addWidget(self._det_title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        det_widget = QWidget()
        self._det_form = QFormLayout(det_widget)
        self._det_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self._det_form.setSpacing(6)
        self._det_rows: dict[str, QLabel] = {}
        for _, key in _DETAIL_FIELDS:
            lbl = QLabel('—')
            lbl.setWordWrap(True)
            lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self._det_form.addRow(tr(key) + ' :', lbl)
            self._det_rows[key] = lbl
        scroll.setWidget(det_widget)
        rv.addWidget(scroll, 1)

        # Action buttons
        acts = QHBoxLayout()
        self._btn_connect = _CliButton(
            tr('conn_connect_btn'),
            lambda: (f'networksetup -setnetworkserviceenabled "{self._current.name}" on'
                     if _IS_MACOS and self._current else
                     f'nmcli connection up "{self._current.name}"'
                     if self._current else ''),
        )
        self._btn_disconnect = _CliButton(
            tr('conn_disconnect_btn'),
            lambda: (f'networksetup -setnetworkserviceenabled "{self._current.name}" off'
                     if _IS_MACOS and self._current else
                     f'nmcli connection down "{self._current.name}"'
                     if self._current else ''),
        )
        self._btn_edit = _CliButton(
            tr('conn_edit_btn'),
            lambda: ('open /System/Library/PreferencePanes/Network.prefPane'
                     if _IS_MACOS else
                     f'nm-connection-editor --edit {self._current.uuid}'
                     if self._current else ''),
        )
        self._btn_delete = _CliButton(
            tr('conn_delete_btn'),
            lambda: ('' if _IS_MACOS else
                     f'nmcli connection delete "{self._current.name}"'
                     if self._current else ''),
        )
        self._btn_connect.clicked.connect(self._on_connect)
        self._btn_disconnect.clicked.connect(self._on_disconnect)
        self._btn_edit.clicked.connect(self._on_edit)
        self._btn_delete.clicked.connect(self._on_delete)
        for b in (self._btn_connect, self._btn_disconnect,
                  self._btn_edit, self._btn_delete):
            acts.addWidget(b)
        acts.addStretch()
        rv.addLayout(acts)

        self._status = QLabel('')
        self._status.setWordWrap(True)
        rv.addWidget(self._status)

        splitter.addWidget(right)
        splitter.setSizes([380, 520])
        root.addWidget(splitter, 1)

        self._set_actions_enabled(False)

    # ── Refresh ──────────────────────────────────────────────────────────────

    def _refresh(self) -> None:
        bar = get_cli_bar()
        if bar:
            bar.set_cmd('networksetup -listallnetworkservices' if _IS_MACOS
                        else 'nmcli connection show')
        w = _ListWorkerMacos() if _IS_MACOS else _ListWorker()
        w.result.connect(self._on_list)
        w.error.connect(lambda e: self._status.setText(
            tr('common_error_prefix', msg=e)))
        w.finished.connect(lambda: self._workers.remove(w))
        self._workers.append(w)
        w.start()

    def _on_list(self, conns: list[_Conn]) -> None:
        prev_name = self._current.name if self._current else None
        self._conns = conns
        self._apply_filter()
        # Restore selection
        if prev_name:
            for r in range(self._table.rowCount()):
                if self._table.item(r, _C_NAME).text() == prev_name:
                    self._table.setCurrentCell(r, _C_NAME)
                    break

    def _apply_filter(self) -> None:
        f_key  = self._filter.currentData()
        search = self._search.text().strip().lower()
        row    = 0
        self._table.setRowCount(0)
        for c in self._conns:
            if f_key == 'conn_filter_wifi'  and c.type != '802-11-wireless': continue
            if f_key == 'conn_filter_eth'   and c.type != '802-3-ethernet':  continue
            if f_key == 'conn_filter_vpn'   and c.type not in ('vpn', 'wireguard'): continue
            if f_key == 'conn_filter_other' and c.type in (
                '802-11-wireless', '802-3-ethernet', 'vpn', 'wireguard'): continue
            if search and search not in c.name.lower() and search not in c.device.lower():
                continue
            self._table.insertRow(row)
            color = _state_color(c.state)
            dot = QTableWidgetItem('●' if c.state == 'activated' else '○')
            dot.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            dot.setForeground(QBrush(color))
            dot.setData(Qt.ItemDataRole.UserRole, c.name)
            self._table.setItem(row, _C_DOT,   dot)
            self._table.setItem(row, _C_NAME,  QTableWidgetItem(c.name))
            self._table.setItem(row, _C_TYPE,  QTableWidgetItem(_friendly_type(c.type)))
            self._table.setItem(row, _C_DEV,   QTableWidgetItem(c.device if c.device != '--' else ''))
            state_item = QTableWidgetItem(c.state if c.state != '--' else '')
            state_item.setForeground(QBrush(color))
            self._table.setItem(row, _C_STATE, state_item)
            row += 1

    # ── Selection ────────────────────────────────────────────────────────────

    def _on_select(self, row: int) -> None:
        if row < 0:
            self._current = None
            self._set_actions_enabled(False)
            self._det_title.setText('—')
            return
        name_item = self._table.item(row, _C_NAME)
        if not name_item:
            return
        name = name_item.text()
        self._current = next((c for c in self._conns if c.name == name), None)
        if not self._current:
            return

        self._det_title.setText(name)
        bar = get_cli_bar()
        if bar:
            bar.set_cmd(f'networksetup -getinfo "{name}"' if _IS_MACOS
                        else f'nmcli connection show "{name}"')
        self._set_actions_enabled(True)
        is_active = self._current.state == 'activated'
        self._btn_connect.setEnabled(not is_active)
        self._btn_disconnect.setEnabled(is_active)
        if _IS_MACOS:
            self._btn_edit.setEnabled(True)
            self._btn_delete.setEnabled(False)
        else:
            self._btn_edit.setEnabled(bool(_CMD_NMED))

        for lbl in self._det_rows.values():
            lbl.setText('…')

        if _IS_MACOS:
            w = _DetailWorkerMacos(name, self._current.device)
        else:
            w = _DetailWorker(name)
        w.result.connect(self._on_details)
        w.finished.connect(lambda: self._workers.remove(w))
        self._workers.append(w)
        w.start()

    def _on_details(self, output: str) -> None:
        if not output:
            return
        d = _parse_details(output)
        for nmcli_key, row_key in _DETAIL_FIELDS:
            val = d.get(nmcli_key, '').strip()
            if not val or val == '--':
                val = ''
            if nmcli_key == 'IP4.ADDRESS[1]' and val:
                m = re.search(r'/(\d+)$', val)
                if m:
                    mask = str(IPv4Network(f'0.0.0.0/{m.group(1)}', strict=False).netmask)
                    val = f'{val}  ({mask})'
            self._det_rows[row_key].setText(val or '—')

    # ── Actions ──────────────────────────────────────────────────────────────

    def _on_connect(self) -> None:
        if not self._current:
            return
        if _IS_MACOS:
            script = (f'do shell script "networksetup -setnetworkserviceenabled '
                      f'\\"{self._current.name}\\" on"'
                      f' with administrator privileges')
            cmd = ['osascript', '-e', script]
        else:
            cmd = [_CMD_NMCLI, 'connection', 'up', self._current.name]
        self._run_action(cmd, tr('conn_status_connecting', name=self._current.name))

    def _on_disconnect(self) -> None:
        if not self._current:
            return
        if _IS_MACOS:
            script = (f'do shell script "networksetup -setnetworkserviceenabled '
                      f'\\"{self._current.name}\\" off"'
                      f' with administrator privileges')
            cmd = ['osascript', '-e', script]
        else:
            cmd = [_CMD_NMCLI, 'connection', 'down', self._current.name]
        self._run_action(cmd, tr('conn_status_disconnecting', name=self._current.name))

    def _on_edit(self) -> None:
        if _IS_MACOS:
            subprocess.Popen(['open',
                              '/System/Library/PreferencePanes/Network.prefPane'])
            return
        if not self._current or not _CMD_NMED:
            self._set_status(tr('conn_no_editor'), error=True)
            return
        subprocess.Popen([_CMD_NMED, '--edit', self._current.uuid])

    def _on_delete(self) -> None:
        if _IS_MACOS or not self._current:
            return
        ans = QMessageBox.question(
            self, tr('conn_dlg_del_title'),
            tr('conn_dlg_del_msg', name=self._current.name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if ans != QMessageBox.StandardButton.Yes:
            return
        cmd = [_CMD_NMCLI, 'connection', 'delete', self._current.name]
        self._run_action(cmd, tr('conn_status_deleting', name=self._current.name))

    def _run_action(self, cmd: list[str], status: str) -> None:
        bar = get_cli_bar()
        if bar:
            bar.set_cmd(' '.join(f'"{p}"' if ' ' in p else p for p in cmd))
        self._set_status(status, error=False)
        self._set_actions_enabled(False)
        if hasattr(self, '_timer'):
            self._timer.stop()

        w = _ActionWorker(cmd)
        w.done.connect(self._on_action_done)
        w.finished.connect(lambda: self._workers.remove(w))
        self._workers.append(w)
        w.start()

    def _on_action_done(self, code: int, stdout: str, stderr: str) -> None:
        if code == 0:
            self._set_status(tr('conn_status_ok'), error=False)
        else:
            msg = (stderr or stdout).strip().splitlines()[0] if (stderr or stdout) else f'code {code}'
            self._set_status(tr('common_error_prefix', msg=msg), error=True)
        self._set_actions_enabled(True)
        if hasattr(self, '_timer'):
            self._timer.start()
        self._refresh()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _set_actions_enabled(self, enabled: bool) -> None:
        for b in (self._btn_connect, self._btn_disconnect,
                  self._btn_edit, self._btn_delete):
            b.setEnabled(enabled)

    def _set_status(self, msg: str, *, error: bool) -> None:
        from nmlinux.core.theme import color_err
        color = color_err() if error else color_ok()
        self._status.setStyleSheet(f'color: {color};')
        self._status.setText(msg)

    def _export(self) -> None:
        from PySide6.QtWidgets import QMessageBox
        from datetime import datetime
        from nmlinux.export_manager import save_export
        from nmlinux.core.export_dialog import open_export_dialog

        filepath, fmt = open_export_dialog(self, "Export Connections", "connections")
        if not filepath:
            return

        data = {
            "timestamp": datetime.now().isoformat(),
            "module": "Connections",
            "connections": [c._asdict() for c in self._conns],
        }
        error = save_export(data, fmt, filepath)
        if error:
            QMessageBox.warning(self, "Export Error", error)
        else:
            QMessageBox.information(self, "Export", f"Saved to:\n{filepath}")

    def hideEvent(self, event) -> None:                     # noqa: N802
        if hasattr(self, '_timer'):
            self._timer.stop()
        super().hideEvent(event)

    def showEvent(self, event) -> None:                     # noqa: N802
        if hasattr(self, '_timer'):
            self._timer.start()
            self._refresh()
        super().showEvent(event)
