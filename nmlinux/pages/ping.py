from __future__ import annotations

import json
import re
import subprocess
import time as _time
from dataclasses import asdict, dataclass, field
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QFrame, QSplitter, QListWidget, QListWidgetItem,
    QFormLayout, QMessageBox,
)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt, QThread, Signal

from nmlinux.core.cli_bar import get_cli_bar
from nmlinux.core.i18n import tr
from nmlinux.core.theme import color_ok, color_err
from nmlinux.core.host_actions import HostActionMenu


_TARGET_STORE_PATH = Path.home() / '.local' / 'share' / 'nmlinux' / 'ping_targets.json'


# ── Saved targets directory (data model) ──────────────────────────────────

@dataclass
class PingTarget:
    name:     str = ''
    host:     str = ''
    interval: int = 2


class _PingTargetStore:
    def __init__(self, path: Path | None = None) -> None:
        self._path = path or _TARGET_STORE_PATH
        self._targets: list[PingTarget] = []
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            try:
                raw = json.loads(self._path.read_text())
                fields = PingTarget.__dataclass_fields__
                self._targets = [
                    PingTarget(**{k: v for k, v in d.items() if k in fields})
                    for d in raw
                ]
            except Exception:
                self._targets = []

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps([asdict(t) for t in self._targets], indent=2, ensure_ascii=False)
        )

    def all(self) -> list[PingTarget]:
        return list(self._targets)

    def add(self, target: PingTarget) -> None:
        self._targets.append(target)
        self._save()

    def update(self, idx: int, target: PingTarget) -> None:
        self._targets[idx] = target
        self._save()

    def remove(self, idx: int) -> None:
        del self._targets[idx]
        self._save()

    def has_host(self, host: str) -> bool:
        return any(t.host == host for t in self._targets)


class PingWorker(QThread):
    pinged = Signal(str, bool, float)

    def __init__(self, host: str, interval: int) -> None:
        super().__init__()
        self._host     = host
        self._interval = interval
        self._running  = True

    def run(self) -> None:
        while self._running:
            t0 = _time.monotonic()
            try:
                proc = subprocess.run(
                    ['ping', '-c', '1', '-W', '2', self._host],
                    capture_output=True, text=True, timeout=5,
                )
                if proc.returncode == 0:
                    m = re.search(r'time=(\d+\.?\d*)', proc.stdout)
                    self.pinged.emit(self._host, True, float(m.group(1)) if m else 0.0)
                else:
                    self.pinged.emit(self._host, False, -1.0)
            except Exception:
                self.pinged.emit(self._host, False, -1.0)

            remaining = self._interval - (_time.monotonic() - t0)
            deadline  = _time.monotonic() + max(0.0, remaining)
            while self._running and _time.monotonic() < deadline:
                _time.sleep(0.05)

    def stop(self) -> None:
        self._running = False
        self.wait(7000)


@dataclass
class _Stats:
    sent:     int         = 0
    received: int         = 0
    rtts:     list[float] = field(default_factory=list)
    last_ok:  bool | None = None

    @property
    def loss_pct(self) -> float:
        return 100.0 * (self.sent - self.received) / self.sent if self.sent else 0.0

    def _fmt(self, v: float) -> str:
        return f"{v:.1f}"

    @property
    def rtt_last(self) -> str: return self._fmt(self.rtts[-1])  if self.rtts else "—"
    @property
    def rtt_min(self)  -> str: return self._fmt(min(self.rtts)) if self.rtts else "—"
    @property
    def rtt_avg(self)  -> str: return self._fmt(sum(self.rtts) / len(self.rtts)) if self.rtts else "—"
    @property
    def rtt_max(self)  -> str: return self._fmt(max(self.rtts)) if self.rtts else "—"


_C_DOT, _C_HOST, _C_SENT, _C_LOSS, _C_LAST, _C_MIN, _C_AVG, _C_MAX, _C_SAVE, _C_DEL = range(10)

_GREY  = QColor("#a6adc8")


class PingPage(QWidget):
    action_requested = Signal(str, str, str)  # action_key, ip, host

    def __init__(self) -> None:
        super().__init__()
        self._workers: dict[str, PingWorker] = {}
        self._stats:   dict[str, _Stats]     = {}
        self._rows:    dict[str, int]         = {}
        self._target_store = _PingTargetStore()
        self._dir_editing: int | None = None
        self._build_ui()
        self._refresh_directory_list()

    def set_target(self, host: str) -> None:
        self._input.setText(host)
        self._on_add()

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self._build_directory_panel())
        splitter.addWidget(self._build_monitor_panel())
        splitter.setSizes([220, 700])
        root.addWidget(splitter)

    def _build_directory_panel(self) -> QWidget:
        panel = QFrame()
        panel.setFrameShape(QFrame.Shape.NoFrame)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 4, 8)
        layout.setSpacing(4)
        layout.addWidget(QLabel(tr("ping_dir_title")))

        self._dir_list = QListWidget()
        self._dir_list.setFrameShape(QFrame.Shape.NoFrame)
        self._dir_list.currentRowChanged.connect(self._on_directory_select)
        layout.addWidget(self._dir_list, 1)

        btns = QHBoxLayout()
        self._dir_btn_add    = QPushButton(tr("ping_dir_add_btn"))
        self._dir_btn_edit   = QPushButton(tr("ping_dir_edit_btn"))
        self._dir_btn_delete = QPushButton(tr("ping_dir_delete_btn"))
        self._dir_btn_add.clicked.connect(self._on_directory_new)
        self._dir_btn_edit.clicked.connect(self._on_directory_edit)
        self._dir_btn_delete.clicked.connect(self._on_directory_delete)
        for b in (self._dir_btn_add, self._dir_btn_edit, self._dir_btn_delete):
            btns.addWidget(b)
        layout.addLayout(btns)

        self._dir_form_title = QLabel()
        self._dir_form_title.setStyleSheet("font-weight: bold;")
        layout.addWidget(self._dir_form_title)

        form = QFormLayout()
        form.setSpacing(4)
        self._dir_f_name = QLineEdit()
        self._dir_f_name.setPlaceholderText(tr("ping_dir_ph_name"))
        self._dir_f_host = QLineEdit()
        self._dir_f_interval = QComboBox()
        for label, val in [("1 s", 1), ("2 s", 2), ("5 s", 5), ("10 s", 10), ("30 s", 30)]:
            self._dir_f_interval.addItem(label, val)
        self._dir_f_interval.setCurrentIndex(1)
        form.addRow(tr("ping_dir_lbl_name"),     self._dir_f_name)
        form.addRow(tr("ping_dir_lbl_host"),     self._dir_f_host)
        form.addRow(tr("ping_dir_lbl_interval"), self._dir_f_interval)
        layout.addLayout(form)

        act = QHBoxLayout()
        self._dir_btn_start  = QPushButton(tr("ping_dir_start_btn"))
        self._dir_btn_save   = QPushButton(tr("ping_dir_save_btn"))
        self._dir_btn_cancel = QPushButton(tr("ping_dir_cancel_btn"))
        self._dir_btn_start.setStyleSheet("font-weight: bold;")
        self._dir_btn_start.clicked.connect(self._on_directory_start)
        self._dir_btn_save.clicked.connect(self._on_directory_save)
        self._dir_btn_cancel.clicked.connect(self._on_directory_cancel)
        act.addWidget(self._dir_btn_start)
        act.addStretch()
        act.addWidget(self._dir_btn_cancel)
        act.addWidget(self._dir_btn_save)
        layout.addLayout(act)

        self._set_directory_form_mode(view=False)
        return panel

    def _build_monitor_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel(tr("ping_title"))
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        bar = QHBoxLayout()

        self._input = QLineEdit()
        self._input.setPlaceholderText(tr("ping_placeholder"))
        self._input.returnPressed.connect(self._on_add)
        self._input.textChanged.connect(self._update_cli)

        self._interval_cb = QComboBox()
        for label, val in [("1 s", 1), ("2 s", 2), ("5 s", 5), ("10 s", 10), ("30 s", 30)]:
            self._interval_cb.addItem(label, val)
        self._interval_cb.setCurrentIndex(1)
        self._interval_cb.currentIndexChanged.connect(self._update_cli)

        btn_add   = QPushButton(tr("ping_add_btn"))
        btn_add.setDefault(True)
        btn_add.clicked.connect(self._on_add)

        btn_clear = QPushButton(tr("ping_clear_btn"))
        btn_clear.clicked.connect(self._on_clear_all)

        bar.addWidget(self._input, 1)
        bar.addWidget(QLabel(tr("ping_interval_lbl")))
        bar.addWidget(self._interval_cb)
        bar.addWidget(btn_add)
        bar.addWidget(btn_clear)
        layout.addLayout(bar)

        self._table = QTableWidget(0, 10)
        self._table.setHorizontalHeaderLabels([
            "", tr("ping_col_host"), tr("ping_col_sent"), tr("ping_col_loss"),
            tr("ping_col_last"), tr("common_min"), tr("ping_col_avg"), tr("common_max"), "", "",
        ])
        hdr = self._table.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(_C_HOST, QHeaderView.ResizeMode.Stretch)
        self._table.setColumnWidth(_C_DOT, 28)
        self._table.setColumnWidth(_C_SAVE, 28)
        self._table.setColumnWidth(_C_DEL, 36)

        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.verticalHeader().setVisible(False)
        layout.addWidget(self._table, 1)

        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._on_right_click)
        return panel

    def _update_cli(self) -> None:
        bar = get_cli_bar()
        if not bar:
            return
        host = self._input.text().strip()
        interval = self._interval_cb.currentData()
        bar.set_cmd(f'ping -i {interval} {host}' if host else '')

    # ── Directory ────────────────────────────────────────────────────────────

    def _refresh_directory_list(self) -> None:
        current = self._dir_list.currentRow()
        self._dir_list.clear()
        for t in self._target_store.all():
            label = f"{t.name}  —  {t.host}" if t.name else t.host
            self._dir_list.addItem(QListWidgetItem(label))
        if 0 <= current < self._dir_list.count():
            self._dir_list.setCurrentRow(current)

    def _on_directory_select(self, row: int) -> None:
        if row < 0:
            return
        self._dir_editing = row
        self._load_directory_form(self._target_store.all()[row])
        self._set_directory_form_mode(view=True)

    def _on_directory_new(self) -> None:
        self._dir_editing = None
        self._dir_list.clearSelection()
        self._load_directory_form(PingTarget())
        self._set_directory_form_mode(view=False)
        self._dir_form_title.setText(tr("ping_dir_form_title_new"))
        self._dir_f_name.setFocus()

    def _on_directory_edit(self) -> None:
        if self._dir_editing is None:
            return
        self._set_directory_form_mode(view=False)
        self._dir_form_title.setText(tr("ping_dir_form_title_edit"))

    def _on_directory_delete(self) -> None:
        row = self._dir_list.currentRow()
        if row < 0:
            return
        t = self._target_store.all()[row]
        name = t.name or t.host
        ans = QMessageBox.question(
            self, tr("ping_dir_dlg_del_title"), tr("ping_dir_dlg_del_msg", name=name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if ans == QMessageBox.StandardButton.Yes:
            self._target_store.remove(row)
            self._dir_editing = None
            self._refresh_directory_list()
            self._clear_directory_form()

    def _on_directory_save(self) -> None:
        host = self._dir_f_host.text().strip()
        if not host:
            return
        t = PingTarget(
            name     = self._dir_f_name.text().strip(),
            host     = host,
            interval = self._dir_f_interval.currentData(),
        )
        if self._dir_editing is None:
            self._target_store.add(t)
            self._dir_editing = len(self._target_store.all()) - 1
        else:
            self._target_store.update(self._dir_editing, t)
        self._refresh_directory_list()
        self._dir_list.setCurrentRow(self._dir_editing)
        self._set_directory_form_mode(view=True)

    def _on_directory_cancel(self) -> None:
        if self._dir_editing is not None:
            self._load_directory_form(self._target_store.all()[self._dir_editing])
            self._set_directory_form_mode(view=True)
        else:
            self._clear_directory_form()

    def _on_directory_start(self) -> None:
        if self._dir_editing is None:
            return
        t = self._target_store.all()[self._dir_editing]
        if t.host in self._workers:
            return
        self._add_host(t.host, t.interval)
        self._set_directory_form_mode(view=True)

    def _load_directory_form(self, t: PingTarget) -> None:
        self._dir_f_name.setText(t.name)
        self._dir_f_host.setText(t.host)
        idx = self._dir_f_interval.findData(t.interval)
        self._dir_f_interval.setCurrentIndex(idx if idx >= 0 else 1)

    def _clear_directory_form(self) -> None:
        self._dir_editing = None
        self._dir_f_name.clear()
        self._dir_f_host.clear()
        self._dir_f_interval.setCurrentIndex(1)
        self._dir_form_title.setText("")

    def _set_directory_form_mode(self, *, view: bool) -> None:
        self._dir_f_name.setReadOnly(view)
        self._dir_f_host.setReadOnly(view)
        self._dir_f_interval.setEnabled(not view)
        self._dir_btn_start.setVisible(view)
        self._dir_btn_save.setVisible(not view)
        self._dir_btn_cancel.setVisible(not view)
        if view and self._dir_editing is not None:
            t = self._target_store.all()[self._dir_editing]
            self._dir_form_title.setText(t.name or t.host)
            self._dir_btn_start.setEnabled(t.host not in self._workers)

    def _on_add(self) -> None:
        host = self._input.text().strip()
        if not host or host in self._workers:
            self._input.clear()
            return
        self._input.clear()
        self._add_host(host, self._interval_cb.currentData())

    def _add_host(self, host: str, interval: int) -> None:
        row = self._table.rowCount()
        self._table.insertRow(row)
        self._rows[host]  = row
        self._stats[host] = _Stats()

        dot = QTableWidgetItem("●")
        dot.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        dot.setForeground(_GREY)
        self._table.setItem(row, _C_DOT, dot)

        self._table.setItem(row, _C_HOST, QTableWidgetItem(host))

        for col in (_C_SENT, _C_LOSS, _C_LAST, _C_MIN, _C_AVG, _C_MAX):
            item = QTableWidgetItem("—")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, col, item)

        btn_save = QPushButton("★")
        btn_save.setFixedWidth(28)
        btn_save.setToolTip(tr("ping_dir_save_tooltip"))
        btn_save.setEnabled(not self._target_store.has_host(host))
        btn_save.clicked.connect(
            lambda _checked=False, h=host, i=interval: self._on_save_to_directory(h, i)
        )
        self._table.setCellWidget(row, _C_SAVE, btn_save)

        btn = QPushButton("✕")
        btn.setFixedWidth(28)
        btn.clicked.connect(lambda _checked=False, h=host: self._on_remove(h))
        self._table.setCellWidget(row, _C_DEL, btn)

        worker = PingWorker(host, interval)
        worker.pinged.connect(self._on_ping_result)
        self._workers[host] = worker
        worker.start()

    def _on_save_to_directory(self, host: str, interval: int) -> None:
        if self._target_store.has_host(host):
            return
        self._target_store.add(PingTarget(name='', host=host, interval=interval))
        self._refresh_directory_list()
        row = self._rows.get(host)
        if row is not None:
            btn = self._table.cellWidget(row, _C_SAVE)
            if btn:
                btn.setEnabled(False)

    def _on_remove(self, host: str) -> None:
        w = self._workers.pop(host, None)
        if w:
            w.pinged.disconnect()
            w.stop()

        row = self._rows.pop(host, None)
        if row is None:
            return
        self._stats.pop(host, None)
        self._table.removeRow(row)

        for h in self._rows:
            if self._rows[h] > row:
                self._rows[h] -= 1

    def _on_clear_all(self) -> None:
        for host in list(self._workers):
            w = self._workers.pop(host)
            w.pinged.disconnect()
            w.stop()
        self._stats.clear()
        self._rows.clear()
        self._table.setRowCount(0)

    def _on_ping_result(self, host: str, success: bool, rtt: float) -> None:
        if host not in self._stats:
            return
        st = self._stats[host]
        st.sent += 1
        st.last_ok = success
        if success:
            st.received += 1
            st.rtts.append(rtt)
            if len(st.rtts) > 1000:
                st.rtts = st.rtts[-500:]

        row = self._rows[host]
        t   = self._table

        t.item(row, _C_DOT).setForeground(QColor(color_ok() if success else color_err()))
        t.item(row, _C_SENT).setText(str(st.sent))
        t.item(row, _C_LOSS).setText(f"{st.loss_pct:.1f} %")
        t.item(row, _C_LAST).setText(st.rtt_last if success else tr("ping_timeout"))
        t.item(row, _C_MIN).setText(st.rtt_min)
        t.item(row, _C_AVG).setText(st.rtt_avg)
        t.item(row, _C_MAX).setText(st.rtt_max)

    def _on_right_click(self, pos) -> None:
        row = self._table.rowAt(pos.y())
        if row < 0:
            return
        item = self._table.item(row, _C_HOST)
        if not item:
            return
        host = item.text()
        menu = HostActionMenu(host, host, parent=self)
        menu.action_chosen.connect(self.action_requested)
        menu.exec(self._table.viewport().mapToGlobal(pos))

    def closeEvent(self, event) -> None:
        self._on_clear_all()
        super().closeEvent(event)

    def showEvent(self, event) -> None:  # noqa: N802
        self._update_cli()
        super().showEvent(event)
