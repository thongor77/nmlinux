"""Bandwidth Monitor — real-time network throughput per interface."""

from __future__ import annotations

import math
import platform
import subprocess
import time
from collections import deque
from pathlib import Path

_IS_MACOS = platform.system() == 'Darwin'

from PySide6.QtCore import Qt, QEvent, QTimer
from PySide6.QtGui import (
    QBrush, QColor, QFont, QPainter, QPainterPath, QPalette, QPen,
)
from PySide6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QSplitter, QVBoxLayout, QWidget,
)

from nmlinux.core.cli_bar import get_cli_bar
from nmlinux.core.i18n import tr
from nmlinux.core.theme import is_dark

# ── Fixed semantic colours (work on both themes) ──────────────────────────────
_RX_LINE = QColor('#89b4fa')          # blue  — download
_TX_LINE = QColor('#fab387')          # orange — upload
_RX_FILL = QColor(137, 180, 250, 40)
_TX_FILL = QColor(250, 179, 135, 40)

_WINDOW = 60   # samples (= seconds)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _read_net_dev() -> dict[str, tuple[int, int]]:
    """Return {iface: (rx_bytes, tx_bytes)}."""
    if _IS_MACOS:
        return _read_net_dev_macos()
    return _read_net_dev_linux()


def _read_net_dev_linux() -> dict[str, tuple[int, int]]:
    out: dict[str, tuple[int, int]] = {}
    for line in Path('/proc/net/dev').read_text().splitlines()[2:]:
        parts = line.split()
        if not parts:
            continue
        iface = parts[0].rstrip(':')
        out[iface] = (int(parts[1]), int(parts[9]))
    return out


def _read_net_dev_macos() -> dict[str, tuple[int, int]]:
    out: dict[str, tuple[int, int]] = {}
    try:
        result = subprocess.run(
            ['netstat', '-ib'],
            capture_output=True, text=True, timeout=5,
        )
        for line in result.stdout.splitlines()[1:]:  # skip header
            parts = line.split()
            if len(parts) < 10 or '<Link#' not in parts[2]:
                continue
            try:
                out[parts[0]] = (int(parts[-5]), int(parts[-2]))
            except ValueError:
                continue
    except Exception:
        pass
    return out


def _fmt_speed(bps: float) -> str:
    for unit, thr in (('GB/s', 1 << 30), ('MB/s', 1 << 20), ('KB/s', 1 << 10)):
        if bps >= thr:
            return f'{bps / thr:.2f} {unit}'
    return f'{bps:.0f} B/s'


def _fmt_total(b: int) -> str:
    for unit, thr in (('GB', 1 << 30), ('MB', 1 << 20), ('KB', 1 << 10)):
        if b >= thr:
            return f'{b / thr:.2f} {unit}'
    return f'{b} B'


def _nice_scale(peak: float) -> float:
    if peak <= 0:
        return 1024.0
    exp  = math.floor(math.log10(peak))
    base = 10 ** exp
    for m in (1, 2, 5, 10):
        c = base * m
        if c >= peak:
            return c
    return base * 10


# ── Graph widget ─────────────────────────────────────────────────────────────

class _Graph(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(220)
        self._rx: deque[float] = deque([0.0] * _WINDOW, maxlen=_WINDOW)
        self._tx: deque[float] = deque([0.0] * _WINDOW, maxlen=_WINDOW)

    def push(self, rx_bps: float, tx_bps: float) -> None:
        self._rx.append(rx_bps)
        self._tx.append(tx_bps)
        self.update()

    def clear(self) -> None:
        self._rx = deque([0.0] * _WINDOW, maxlen=_WINDOW)
        self._tx = deque([0.0] * _WINDOW, maxlen=_WINDOW)
        self.update()

    def changeEvent(self, event: QEvent) -> None:  # noqa: N802
        if event.type() == QEvent.Type.ApplicationPaletteChange:
            self.update()
        super().changeEvent(event)

    def paintEvent(self, _event) -> None:                  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        pal  = self.palette()
        c_bg      = pal.color(QPalette.ColorRole.Window)
        c_surface = pal.color(QPalette.ColorRole.Base)
        c_grid    = pal.color(QPalette.ColorRole.Mid)
        c_mid     = pal.color(QPalette.ColorRole.PlaceholderText)

        W, H = self.width(), self.height()
        PL, PR, PT, PB = 72, 12, 12, 28   # left/right/top/bottom padding
        cw = W - PL - PR                   # chart area
        ch = H - PT - PB

        p.fillRect(self.rect(), c_bg)

        # Chart background
        p.fillRect(PL, PT, cw, ch, c_surface)

        peak  = max(max(self._rx, default=0), max(self._tx, default=0), 1.0)
        scale = _nice_scale(peak)

        # Horizontal grid + Y labels
        label_font = QFont('Menlo' if _IS_MACOS else 'Monospace', 7)
        p.setFont(label_font)
        for i in range(5):
            gy = PT + ch - int(i / 4 * ch)
            p.setPen(QPen(c_grid, 1, Qt.PenStyle.DotLine))
            p.drawLine(PL, gy, PL + cw, gy)
            p.setPen(c_mid)
            lbl = _fmt_speed(scale * i / 4)
            p.drawText(0, gy + 4, PL - 4, 12, Qt.AlignmentFlag.AlignRight, lbl)

        # Time axis labels
        p.setPen(c_mid)
        p.drawText(PL, H - 4, '−60s')
        p.drawText(PL + cw // 2 - 12, H - 4, '−30s')
        p.drawText(PL + cw - 16, H - 4, 'now')

        def _polyline(data: deque[float], line_col: QColor, fill_col: QColor) -> None:
            pts = list(data)
            n   = len(pts)
            if n < 2:
                return
            xs = [PL + i * cw / (n - 1) for i in range(n)]
            ys = [PT + ch - pts[i] / scale * ch for i in range(n)]

            # Filled area
            area = QPainterPath()
            area.moveTo(xs[0], PT + ch)
            for x, y in zip(xs, ys):
                area.lineTo(x, y)
            area.lineTo(xs[-1], PT + ch)
            area.closeSubpath()
            p.fillPath(area, QBrush(fill_col))

            # Line on top
            p.setPen(QPen(line_col, 2))
            for i in range(n - 1):
                p.drawLine(int(xs[i]), int(ys[i]), int(xs[i+1]), int(ys[i+1]))

        _polyline(self._rx, _RX_LINE, _RX_FILL)
        _polyline(self._tx, _TX_LINE, _TX_FILL)

        # Border
        p.setPen(QPen(c_grid, 1))
        p.drawRect(PL, PT, cw, ch)

        # Legend
        p.setFont(QFont('Sans', 8))
        for col, label, ox in ((
                _RX_LINE, tr("bw_download"), 0), (_TX_LINE, tr("bw_upload"), 90)):
            p.setPen(col)
            p.drawText(PL + ox, H - 4, label)


# ── Page ─────────────────────────────────────────────────────────────────────

class BandwidthPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._prev: dict[str, tuple[int, int]] = {}
        self._start_rx:  dict[str, int] = {}
        self._start_tx:  dict[str, int] = {}
        self._peak_rx:   dict[str, float] = {}
        self._peak_tx:   dict[str, float] = {}
        self._selected:  str = ''
        self._running:   bool = False
        self._build_ui()

        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)
        # Populate interface list once without starting monitoring
        self._tick_ifaces_only()

    # ── UI ───────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        # Left — interface list
        left = QFrame()
        left.setFrameShape(QFrame.Shape.NoFrame)
        lv = QVBoxLayout(left)
        lv.setContentsMargins(8, 8, 4, 8)
        lv.addWidget(QLabel(tr("bw_ifaces_lbl")))
        self._iface_list = QListWidget()
        self._iface_list.setFrameShape(QFrame.Shape.NoFrame)
        self._iface_list.currentItemChanged.connect(self._on_iface_changed)
        lv.addWidget(self._iface_list, 1)
        splitter.addWidget(left)

        # Right — graph + stats
        right = QWidget()
        rv = QVBoxLayout(right)
        rv.setContentsMargins(12, 12, 12, 12)
        rv.setSpacing(10)

        # Interface name + live speeds + start/stop button
        header = QHBoxLayout()
        self._lbl_iface = QLabel("—")
        self._lbl_iface.setStyleSheet("font-size: 16px; font-weight: bold;")
        header.addWidget(self._lbl_iface)
        header.addStretch()
        self._lbl_rx = QLabel("↓  —")
        self._lbl_rx.setStyleSheet(f"color: {_RX_LINE.name()}; font-size: 14px; font-weight: bold;")
        self._lbl_tx = QLabel("↑  —")
        self._lbl_tx.setStyleSheet(f"color: {_TX_LINE.name()}; font-size: 14px; font-weight: bold;")
        header.addWidget(self._lbl_rx)
        header.addSpacing(16)
        header.addWidget(self._lbl_tx)
        header.addSpacing(16)
        self._btn_startstop = QPushButton(tr("bw_start_btn"))
        self._btn_startstop.setFixedWidth(110)
        self._btn_startstop.clicked.connect(self._on_startstop)
        header.addWidget(self._btn_startstop)
        rv.addLayout(header)

        # Graph
        self._graph = _Graph()
        rv.addWidget(self._graph, 1)

        # Stats row
        stats = QHBoxLayout()
        self._lbl_total_rx  = self._stat_label(tr("bw_total_dl"), "—")
        self._lbl_total_tx  = self._stat_label(tr("bw_total_ul"), "—")
        self._lbl_peak_rx   = self._stat_label(tr("bw_peak_dl"), "—")
        self._lbl_peak_tx   = self._stat_label(tr("bw_peak_ul"), "—")
        for w in (self._lbl_total_rx, self._lbl_total_tx,
                  self._lbl_peak_rx,  self._lbl_peak_tx):
            stats.addWidget(w)
            stats.addStretch()
        rv.addLayout(stats)

        splitter.addWidget(right)
        splitter.setSizes([160, 700])
        root.addWidget(splitter)

    @staticmethod
    def _muted_color() -> str:
        return '#7f849c' if is_dark() else '#7c7f93'

    def _stat_label(self, title: str, value: str) -> QLabel:
        c = self._muted_color()
        lbl = QLabel(f'<span style="color:{c}; font-size:9px">{title}</span>'
                     f'<br><b>{value}</b>')
        lbl.setTextFormat(Qt.TextFormat.RichText)
        return lbl

    def _set_stat(self, lbl: QLabel, title: str, value: str) -> None:
        c = self._muted_color()
        lbl.setText(f'<span style="color:{c}; font-size:9px">{title}</span>'
                    f'<br><b>{value}</b>')

    # ── Start / Stop ─────────────────────────────────────────────────────────

    def _on_startstop(self) -> None:
        if self._running:
            self._timer.stop()
            self._running = False
            self._btn_startstop.setText(tr("bw_start_btn"))
        else:
            self._running = True
            self._btn_startstop.setText(tr("bw_stop_btn"))
            self._tick()
            self._timer.start()

    # ── Sampling ─────────────────────────────────────────────────────────────

    def _tick_ifaces_only(self) -> None:
        """Populate the interface list without starting the graph."""
        current = _read_net_dev()
        existing = {self._iface_list.item(i).text()
                    for i in range(self._iface_list.count())}
        for iface in sorted(k for k in current if not k.startswith('lo')):
            if iface not in existing:
                self._iface_list.addItem(QListWidgetItem(iface))
        if not self._selected and self._iface_list.count():
            self._iface_list.setCurrentRow(0)

    def _tick(self) -> None:
        current = _read_net_dev()

        # Populate / refresh interface list (skip loopback)
        ifaces = [k for k in current if not k.startswith('lo')]
        existing = {self._iface_list.item(i).text()
                    for i in range(self._iface_list.count())}
        for iface in sorted(ifaces):
            if iface not in existing:
                self._iface_list.addItem(QListWidgetItem(iface))
        if not self._selected and self._iface_list.count():
            self._iface_list.setCurrentRow(0)

        # Compute speeds for each interface
        for iface, (rx, tx) in current.items():
            if iface.startswith('lo'):
                continue
            if iface in self._prev:
                p_rx, p_tx = self._prev[iface]
                rx_bps = max(0.0, rx - p_rx)
                tx_bps = max(0.0, tx - p_tx)
            else:
                rx_bps = tx_bps = 0.0
                self._start_rx[iface] = rx
                self._start_tx[iface] = tx

            self._peak_rx[iface] = max(self._peak_rx.get(iface, 0.0), rx_bps)
            self._peak_tx[iface] = max(self._peak_tx.get(iface, 0.0), tx_bps)

            if iface == self._selected:
                self._graph.push(rx_bps, tx_bps)
                self._lbl_rx.setText(f'↓  {_fmt_speed(rx_bps)}')
                self._lbl_tx.setText(f'↑  {_fmt_speed(tx_bps)}')
                total_rx = rx - self._start_rx.get(iface, rx)
                total_tx = tx - self._start_tx.get(iface, tx)
                self._set_stat(self._lbl_total_rx, tr("bw_total_dl"), _fmt_total(total_rx))
                self._set_stat(self._lbl_total_tx, tr("bw_total_ul"), _fmt_total(total_tx))
                self._set_stat(self._lbl_peak_rx,  tr("bw_peak_dl"),  _fmt_speed(self._peak_rx[iface]))
                self._set_stat(self._lbl_peak_tx,  tr("bw_peak_ul"),  _fmt_speed(self._peak_tx[iface]))

        self._prev = current

    # ── Selection ────────────────────────────────────────────────────────────

    def _on_iface_changed(self, item: QListWidgetItem | None, _prev) -> None:
        if item is None:
            return
        self._selected = item.text()
        bar = get_cli_bar()
        if bar:
            bar.set_cmd(f'{"netstat -ib" if _IS_MACOS else "cat /proc/net/dev"}  # interface : {self._selected}')
        self._lbl_iface.setText(self._selected)
        self._graph.clear()
        self._lbl_rx.setText('↓  —')
        self._lbl_tx.setText('↑  —')
        self._set_stat(self._lbl_total_rx, tr("bw_total_dl"), '—')
        self._set_stat(self._lbl_total_tx, tr("bw_total_ul"), '—')
        self._set_stat(self._lbl_peak_rx,  tr("bw_peak_dl"),  '—')
        self._set_stat(self._lbl_peak_tx,  tr("bw_peak_ul"),  '—')

    def hideEvent(self, event) -> None:                    # noqa: N802
        self._timer.stop()
        super().hideEvent(event)

    def showEvent(self, event) -> None:                    # noqa: N802
        if self._running:
            self._timer.start()
        bar = get_cli_bar()
        if bar:
            bar.set_cmd(f'{"netstat -ib" if _IS_MACOS else "cat /proc/net/dev"}  # interface : {self._selected}' if self._selected else '')
        super().showEvent(event)
