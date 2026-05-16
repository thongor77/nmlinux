from __future__ import annotations

import re
import subprocess
import time as _time
from dataclasses import dataclass, field

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView,
)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt, QThread, Signal

from nmlinux.core.cli_bar import get_cli_bar
from nmlinux.core.i18n import tr


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


_C_DOT, _C_HOST, _C_SENT, _C_LOSS, _C_LAST, _C_MIN, _C_AVG, _C_MAX, _C_DEL = range(9)

_GREEN = QColor("#a6e3a1")
_RED   = QColor("#f38ba8")
_GREY  = QColor("#a6adc8")


class PingPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._workers: dict[str, PingWorker] = {}
        self._stats:   dict[str, _Stats]     = {}
        self._rows:    dict[str, int]         = {}
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
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

        self._table = QTableWidget(0, 9)
        self._table.setHorizontalHeaderLabels([
            "", tr("ping_col_host"), tr("ping_col_sent"), tr("ping_col_loss"),
            tr("ping_col_last"), tr("common_min"), tr("ping_col_avg"), tr("common_max"), "",
        ])
        hdr = self._table.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(_C_HOST, QHeaderView.ResizeMode.Stretch)
        self._table.setColumnWidth(_C_DOT, 28)
        self._table.setColumnWidth(_C_DEL, 36)

        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.verticalHeader().setVisible(False)
        layout.addWidget(self._table, 1)

    def _update_cli(self) -> None:
        bar = get_cli_bar()
        if not bar:
            return
        host = self._input.text().strip()
        interval = self._interval_cb.currentData()
        bar.set_cmd(f'ping -i {interval} {host}' if host else '')

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

        btn = QPushButton("✕")
        btn.setFixedWidth(28)
        btn.clicked.connect(lambda _checked=False, h=host: self._on_remove(h))
        self._table.setCellWidget(row, _C_DEL, btn)

        worker = PingWorker(host, interval)
        worker.pinged.connect(self._on_ping_result)
        self._workers[host] = worker
        worker.start()

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

        t.item(row, _C_DOT).setForeground(_GREEN if success else _RED)
        t.item(row, _C_SENT).setText(str(st.sent))
        t.item(row, _C_LOSS).setText(f"{st.loss_pct:.1f} %")
        t.item(row, _C_LAST).setText(st.rtt_last if success else tr("ping_timeout"))
        t.item(row, _C_MIN).setText(st.rtt_min)
        t.item(row, _C_AVG).setText(st.rtt_avg)
        t.item(row, _C_MAX).setText(st.rtt_max)

    def closeEvent(self, event) -> None:
        self._on_clear_all()
        super().closeEvent(event)

    def showEvent(self, event) -> None:  # noqa: N802
        self._update_cli()
        super().showEvent(event)
