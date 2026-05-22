"""Wake on LAN — send magic packets to wake remote machines."""

from __future__ import annotations

import json
import socket
from dataclasses import asdict, dataclass
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFormLayout, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QMessageBox, QPushButton,
    QSplitter, QVBoxLayout, QWidget,
)

from nmlinux.core.cli_bar import get_cli_bar
from nmlinux.core.i18n import tr
from nmlinux.core.theme import color_ok, color_err

_STORE_PATH = Path.home() / '.local' / 'share' / 'nmlinux' / 'wol_hosts.json'


# ── Data model ────────────────────────────────────────────────────────────────

@dataclass
class WolHost:
    name:      str = ''
    mac:       str = ''
    broadcast: str = '255.255.255.255'
    port:      int = 9


class _WolStore:
    def __init__(self) -> None:
        self._hosts: list[WolHost] = []
        self._load()

    def _load(self) -> None:
        if _STORE_PATH.exists():
            try:
                self._hosts = [WolHost(**h) for h in json.loads(_STORE_PATH.read_text())]
            except Exception:
                self._hosts = []

    def _save(self) -> None:
        _STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
        _STORE_PATH.write_text(json.dumps([asdict(h) for h in self._hosts], indent=2))

    def all(self) -> list[WolHost]:
        return list(self._hosts)

    def add(self, host: WolHost) -> None:
        self._hosts.append(host)
        self._save()

    def update(self, idx: int, host: WolHost) -> None:
        self._hosts[idx] = host
        self._save()

    def remove(self, idx: int) -> None:
        del self._hosts[idx]
        self._save()


# ── Magic packet ──────────────────────────────────────────────────────────────

def _parse_mac(mac: str) -> bytes:
    clean = mac.replace(':', '').replace('-', '').replace('.', '')
    if len(clean) != 12:
        raise ValueError(mac)
    return bytes.fromhex(clean)


def _send_magic_packet(mac: str, broadcast: str, port: int) -> None:
    mac_bytes = _parse_mac(mac)
    packet = b'\xff' * 6 + mac_bytes * 16
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.sendto(packet, (broadcast, port))


# ── Page ──────────────────────────────────────────────────────────────────────

class WolPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._store   = _WolStore()
        self._editing: int | None = None
        self._build_ui()
        self._refresh_list()

    # ── Layout ───────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        # Left — saved hosts
        left = QFrame()
        left.setFrameShape(QFrame.Shape.NoFrame)
        lv = QVBoxLayout(left)
        lv.setContentsMargins(8, 8, 4, 8)
        lv.addWidget(QLabel(tr("wol_saved_hosts")))

        self._list = QListWidget()
        self._list.setFrameShape(QFrame.Shape.NoFrame)
        self._list.currentRowChanged.connect(self._on_select)
        lv.addWidget(self._list, 1)

        btns = QHBoxLayout()
        self._btn_add  = QPushButton(tr("wol_add_btn"))
        self._btn_edit = QPushButton(tr("wol_edit_btn"))
        self._btn_del  = QPushButton(tr("wol_delete_btn"))
        self._btn_add.clicked.connect(self._on_new)
        self._btn_edit.clicked.connect(self._on_edit)
        self._btn_del.clicked.connect(self._on_delete)
        for b in (self._btn_add, self._btn_edit, self._btn_del):
            btns.addWidget(b)
        lv.addLayout(btns)
        splitter.addWidget(left)

        # Right — detail / form
        right = QWidget()
        rv = QVBoxLayout(right)
        rv.setContentsMargins(20, 16, 20, 16)
        rv.setSpacing(12)

        self._form_title = QLabel()
        self._form_title.setStyleSheet("font-size: 15px; font-weight: bold;")
        rv.addWidget(self._form_title)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setSpacing(8)

        self._f_name      = QLineEdit()
        self._f_mac       = QLineEdit()
        self._f_broadcast = QLineEdit()
        self._f_port      = QLineEdit()

        self._f_name.setPlaceholderText(tr("wol_ph_name"))
        self._f_mac.setPlaceholderText("AA:BB:CC:DD:EE:FF")
        self._f_broadcast.setPlaceholderText("255.255.255.255")
        self._f_port.setPlaceholderText("9")
        self._f_mac.textChanged.connect(self._update_cli)
        self._f_broadcast.textChanged.connect(self._update_cli)
        self._f_port.textChanged.connect(self._update_cli)

        form.addRow(tr("wol_lbl_name"),      self._f_name)
        form.addRow(tr("wol_lbl_mac"),       self._f_mac)
        form.addRow(tr("wol_lbl_broadcast"), self._f_broadcast)
        form.addRow(tr("wol_lbl_port"),      self._f_port)
        rv.addLayout(form)

        # Action row
        act = QHBoxLayout()
        self._btn_wake   = QPushButton(tr("wol_wake_btn"))
        self._btn_save   = QPushButton(tr("wol_save_btn"))
        self._btn_cancel = QPushButton(tr("wol_cancel_btn"))
        self._btn_wake.setStyleSheet("font-weight: bold; padding: 6px 16px;")
        self._btn_wake.clicked.connect(self._on_wake)
        self._btn_save.clicked.connect(self._on_save)
        self._btn_cancel.clicked.connect(self._on_cancel)
        act.addWidget(self._btn_wake)
        act.addStretch()
        act.addWidget(self._btn_cancel)
        act.addWidget(self._btn_save)
        rv.addLayout(act)

        self._lbl_status = QLabel("")
        self._lbl_status.setWordWrap(True)
        rv.addWidget(self._lbl_status)
        rv.addStretch()

        splitter.addWidget(right)
        splitter.setSizes([220, 620])
        root.addWidget(splitter)

        self._set_form_mode(view=False)

    # ── List ─────────────────────────────────────────────────────────────────

    def _refresh_list(self) -> None:
        current = self._list.currentRow()
        self._list.clear()
        for h in self._store.all():
            label = f"{h.name}  —  {h.mac}" if h.name else h.mac
            self._list.addItem(QListWidgetItem(label))
        if 0 <= current < self._list.count():
            self._list.setCurrentRow(current)

    def _on_select(self, row: int) -> None:
        if row < 0:
            return
        self._editing = row
        self._load_form(self._store.all()[row])
        self._set_form_mode(view=True)
        self._lbl_status.setText("")

    def _on_new(self) -> None:
        self._editing = None
        self._list.clearSelection()
        self._load_form(WolHost())
        self._set_form_mode(view=False)
        self._form_title.setText(tr("wol_form_title_new"))
        self._lbl_status.setText("")
        self._f_mac.setFocus()

    def _on_edit(self) -> None:
        if self._editing is None:
            return
        self._set_form_mode(view=False)
        self._form_title.setText(tr("wol_form_title_edit"))

    def _on_delete(self) -> None:
        row = self._list.currentRow()
        if row < 0:
            return
        h    = self._store.all()[row]
        name = h.name or h.mac
        ans  = QMessageBox.question(
            self, tr("wol_dlg_del_title"), tr("wol_dlg_del_msg", name=name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if ans == QMessageBox.StandardButton.Yes:
            self._store.remove(row)
            self._editing = None
            self._refresh_list()
            self._clear_form()

    # ── Form ─────────────────────────────────────────────────────────────────

    def _on_save(self) -> None:
        mac = self._f_mac.text().strip()
        try:
            _parse_mac(mac)
        except (ValueError, Exception):
            self._set_status(tr("wol_err_invalid_mac"), error=True)
            return

        try:
            port = int(self._f_port.text().strip() or '9')
        except ValueError:
            port = 9

        h = WolHost(
            name      = self._f_name.text().strip(),
            mac       = mac.upper(),
            broadcast = self._f_broadcast.text().strip() or '255.255.255.255',
            port      = port,
        )
        if self._editing is None:
            self._store.add(h)
            self._editing = len(self._store.all()) - 1
        else:
            self._store.update(self._editing, h)

        self._refresh_list()
        self._list.setCurrentRow(self._editing)
        self._set_form_mode(view=True)
        self._lbl_status.setText("")

    def _on_cancel(self) -> None:
        if self._editing is not None:
            self._load_form(self._store.all()[self._editing])
            self._set_form_mode(view=True)
        else:
            self._clear_form()
        self._lbl_status.setText("")

    def _update_cli(self) -> None:
        bar = get_cli_bar()
        if not bar:
            return
        mac  = self._f_mac.text().strip()
        bcast = self._f_broadcast.text().strip() or '255.255.255.255'
        port = self._f_port.text().strip() or '9'
        bar.set_cmd(f'wakeonlan -b {bcast} -p {port} {mac}' if mac else '')

    # ── Wake ─────────────────────────────────────────────────────────────────

    def _on_wake(self) -> None:
        mac = self._f_mac.text().strip()
        if not mac:
            self._set_status(tr("wol_err_no_mac"), error=True)
            return
        broadcast = self._f_broadcast.text().strip() or '255.255.255.255'
        try:
            port = int(self._f_port.text().strip() or '9')
        except ValueError:
            port = 9
        try:
            _send_magic_packet(mac, broadcast, port)
            self._set_status(
                tr("wol_status_sent", mac=mac.upper(), broadcast=broadcast, port=port),
                error=False,
            )
        except Exception as exc:
            self._set_status(tr("common_error_prefix", msg=str(exc)), error=True)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _load_form(self, h: WolHost) -> None:
        self._f_name.setText(h.name)
        self._f_mac.setText(h.mac)
        self._f_broadcast.setText(h.broadcast)
        self._f_port.setText(str(h.port))

    def _clear_form(self) -> None:
        self._editing = None
        for f in (self._f_name, self._f_mac, self._f_broadcast, self._f_port):
            f.clear()
        self._form_title.setText("")
        self._lbl_status.setText("")

    def _set_status(self, msg: str, *, error: bool) -> None:
        color = color_err() if error else color_ok()
        self._lbl_status.setStyleSheet(f"color: {color};")
        self._lbl_status.setText(msg)

    def _set_form_mode(self, *, view: bool) -> None:
        """view=True → fields read-only + Wake button; False → editable + Save/Cancel."""
        for f in (self._f_name, self._f_mac, self._f_broadcast, self._f_port):
            f.setReadOnly(view)
        self._btn_wake.setVisible(view)
        self._btn_save.setVisible(not view)
        self._btn_cancel.setVisible(not view)
        if view and self._editing is not None:
            h = self._store.all()[self._editing]
            self._form_title.setText(h.name or h.mac)

    def showEvent(self, event) -> None:  # noqa: N802
        self._update_cli()
        super().showEvent(event)
