"""Speed Test — mesure de débit internet via curl + ping."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from collections import deque
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QEvent, QThread, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPainterPath, QPen, QPalette
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QProgressBar,
    QPushButton, QSizePolicy, QVBoxLayout, QWidget,
)

from nmlinux.core.cli_bar import get_cli_bar
from nmlinux.core.i18n import tr
from nmlinux.core.theme import color_ok, color_err

_CMD_CURL  = shutil.which('curl')
_CMD_PING  = shutil.which('ping')

_HISTORY_FILE = Path.home() / '.local' / 'share' / 'nmlinux' / 'speedtest_history.json'
_PERSIST_MAX  = 5

_DL_URL  = 'https://speed.cloudflare.com/__down?bytes=25000000'   # 25 MB
_UL_URL  = 'https://speed.cloudflare.com/__up'
_PING_HOST = '1.1.1.1'

_BLUE_LINE  = QColor('#89b4fa')
_BLUE_FILL  = QColor(137, 180, 250, 40)
_ORA_LINE   = QColor('#fab387')
_ORA_FILL   = QColor(250, 179, 135, 40)
_PING_COL   = QColor('#f9e2af')

_HISTORY_MAX = 10
_PING_AVG_RE = re.compile(r'=\s*[\d.]+/([\d.]+)/')


# ── Worker ────────────────────────────────────────────────────────────────────

class SpeedTestWorker(QThread):
    phase_changed = Signal(str)    # 'ping' | 'download' | 'upload' | 'done'
    ping_done     = Signal(float)  # ms
    download_done = Signal(float)  # Mbit/s
    upload_done   = Signal(float)  # Mbit/s
    error         = Signal(str)
    finished      = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._stop = False
        self._proc: subprocess.Popen | None = None

    def run(self) -> None:
        try:
            # ── Ping ─────────────────────────────────────────────────────────
            self.phase_changed.emit('ping')
            ping = self._measure_ping()
            if self._stop:
                return
            if ping is not None:
                self.ping_done.emit(ping)

            # ── Download ──────────────────────────────────────────────────────
            self.phase_changed.emit('download')
            dl = self._measure_download()
            if self._stop:
                return
            if dl is not None:
                self.download_done.emit(dl)
            else:
                self.error.emit(tr("speed_err_dl"))
                return

            # ── Upload ────────────────────────────────────────────────────────
            self.phase_changed.emit('upload')
            ul = self._measure_upload()
            if self._stop:
                return
            if ul is not None:
                self.upload_done.emit(ul)

            self.phase_changed.emit('done')
        except Exception as exc:
            self.error.emit(str(exc))
        finally:
            self.finished.emit()

    def _run(self, args: list[str], timeout: int) -> str | None:
        """Run a command, return stdout or None on failure."""
        try:
            self._proc = subprocess.Popen(
                args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            )
            stdout, _ = self._proc.communicate(timeout=timeout)
            self._proc = None
            return stdout.strip() if self._proc is None else stdout.strip()
        except Exception:
            return None

    def _measure_ping(self) -> float | None:
        if not _CMD_PING:
            return None
        try:
            self._proc = subprocess.Popen(
                [_CMD_PING, '-c', '5', '-q', _PING_HOST],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            )
            stdout, _ = self._proc.communicate(timeout=15)
            self._proc = None
            m = _PING_AVG_RE.search(stdout)
            return float(m.group(1)) if m else None
        except Exception:
            return None

    def _measure_download(self) -> float | None:
        if not _CMD_CURL:
            return None
        try:
            self._proc = subprocess.Popen(
                [_CMD_CURL, '-o', '/dev/null', '-s', '-w', '%{speed_download}',
                 '--max-time', '45', _DL_URL],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            )
            stdout, _ = self._proc.communicate(timeout=50)
            self._proc = None
            val = float(stdout.strip())
            return val * 8 / 1_000_000 if val > 0 else None
        except Exception:
            return None

    def _measure_upload(self) -> float | None:
        if not _CMD_CURL:
            return None
        tmpfile = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.bin') as f:
                f.write(b'\x00' * (10 * 1024 * 1024))   # 10 MB
                tmpfile = f.name
            self._proc = subprocess.Popen(
                [_CMD_CURL, '-X', 'POST', '-o', '/dev/null', '-s',
                 '-w', '%{speed_upload}', '--max-time', '45',
                 '-T', tmpfile, _UL_URL],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            )
            stdout, _ = self._proc.communicate(timeout=50)
            self._proc = None
            val = float(stdout.strip())
            return val * 8 / 1_000_000 if val > 0 else None
        except Exception:
            return None
        finally:
            if tmpfile and os.path.exists(tmpfile):
                os.unlink(tmpfile)

    def stop(self) -> None:
        self._stop = True
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()
        self.wait(10000)


# ── Metric card ───────────────────────────────────────────────────────────────

class _MetricCard(QFrame):
    def __init__(self, label: str, unit: str) -> None:
        super().__init__()
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setMinimumWidth(180)
        self._unit = unit

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(4)

        # Label en haut — toujours visible
        self._lbl_name = QLabel(label.upper())
        self._lbl_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font_name = QFont()
        font_name.setPointSize(10)
        font_name.setBold(True)
        self._lbl_name.setFont(font_name)

        # Valeur — grand chiffre
        self._lbl_value = QLabel("—")
        self._lbl_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font_val = QFont()
        font_val.setPointSize(32)
        font_val.setBold(True)
        self._lbl_value.setFont(font_val)

        # Unité en dessous
        self._lbl_unit = QLabel(unit)
        self._lbl_unit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font_unit = QFont()
        font_unit.setPointSize(11)
        self._lbl_unit.setFont(font_unit)

        layout.addWidget(self._lbl_name)
        layout.addWidget(self._lbl_value)
        layout.addWidget(self._lbl_unit)

    def set_value(self, v: float, color: str | None = None) -> None:
        text = f"{v:.1f}" if v >= 10 else f"{v:.2f}"
        self._lbl_value.setText(text)
        pal = self._lbl_value.palette()
        if color:
            from PySide6.QtGui import QPalette
            pal2 = QPalette(pal)
            pal2.setColor(QPalette.ColorRole.WindowText, QColor(color))
            self._lbl_value.setPalette(pal2)
        else:
            self._lbl_value.setPalette(pal)

    def reset(self) -> None:
        self._lbl_value.setText("—")
        self._lbl_value.setPalette(self.palette())

    def set_active(self, active: bool) -> None:
        from PySide6.QtGui import QPalette
        pal = self._lbl_name.palette()
        if active:
            pal2 = QPalette(pal)
            pal2.setColor(QPalette.ColorRole.WindowText, _BLUE_LINE)
            self._lbl_name.setPalette(pal2)
        else:
            self._lbl_name.setPalette(self.palette())


# ── History graph ─────────────────────────────────────────────────────────────

class _SpeedGraph(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setMinimumHeight(160)
        self._history: deque[dict] = deque(maxlen=_HISTORY_MAX)

    def push(self, dl: float, ul: float, ping: float) -> None:
        self._history.append({'dl': dl, 'ul': ul, 'ping': ping,
                               'ts': datetime.now().strftime('%H:%M')})
        self.update()

    def clear(self) -> None:
        self._history.clear()
        self.update()

    def changeEvent(self, event: QEvent) -> None:  # noqa: N802
        if event.type() == QEvent.Type.ApplicationPaletteChange:
            self.update()
        super().changeEvent(event)

    def paintEvent(self, _event) -> None:           # noqa: N802
        if not self._history:
            p = QPainter(self)
            p.setPen(self.palette().color(QPalette.ColorRole.PlaceholderText))
            p.setFont(QFont('Sans', 10))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, tr("speed_graph_hint"))
            return

        pal  = self.palette()
        c_bg      = pal.color(QPalette.ColorRole.Window)
        c_surface = pal.color(QPalette.ColorRole.Base)
        c_grid    = pal.color(QPalette.ColorRole.Mid)
        c_text    = pal.color(QPalette.ColorRole.PlaceholderText)

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        W, H = self.width(), self.height()
        PL, PR, PT, PB = 52, 12, 12, 24
        cw = W - PL - PR
        ch = H - PT - PB

        p.fillRect(self.rect(), c_bg)
        p.fillRect(PL, PT, cw, ch, c_surface)

        pts = list(self._history)
        n   = len(pts)

        all_speeds = [r['dl'] for r in pts] + [r['ul'] for r in pts]
        peak = max(max(all_speeds, default=1), 1.0)
        # Round up to a nice value
        scale = _nice(peak)

        # Grid + Y labels
        lbl_font = QFont('Monospace', 7)
        p.setFont(lbl_font)
        for i in range(5):
            gy = PT + ch - int(i / 4 * ch)
            p.setPen(QPen(c_grid, 1, Qt.PenStyle.DotLine))
            p.drawLine(PL, gy, PL + cw, gy)
            p.setPen(c_text)
            lbl = f"{scale * i / 4:.0f}"
            p.drawText(0, gy - 6, PL - 4, 14, Qt.AlignmentFlag.AlignRight, lbl)

        # X labels (timestamps)
        if n >= 2:
            step = cw / (n - 1)
            for i, r in enumerate(pts):
                x = int(PL + i * step)
                p.setPen(c_text)
                p.drawText(x - 16, H - 4, 32, 14, Qt.AlignmentFlag.AlignCenter, r['ts'])

        def _line(key: str, line_col: QColor, fill_col: QColor) -> None:
            vals = [r[key] for r in pts]
            if n < 1:
                return
            xs = [PL + i * cw / max(n - 1, 1) for i in range(n)]
            ys = [PT + ch - v / scale * ch for v in vals]

            if n >= 2:
                area = QPainterPath()
                area.moveTo(xs[0], PT + ch)
                for x, y in zip(xs, ys):
                    area.lineTo(x, y)
                area.lineTo(xs[-1], PT + ch)
                area.closeSubpath()
                p.fillPath(area, QBrush(fill_col))

                p.setPen(QPen(line_col, 2))
                for i in range(n - 1):
                    p.drawLine(int(xs[i]), int(ys[i]), int(xs[i+1]), int(ys[i+1]))

            # Dots
            p.setBrush(QBrush(line_col))
            p.setPen(Qt.PenStyle.NoPen)
            for x, y in zip(xs, ys):
                p.drawEllipse(int(x) - 4, int(y) - 4, 8, 8)

        _line('dl', _BLUE_LINE, _BLUE_FILL)
        _line('ul', _ORA_LINE,  _ORA_FILL)

        # Legend
        p.setPen(Qt.PenStyle.NoPen)
        lx = PL + 8
        for col, label in ((_BLUE_LINE, tr("speed_legend_dl")),
                            (_ORA_LINE,  tr("speed_legend_ul"))):
            p.setBrush(QBrush(col))
            p.drawEllipse(lx, PT + 4, 8, 8)
            p.setPen(c_text)
            p.setFont(lbl_font)
            p.drawText(lx + 12, PT + 13, label)
            p.setPen(Qt.PenStyle.NoPen)
            lx += 60


def _load_history() -> list[dict]:
    try:
        if _HISTORY_FILE.exists():
            data = json.loads(_HISTORY_FILE.read_text(encoding='utf-8'))
            if isinstance(data, list):
                return data[-_PERSIST_MAX:]
    except Exception:
        pass
    return []


def _save_history(history: list[dict]) -> None:
    try:
        _HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        _HISTORY_FILE.write_text(
            json.dumps(list(history)[-_PERSIST_MAX:], ensure_ascii=False, indent=2),
            encoding='utf-8',
        )
    except Exception:
        pass


def _nice(v: float) -> float:
    """Round v up to a visually clean scale value."""
    if v <= 0:
        return 100
    import math
    magnitude = 10 ** math.floor(math.log10(v))
    for factor in (1, 2, 5, 10):
        candidate = factor * magnitude
        if candidate >= v:
            return candidate
    return v


# ── Page ──────────────────────────────────────────────────────────────────────

class SpeedTestPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._worker: SpeedTestWorker | None = None
        self._pending: dict = {}
        self._build_ui()
        self._restore_history()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Toolbar
        bar = QHBoxLayout()
        self._btn_start = QPushButton(tr("speed_start_btn"))
        self._btn_start.setFixedWidth(140)
        self._btn_start.setDefault(True)
        self._btn_start.clicked.connect(self._on_start)
        bar.addWidget(self._btn_start)

        self._btn_stop = QPushButton(tr("speed_stop_btn"))
        self._btn_stop.setFixedWidth(100)
        self._btn_stop.clicked.connect(self._on_stop)
        self._btn_stop.setEnabled(False)
        bar.addWidget(self._btn_stop)

        bar.addSpacing(12)
        self._lbl_status = QLabel("")
        bar.addWidget(self._lbl_status, 1)
        layout.addLayout(bar)

        # Progress bar (indeterminate while running)
        self._progress = QProgressBar()
        self._progress.setRange(0, 0)
        self._progress.setFixedHeight(4)
        self._progress.setTextVisible(False)
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        # Metric cards
        cards_row = QHBoxLayout()
        self._card_ping = _MetricCard(tr("speed_lbl_ping"), "ms")
        self._card_dl   = _MetricCard(tr("speed_lbl_dl"),   "Mbit/s")
        self._card_ul   = _MetricCard(tr("speed_lbl_ul"),   "Mbit/s")
        for card in (self._card_ping, self._card_dl, self._card_ul):
            cards_row.addWidget(card)
        layout.addLayout(cards_row)

        # Résumé du dernier test
        self._lbl_summary = QLabel("")
        self._lbl_summary.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font_sum = QFont()
        font_sum.setPointSize(10)
        self._lbl_summary.setFont(font_sum)
        self._lbl_summary.setVisible(False)
        layout.addWidget(self._lbl_summary)

        # Info serveur
        info = QLabel(tr("speed_server_info"))
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font_info = QFont()
        font_info.setPointSize(9)
        info.setFont(font_info)
        from PySide6.QtGui import QPalette as _P
        from PySide6.QtWidgets import QApplication
        pal = QApplication.palette()
        dim = pal.color(_P.ColorRole.PlaceholderText)
        info.setStyleSheet(f"color: {dim.name()};")
        layout.addWidget(info)

        # Graph
        self._graph = _SpeedGraph()

        if not _CMD_CURL:
            self._btn_start.setEnabled(False)
            self._btn_stop.setEnabled(False)
            banner = QLabel(tr("speed_err_no_cmd"))
            banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
            banner.setStyleSheet(
                "color: palette(mid); font-size: 13px; padding: 24px;"
            )
            banner.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            layout.addWidget(banner)
        else:
            get_cli_bar() and get_cli_bar().set_cmd(
                f'curl -o /dev/null -s -w "%{{speed_download}}" {_DL_URL}'
            )
            sep = QFrame()
            sep.setFrameShape(QFrame.Shape.HLine)
            sep.setFrameShadow(QFrame.Shadow.Sunken)
            layout.addWidget(sep)
            graph_lbl = QLabel(tr("speed_history_lbl"))
            graph_lbl.setStyleSheet("color: palette(mid); font-size: 10px;")
            layout.addWidget(graph_lbl)
            layout.addWidget(self._graph, 1)

    def _restore_history(self) -> None:
        for entry in _load_history():
            try:
                self._graph.push(entry['dl'], entry['ul'], entry['ping'])
            except (KeyError, TypeError):
                pass

    # ── Control ──────────────────────────────────────────────────────────────

    def _on_start(self) -> None:
        if not _CMD_CURL:
            return
        self._stop_worker()
        self._pending = {}
        self._card_ping.reset()
        self._card_dl.reset()
        self._card_ul.reset()

        self._worker = SpeedTestWorker()
        self._worker.phase_changed.connect(self._on_phase)
        self._worker.ping_done.connect(self._on_ping)
        self._worker.download_done.connect(self._on_dl)
        self._worker.upload_done.connect(self._on_ul)
        self._worker.error.connect(self._on_error)
        self._worker.finished.connect(self._on_finished)

        self._btn_start.setEnabled(False)
        self._btn_stop.setEnabled(True)
        self._progress.setVisible(True)
        self._worker.start()

    def _on_stop(self) -> None:
        self._stop_worker()
        self._lbl_status.setText(tr("speed_status_stop"))

    def _stop_worker(self) -> None:
        if self._worker:
            try:
                self._worker.phase_changed.disconnect()
                self._worker.ping_done.disconnect()
                self._worker.download_done.disconnect()
                self._worker.upload_done.disconnect()
                self._worker.error.disconnect()
                self._worker.finished.disconnect()
            except Exception:
                pass
            self._worker.stop()
            self._worker = None
        self._btn_start.setEnabled(bool(_CMD_CURL))
        self._btn_stop.setEnabled(False)
        self._progress.setVisible(False)
        for card in (self._card_ping, self._card_dl, self._card_ul):
            card.set_active(False)

    # ── Signals ──────────────────────────────────────────────────────────────

    _PHASE_LABELS = {
        'ping':     'speed_phase_ping',
        'download': 'speed_phase_dl',
        'upload':   'speed_phase_ul',
        'done':     '',
    }
    _PHASE_CARDS = {
        'ping':     '_card_ping',
        'download': '_card_dl',
        'upload':   '_card_ul',
    }

    def _on_phase(self, phase: str) -> None:
        for name in ('_card_ping', '_card_dl', '_card_ul'):
            getattr(self, name).set_active(False)
        if phase in self._PHASE_CARDS:
            getattr(self, self._PHASE_CARDS[phase]).set_active(True)
        key = self._PHASE_LABELS.get(phase, '')
        self._lbl_status.setText(tr(key) if key else "")
        self._lbl_summary.setVisible(False)

    def _on_ping(self, ms: float) -> None:
        self._pending['ping'] = ms
        color = color_ok() if ms < 30 else ('#f9e2af' if ms < 80 else '#fab387')
        self._card_ping.set_value(ms, color)

    def _on_dl(self, mbps: float) -> None:
        self._pending['dl'] = mbps
        self._card_dl.set_value(mbps, _BLUE_LINE.name())

    def _on_ul(self, mbps: float) -> None:
        self._pending['ul'] = mbps
        self._card_ul.set_value(mbps, _ORA_LINE.name())

    def _on_error(self, msg: str) -> None:
        self._lbl_status.setText(tr("common_error_prefix", msg=msg))
        self._lbl_summary.setVisible(False)

    def _on_finished(self) -> None:
        self._stop_worker()
        if {'dl', 'ul', 'ping'} <= self._pending.keys():
            entry = {
                'dl':   self._pending['dl'],
                'ul':   self._pending['ul'],
                'ping': self._pending.get('ping', 0.0),
                'ts':   datetime.now().strftime('%H:%M'),
                'date': datetime.now().strftime('%Y-%m-%d'),
            }
            self._graph.push(entry['dl'], entry['ul'], entry['ping'])
            saved = _load_history()
            saved.append(entry)
            _save_history(saved)
            summary = (
                f"↓ {entry['dl']:.1f} Mbit/s   "
                f"↑ {entry['ul']:.1f} Mbit/s   "
                f"ping {entry['ping']:.0f} ms   "
                f"— {entry['date']} {entry['ts']}"
            )
            self._lbl_status.setText("")
            self._lbl_summary.setText(summary)
            self._lbl_summary.setVisible(True)
