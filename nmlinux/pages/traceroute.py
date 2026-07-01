"""Visual Traceroute — world map with geolocation of each hop."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from urllib.request import urlopen, Request

from PySide6.QtCore import Qt, QPoint, QPointF, QThread, Signal
from PySide6.QtGui import (
    QBrush, QColor, QFont, QPainter, QPainterPath, QPen, QTransform,
)
from PySide6.QtWidgets import (
    QFileDialog, QFrame, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QMessageBox, QPushButton, QSplitter, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

from nmlinux.core.cli_bar import get_cli_bar
from nmlinux.core.host_actions import HostActionMenu
from nmlinux.core.i18n import tr
from nmlinux.core.theme import color_ok, color_err

_GEOJSON = Path(__file__).parent.parent / "assets" / "world.geojson"

# Fixed semantic colours (work on both themes)
_YELLOW    = QColor('#f9e2af')
_ORANGE    = QColor('#fab387')
_BLUE      = QColor('#89b4fa')


def _rtt_color(rtt: float) -> QColor:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QPalette as _P
    overlay = QApplication.palette().color(_P.ColorRole.PlaceholderText)
    if rtt < 0:    return overlay
    if rtt < 20:   return QColor(color_ok())
    if rtt < 80:   return _YELLOW
    if rtt < 200:  return _ORANGE
    return QColor(color_err())


# ── Workers ──────────────────────────────────────────────────────────────────

import shutil as _shutil
_CMD_TRACEROUTE = _shutil.which('traceroute')
_CMD_TRACEPATH  = _shutil.which('tracepath')

# traceroute: " 3  hostname (1.2.3.4)  5.1 ms  6.2 ms"  or  " 3  1.2.3.4  5.1 ms"
_TR_HOP_RE  = re.compile(
    r'^\s*(\d+)\s+'
    r'(?:(\S+)\s+\(([^)]+)\)|(\S+))'
    r'((?:\s+[\d.]+\s+ms)*)'
)
_TR_RTT_RE  = re.compile(r'([\d.]+)\s+ms')
_TR_STAR_RE = re.compile(r'^\s*(\d+)\s+\*')

# tracepath -b: " 4:  hostname (1.2.3.4)                16.3ms"
#               " 2:  no reply"
_TP_HOP_RE  = re.compile(
    r'^\s*(\d+):\s+'
    r'(\S+)\s+\(([^)]+)\)'         # hostname (ip)
    r'.*?([\d.]+)ms'               # RTT (no space before ms)
)
_TP_STAR_RE = re.compile(r'^\s*(\d+):\s+no reply')


class TracerouteWorker(QThread):
    hop_found  = Signal(int, str, str, float)   # num, ip, hostname, avg_rtt
    star_found = Signal(int)
    error      = Signal(str)
    finished   = Signal()

    def __init__(self, target: str) -> None:
        super().__init__()
        self._target = target
        self._proc: subprocess.Popen | None = None

    def run(self) -> None:
        if _CMD_TRACEROUTE:
            self._run_traceroute()
        elif _CMD_TRACEPATH:
            self._run_tracepath()
        else:
            self.error.emit(tr("trace_err_no_cmd"))
            self.finished.emit()

    def _run_traceroute(self) -> None:
        try:
            self._proc = subprocess.Popen(
                [_CMD_TRACEROUTE, '-w', '2', '-q', '3', self._target],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            )
            seen: set[int] = set()
            for line in self._proc.stdout:
                m = _TR_HOP_RE.match(line)
                if m:
                    num = int(m.group(1))
                    if num in seen:
                        continue
                    seen.add(num)
                    hostname = m.group(2) or m.group(4)
                    ip       = m.group(3) or m.group(4)
                    rtts = [float(v) for v in _TR_RTT_RE.findall(m.group(5))]
                    avg  = sum(rtts) / len(rtts) if rtts else 0.0
                    self.hop_found.emit(num, ip, hostname, avg)
                    continue
                sm = _TR_STAR_RE.match(line)
                if sm:
                    num = int(sm.group(1))
                    if num not in seen:
                        seen.add(num)
                        self.star_found.emit(num)
            self._proc.wait()
        except Exception as exc:
            self.error.emit(str(exc))
        finally:
            self.finished.emit()

    def _run_tracepath(self) -> None:
        try:
            self._proc = subprocess.Popen(
                [_CMD_TRACEPATH, '-b', self._target],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            )
            seen: set[int] = set()
            for line in self._proc.stdout:
                m = _TP_HOP_RE.match(line)
                if m:
                    num = int(m.group(1))
                    if num in seen:
                        continue
                    seen.add(num)
                    hostname = m.group(2)
                    ip       = m.group(3)
                    rtt      = float(m.group(4))
                    self.hop_found.emit(num, ip, hostname, rtt)
                    continue
                sm = _TP_STAR_RE.match(line)
                if sm:
                    num = int(sm.group(1))
                    if num not in seen:
                        seen.add(num)
                        self.star_found.emit(num)
            self._proc.wait()
        except Exception as exc:
            self.error.emit(str(exc))
        finally:
            self.finished.emit()

    def stop(self) -> None:
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()
        self.wait(3000)


class GeolocWorker(QThread):
    result = Signal(list)

    def __init__(self, ips: list[str]) -> None:
        super().__init__()
        self._ips = ips

    def run(self) -> None:
        try:
            payload = json.dumps(
                [{"query": ip} for ip in self._ips]
            ).encode()
            req = Request(
                'http://ip-api.com/batch?fields=status,query,lat,lon,city,country',
                data=payload, method='POST',
                headers={'Content-Type': 'application/json'},
            )
            with urlopen(req, timeout=8) as r:
                self.result.emit(json.loads(r.read()))
        except Exception:
            self.result.emit([])


# ── World map widget ─────────────────────────────────────────────────────────

class _MapWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(280)
        self._country_paths: list[QPainterPath] = []
        self._hops: list[tuple[float, float, int, float]] = []
        # Zoom / pan state
        self._zoom:      float = 1.0
        self._cx:        float = 0.5    # world-x of viewport centre (0-1)
        self._cy:        float = 0.5    # world-y of viewport centre (0-1)
        self._auto_fit:  bool  = True   # False once user zooms/pans manually
        self._drag_origin: QPointF | None = None
        self._drag_cx0:    float = 0.5
        self._drag_cy0:    float = 0.5
        self.setMouseTracking(False)
        self._load_geo()

    def _load_geo(self) -> None:
        if not _GEOJSON.exists():
            return
        with open(_GEOJSON) as f:
            data = json.load(f)
        for feature in data['features']:
            geom = feature['geometry']
            polys = (
                [geom['coordinates']] if geom['type'] == 'Polygon'
                else geom['coordinates']
            )
            for poly in polys:
                for ring in poly:
                    path = QPainterPath()
                    first = True
                    for lon, lat in ring:
                        x = (lon + 180) / 360
                        y = (90 - lat) / 180
                        if first:
                            path.moveTo(x, y)
                            first = False
                        else:
                            path.lineTo(x, y)
                    path.closeSubpath()
                    self._country_paths.append(path)

    def set_hops(self, hops: list[tuple[float, float, int, float]]) -> None:
        self._hops = hops
        if not hops:
            self._auto_fit = True
        self.update()

    # ── Zoom / pan ───────────────────────────────────────────────────────────

    def _make_transform(self) -> QTransform:
        """World [0,1]² → screen pixels, honouring current zoom and centre."""
        w, h = self.width(), self.height()
        t = QTransform()
        t.translate(w / 2, h / 2)
        t.scale(self._zoom * w, self._zoom * h)
        t.translate(-self._cx, -self._cy)
        return t

    def _world_of(self, sx: float, sy: float) -> tuple[float, float]:
        inv, _ = self._make_transform().inverted()
        p = inv.map(QPointF(sx, sy))
        return p.x(), p.y()

    def _world_to_screen(self, lat: float, lon: float) -> QPointF:
        wx = (lon + 180) / 360
        wy = (90 - lat) / 180
        return self._make_transform().map(QPointF(wx, wy))

    def _zoom_at(self, sx: float, sy: float, factor: float) -> None:
        wx, wy = self._world_of(sx, sy)
        new_zoom = max(1.0, min(30.0, self._zoom * factor))
        w, h = self.width(), self.height()
        self._cx = wx - (sx - w / 2) / (new_zoom * w)
        self._cy = wy - (sy - h / 2) / (new_zoom * h)
        self._zoom = new_zoom
        self._clamp()
        self.update()

    def _clamp(self) -> None:
        hw = 1 / (2 * self._zoom)
        hh = 1 / (2 * self._zoom)
        self._cx = max(hw, min(1 - hw, self._cx))
        self._cy = max(hh, min(1 - hh, self._cy))

    def reset_view(self) -> None:
        self._zoom = 1.0
        self._cx = 0.5
        self._cy = 0.5
        self._auto_fit = True
        self.update()

    def fit_hops(self) -> None:
        """Auto-zoom to the bounding box of geolocated hops (unless user already panned)."""
        if not self._auto_fit or len(self._hops) < 2:
            return
        w, h = self.width(), self.height()
        if w <= 0 or h <= 0:
            return

        wxs = [(lon + 180) / 360 for _, lon, _, _ in self._hops]
        wys = [(90 - lat) / 180  for lat, _, _, _ in self._hops]
        min_wx, max_wx = min(wxs), max(wxs)
        min_wy, max_wy = min(wys), max(wys)
        bbox_w = max_wx - min_wx
        bbox_h = max_wy - min_wy

        PAD = 0.25
        zoom_x = (1 - PAD) / bbox_w if bbox_w > 1e-4 else 20.0
        zoom_y = (1 - PAD) / bbox_h if bbox_h > 1e-4 else 20.0
        self._zoom = max(1.0, min(20.0, min(zoom_x, zoom_y)))
        self._cx = (min_wx + max_wx) / 2
        self._cy = (min_wy + max_wy) / 2
        self._clamp()
        self.update()

    # ── Mouse events ─────────────────────────────────────────────────────────

    def wheelEvent(self, event) -> None:                    # noqa: N802
        self._auto_fit = False
        factor = 1.20 if event.angleDelta().y() > 0 else 1 / 1.20
        pos = event.position()
        self._zoom_at(pos.x(), pos.y(), factor)

    def mousePressEvent(self, event) -> None:               # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_origin = event.position()
            self._drag_cx0    = self._cx
            self._drag_cy0    = self._cy
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, event) -> None:                # noqa: N802
        if self._drag_origin is not None:
            self._auto_fit = False
            d = event.position() - self._drag_origin
            w, h = self.width(), self.height()
            self._cx = self._drag_cx0 - d.x() / (self._zoom * w)
            self._cy = self._drag_cy0 - d.y() / (self._zoom * h)
            self._clamp()
            self.update()

    def mouseReleaseEvent(self, event) -> None:             # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_origin = None
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def mouseDoubleClickEvent(self, event) -> None:         # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._auto_fit = False
            pos = event.position()
            self._zoom_at(pos.x(), pos.y(), 2.0)

    def contextMenuEvent(self, event) -> None:              # noqa: N802
        self.reset_view()

    # ── Rendering ────────────────────────────────────────────────────────────

    def changeEvent(self, event) -> None:  # noqa: N802
        super().changeEvent(event)

    def paintEvent(self, _event) -> None:                   # noqa: N802
        c_bg      = QColor('#1e3a5f')   # ocean
        c_country = QColor('#3d6b4f')   # land
        c_border  = QColor('#2a4d38')   # country borders
        c_overlay = QColor('#607d8b')   # hint text
        c_text    = QColor('#e0e8f0')   # hop labels

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        p.fillRect(self.rect(), c_bg)

        t = self._make_transform()

        # Countries (drawn in world coords via transform)
        if self._country_paths:
            border = QPen(c_border, 0)   # cosmetic hairline — 1 px at any zoom
            p.save()
            p.setTransform(t)
            p.setPen(border)
            p.setBrush(QBrush(c_country))
            for path in self._country_paths:
                p.drawPath(path)
            p.restore()

        # Hint when no hops yet
        if not self._hops:
            p.setPen(c_overlay)
            p.setFont(QFont('Sans', 10))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, tr("trace_map_hint"))
            return

        # Route lines (screen coords, so thickness is constant regardless of zoom)
        if len(self._hops) >= 2:
            p.setPen(QPen(_BLUE, 1.5, Qt.PenStyle.DashLine))
            for i in range(len(self._hops) - 1):
                a = self._world_to_screen(self._hops[i][0],     self._hops[i][1])
                b = self._world_to_screen(self._hops[i + 1][0], self._hops[i + 1][1])
                p.drawLine(a, b)

        # Hop dots + labels (screen coords — constant pixel size)
        p.setPen(Qt.PenStyle.NoPen)
        label_font = QFont('Monospace', 7)
        for i, (lat, lon, num, rtt) in enumerate(self._hops):
            pt = self._world_to_screen(lat, lon)
            radius = 7 if i in (0, len(self._hops) - 1) else 5
            p.setBrush(QBrush(_rtt_color(rtt).darker(160)))
            p.drawEllipse(pt, radius + 2, radius + 2)
            p.setBrush(QBrush(_rtt_color(rtt)))
            p.drawEllipse(pt, radius, radius)
            p.setPen(c_text)
            p.setFont(label_font)
            p.drawText(int(pt.x()) + radius + 2, int(pt.y()) + 4, str(num))
            p.setPen(Qt.PenStyle.NoPen)


# ── Page ─────────────────────────────────────────────────────────────────────

def _is_private(ip: str) -> bool:
    """Return True for RFC-1918 / loopback / link-local addresses."""
    return (
        ip.startswith('10.') or
        ip.startswith('127.') or
        ip.startswith('169.254.') or
        ip.startswith('192.168.') or
        (ip.startswith('172.') and
         16 <= int(ip.split('.')[1]) <= 31)
    )


class TraceroutePage(QWidget):
    action_requested = Signal(str, str, str)

    def __init__(self) -> None:
        super().__init__()
        self._hops: dict[int, dict] = {}
        self._worker: TracerouteWorker | None = None
        self._geo_workers: list[GeolocWorker] = []
        self._build_ui()

    # ── Layout ──────────────────────────────────────────────────────────────

    def set_target(self, host: str) -> None:
        self._input.setText(host)
        self._on_start()

    def _on_right_click(self, pos) -> None:
        row = self._table.rowAt(pos.y())
        if row < 0:
            return
        ip_item   = self._table.item(row, 1)
        host_item = self._table.item(row, 2)
        if not ip_item:
            return
        ip   = ip_item.text()
        host = host_item.text() if host_item else ''
        if ip in ('*', '—', ''):
            return
        menu = HostActionMenu(ip, host, parent=self)
        menu.action_chosen.connect(self.action_requested)
        menu.exec(self._table.viewport().mapToGlobal(pos))

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Toolbar
        bar = QHBoxLayout()
        bar.addWidget(QLabel(tr("trace_target_lbl")))
        self._input = QLineEdit()
        self._input.setPlaceholderText(tr("trace_target_ph"))
        self._input.returnPressed.connect(self._on_start)
        self._input.textChanged.connect(lambda t: get_cli_bar() and get_cli_bar().set_cmd(
            (f'traceroute {t.strip()}' if _CMD_TRACEROUTE else f'tracepath -b {t.strip()}') if t.strip() else ''
        ))
        self._btn_go   = QPushButton(tr("trace_start_btn"))
        self._btn_go.setDefault(True)
        self._btn_go.clicked.connect(self._on_start)
        self._btn_stop = QPushButton(tr("trace_stop_btn"))
        self._btn_stop.clicked.connect(self._on_stop)
        self._btn_stop.setEnabled(False)
        self._lbl_status = QLabel("")
        self._lbl_status.setStyleSheet("color: palette(mid);")
        self._btn_csv = QPushButton(tr("common_export_csv"))
        self._btn_csv.setVisible(False)
        self._btn_csv.clicked.connect(self._export_csv)
        self._btn_txt = QPushButton(tr("common_export_txt"))
        self._btn_txt.setVisible(False)
        self._btn_txt.clicked.connect(self._export_txt)
        bar.addWidget(self._input, 1)
        bar.addWidget(self._btn_go)
        bar.addWidget(self._btn_stop)
        bar.addWidget(self._lbl_status)
        bar.addSpacing(12)
        bar.addWidget(self._btn_csv)
        bar.addWidget(self._btn_txt)
        layout.addLayout(bar)

        # Legend
        legend = QHBoxLayout()
        legend.addStretch()
        for color_str, label in [
            (color_ok(),    "< 20 ms"),
            (_YELLOW.name(), "20-80 ms"),
            (_ORANGE.name(), "80-200 ms"),
            (color_err(),   "> 200 ms"),
            ("palette(mid)", tr("trace_legend_to")),
        ]:
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {color_str}; font-size: 10px;")
            legend.addWidget(dot)
            legend.addWidget(QLabel(label))
            legend.addSpacing(12)
        layout.addLayout(legend)

        # Splitter: map / table
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setChildrenCollapsible(False)

        self._map = _MapWidget()
        splitter.addWidget(self._map)

        self._table = QTableWidget(0, 5)
        self._table.setHorizontalHeaderLabels([
            tr("trace_col_hop"), tr("trace_col_ip"), tr("trace_col_host"),
            tr("trace_col_rtt"), tr("trace_col_loc"),
        ])
        hh = self._table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)
        self._table.setMaximumHeight(240)
        splitter.addWidget(self._table)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._on_right_click)
        splitter.setSizes([420, 200])

        layout.addWidget(splitter, 1)

    # ── Control ─────────────────────────────────────────────────────────────

    def _on_start(self) -> None:
        target = self._input.text().strip()
        if not target:
            return
        self._stop_all()
        self._hops.clear()
        self._table.setRowCount(0)
        self._map.set_hops([])

        self._btn_csv.setVisible(False)
        self._btn_txt.setVisible(False)
        self._worker = TracerouteWorker(target)
        self._worker.hop_found.connect(self._on_hop)
        self._worker.star_found.connect(self._on_star)
        self._worker.error.connect(self._on_error)
        self._worker.finished.connect(self._on_finished)
        self._btn_go.setEnabled(False)
        self._btn_stop.setEnabled(True)
        self._lbl_status.setText(tr("trace_status_run", target=target))
        self._worker.start()

    def _on_stop(self) -> None:
        self._stop_all()
        self._lbl_status.setText(tr("trace_status_stop"))

    def _stop_all(self) -> None:
        if self._worker:
            try:
                self._worker.hop_found.disconnect()
                self._worker.star_found.disconnect()
                self._worker.error.disconnect()
                self._worker.finished.disconnect()
            except Exception:
                pass
            self._worker.stop()
            self._worker = None
        for geo in self._geo_workers:
            try: geo.result.disconnect()
            except Exception: pass
        self._geo_workers.clear()
        self._btn_go.setEnabled(True)
        self._btn_stop.setEnabled(False)

    # ── Hop handling ─────────────────────────────────────────────────────────

    def _on_hop(self, num: int, ip: str, hostname: str, rtt: float) -> None:
        self._hops[num] = {
            'ip': ip, 'hostname': hostname, 'rtt': rtt,
            'lat': None, 'lon': None, 'location': '',
        }
        self._table_add(num, ip, hostname, rtt, '')
        # Geolocate immediately — skip private/loopback IPs
        if ip and ip != '*' and not _is_private(ip):
            self._geolocate(ip)

    def _on_star(self, num: int) -> None:
        self._hops[num] = {
            'ip': '*', 'hostname': '*', 'rtt': -1,
            'lat': None, 'lon': None, 'location': '',
        }
        self._table_add(num, '*', '—', -1, '')

    def _on_error(self, msg: str) -> None:
        self._lbl_status.setText(tr("common_error_prefix", msg=msg))

    def _on_finished(self) -> None:
        n = sum(1 for h in self._hops.values() if h['ip'] != '*')
        self._lbl_status.setText(tr("trace_status_done", total=len(self._hops), n=n))
        self._btn_go.setEnabled(True)
        self._btn_stop.setEnabled(False)
        self._worker = None
        has_rows = self._table.rowCount() > 0
        self._btn_csv.setVisible(has_rows)
        self._btn_txt.setVisible(has_rows)

    # ── Geolocation ──────────────────────────────────────────────────────────

    def _geolocate(self, ip: str) -> None:
        geo = GeolocWorker([ip])
        geo.result.connect(self._on_geo_result)
        self._geo_workers.append(geo)
        geo.start()

    def _on_geo_result(self, results: list) -> None:
        for r in results:
            if r.get('status') != 'success':
                continue
            ip  = r['query']
            lat, lon = r['lat'], r['lon']
            city    = r.get('city', '')
            country = r.get('country', '')
            loc = f"{city}, {country}" if city else country
            for num, hop in self._hops.items():
                if hop['ip'] == ip:
                    hop['lat'] = lat
                    hop['lon'] = lon
                    hop['location'] = loc
                    self._table_update_location(num, loc)
        self._refresh_map()

    # ── Map refresh ───────────────────────────────────────────────────────────

    def _refresh_map(self) -> None:
        pts = [
            (h['lat'], h['lon'], num, h['rtt'])
            for num, h in sorted(self._hops.items())
            if h['lat'] is not None
        ]
        self._map.set_hops(pts)
        self._map.fit_hops()

    # ── Table helpers ─────────────────────────────────────────────────────────

    def _table_add(self, num: int, ip: str, hostname: str,
                   rtt: float, location: str) -> None:
        row = self._table.rowCount()
        self._table.insertRow(row)
        rtt_str = f"{rtt:.1f} ms" if rtt >= 0 else "* * *"
        for col, val in enumerate([str(num), ip, hostname, rtt_str, location]):
            item = QTableWidgetItem(val)
            item.setData(Qt.ItemDataRole.UserRole, num)
            if col == 3 and rtt >= 0:
                item.setForeground(QBrush(_rtt_color(rtt)))
            elif col == 3:
                from PySide6.QtWidgets import QApplication
                from PySide6.QtGui import QPalette as _P
                item.setForeground(QBrush(QApplication.palette().color(_P.ColorRole.PlaceholderText)))
            self._table.setItem(row, col, item)

    def _table_update_location(self, num: int, location: str) -> None:
        for row in range(self._table.rowCount()):
            item = self._table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == num:
                self._table.item(row, 4).setText(location)
                return

    # ── Export ───────────────────────────────────────────────────────────────

    def _table_rows(self) -> list[tuple[str, ...]]:
        rows = []
        for r in range(self._table.rowCount()):
            rows.append(tuple(
                (self._table.item(r, c).text() if self._table.item(r, c) else '')
                for c in range(5)
            ))
        return rows

    def _export_csv(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, tr("common_export_csv"), "traceroute_result.csv",
            "CSV (*.csv);;All (*)",
        )
        if not path:
            return
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write("Hop,IP,Hostname,RTT,Location\n")
                for row in self._table_rows():
                    safe = [v.replace('"', '""') for v in row]
                    f.write(','.join(f'"{v}"' if ',' in v else v for v in safe) + '\n')
        except OSError as exc:
            QMessageBox.critical(self, "Error", str(exc))

    def _export_txt(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, tr("common_export_txt"), "traceroute_result.txt",
            "Text (*.txt);;All (*)",
        )
        if not path:
            return
        try:
            rows = self._table_rows()
            headers = [
                tr("trace_col_hop"), tr("trace_col_ip"), tr("trace_col_host"),
                tr("trace_col_rtt"), tr("trace_col_loc"),
            ]
            widths = [
                max(len(h), max((len(r[i]) for r in rows), default=0))
                for i, h in enumerate(headers)
            ]
            sep  = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
            hrow = "| " + " | ".join(f"{h:<{w}}" for h, w in zip(headers, widths)) + " |"
            target = self._input.text().strip()
            with open(path, 'w', encoding='utf-8') as f:
                if target:
                    f.write(f"Target: {target}\n{self._lbl_status.text()}\n\n")
                f.write(sep + "\n" + hrow + "\n" + sep + "\n")
                for row in rows:
                    f.write("| " + " | ".join(f"{v:<{w}}" for v, w in zip(row, widths)) + " |\n")
                f.write(sep + "\n")
        except OSError as exc:
            QMessageBox.critical(self, "Error", str(exc))
