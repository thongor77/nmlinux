"""Connection Manager — view and control NetworkManager connections via nmcli."""

from __future__ import annotations

import re
import shutil
import subprocess
from typing import NamedTuple

from PySide6.QtCore import Qt, QThread, QTimer, Signal
from PySide6.QtGui import QBrush, QColor, QFont
from PySide6.QtWidgets import (
    QApplication, QComboBox, QFormLayout, QFrame, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QMessageBox, QPushButton, QScrollArea,
    QSplitter, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from nmlinux.core.i18n import tr

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

_GREEN  = QColor('#a6e3a1')
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
    if state == 'activated':   return _GREEN
    if 'activat' in state:     return _YELLOW
    if 'deactivat' in state:   return _ORANGE
    return _MID


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


# ── CLI bar ───────────────────────────────────────────────────────────────────

class _CliBar(QWidget):
    """Terminal-style bar — shows the nmcli command that will be / was executed."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(38)
        self.setStyleSheet('background-color: #11111b; border-radius: 4px;')

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 6, 0)
        layout.setSpacing(6)

        mono = QFont('Monospace', 9)

        prompt = QLabel('$')
        prompt.setFont(mono)
        prompt.setStyleSheet('color: #a6e3a1; font-weight: bold;')
        layout.addWidget(prompt)

        self._lbl = QLabel(tr('conn_cli_idle'))
        self._lbl.setFont(mono)
        self._lbl.setStyleSheet('color: #cdd6f4;')
        self._lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self._lbl, 1)

        self._btn = QPushButton(tr('conn_cli_copy'))
        self._btn.setFlat(True)
        self._btn.setStyleSheet('color: #6c7086; font-size: 10px;')
        self._btn.clicked.connect(self._copy)
        layout.addWidget(self._btn)

    def set_cmd(self, cmd: str) -> None:
        self._lbl.setText(cmd)

    def get_cmd(self) -> str:
        return self._lbl.text()

    def _copy(self) -> None:
        QApplication.clipboard().setText(self._lbl.text())


class _CliButton(QPushButton):
    """Button that previews its nmcli command in the CLI bar when hovered."""

    def __init__(self, label: str, bar: _CliBar,
                 cmd_fn, parent: QWidget | None = None) -> None:
        super().__init__(label, parent)
        self._bar    = bar
        self._cmd_fn = cmd_fn
        self._saved  = ''

    def enterEvent(self, event) -> None:                    # noqa: N802
        self._saved = self._bar.get_cmd()
        cmd = self._cmd_fn()
        if cmd:
            self._bar.set_cmd(cmd)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:                    # noqa: N802
        self._bar.set_cmd(self._saved)
        super().leaveEvent(event)


# ── Page ─────────────────────────────────────────────────────────────────────

class ConnectionManagerPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._conns:   list[_Conn] = []
        self._current: _Conn | None = None
        self._workers: list[QThread] = []
        self._build_ui()

        if not _CMD_NMCLI:
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

        self._cli_bar = _CliBar()

        self._btn_refresh = _CliButton(
            tr('conn_refresh_btn'), self._cli_bar,
            lambda: f'nmcli connection show',
        )
        self._btn_refresh.clicked.connect(self._refresh)
        bar.addWidget(self._btn_refresh)
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
        self._table.currentRowChanged.connect(self._on_select)
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
            tr('conn_connect_btn'), self._cli_bar,
            lambda: (f'nmcli connection up "{self._current.name}"'
                     if self._current else ''),
        )
        self._btn_disconnect = _CliButton(
            tr('conn_disconnect_btn'), self._cli_bar,
            lambda: (f'nmcli connection down "{self._current.name}"'
                     if self._current else ''),
        )
        self._btn_edit = _CliButton(
            tr('conn_edit_btn'), self._cli_bar,
            lambda: (f'nm-connection-editor --edit {self._current.uuid}'
                     if self._current else ''),
        )
        self._btn_delete = _CliButton(
            tr('conn_delete_btn'), self._cli_bar,
            lambda: (f'nmcli connection delete "{self._current.name}"'
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

        # CLI bar — full width at the bottom
        cli_wrap = QHBoxLayout()
        cli_wrap.setContentsMargins(12, 6, 12, 10)
        cli_wrap.addWidget(self._cli_bar)
        root.addLayout(cli_wrap)

        self._set_actions_enabled(False)

    # ── Refresh ──────────────────────────────────────────────────────────────

    def _refresh(self) -> None:
        self._cli_bar.set_cmd('nmcli connection show')
        w = _ListWorker()
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
        self._cli_bar.set_cmd(f'nmcli connection show "{name}"')
        self._set_actions_enabled(True)
        is_active = self._current.state == 'activated'
        self._btn_connect.setEnabled(not is_active)
        self._btn_disconnect.setEnabled(is_active)
        self._btn_edit.setEnabled(bool(_CMD_NMED))

        # Reset detail rows
        for lbl in self._det_rows.values():
            lbl.setText('…')

        # Load full details in background
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
            self._det_rows[row_key].setText(val or '—')

    # ── Actions ──────────────────────────────────────────────────────────────

    def _on_connect(self) -> None:
        if not self._current:
            return
        cmd = [_CMD_NMCLI, 'connection', 'up', self._current.name]
        self._run_action(cmd, tr('conn_status_connecting', name=self._current.name))

    def _on_disconnect(self) -> None:
        if not self._current:
            return
        cmd = [_CMD_NMCLI, 'connection', 'down', self._current.name]
        self._run_action(cmd, tr('conn_status_disconnecting', name=self._current.name))

    def _on_edit(self) -> None:
        if not self._current or not _CMD_NMED:
            self._set_status(tr('conn_no_editor'), error=True)
            return
        import subprocess as sp
        sp.Popen([_CMD_NMED, '--edit', self._current.uuid])

    def _on_delete(self) -> None:
        if not self._current:
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
        self._cli_bar.set_cmd(' '.join(
            f'"{p}"' if ' ' in p else p for p in cmd
        ))
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
        color = '#f38ba8' if error else '#a6e3a1'
        self._status.setStyleSheet(f'color: {color};')
        self._status.setText(msg)

    def hideEvent(self, event) -> None:                     # noqa: N802
        if hasattr(self, '_timer'):
            self._timer.stop()
        super().hideEvent(event)

    def showEvent(self, event) -> None:                     # noqa: N802
        if hasattr(self, '_timer'):
            self._timer.start()
            self._refresh()
        super().showEvent(event)
