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
    QFrame, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QPushButton, QSplitter, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

_GEOJSON = Path(__file__).parent.parent / "assets" / "world.geojson"

# Catppuccin Mocha colours
_BG        = QColor('#1e1e2e')
_SURFACE0  = QColor('#313244')
_SURFACE1  = QColor('#45475a')
_OVERLAY0  = QColor('#6c7086')
_TEXT      = QColor('#cdd6f4')
_GREEN     = QColor('#a6e3a1')
_YELLOW    = QColor('#f9e2af')
_ORANGE    = QColor('#fab387')
_RED       = QColor('#f38ba8')
_BLUE      = QColor('#89b4fa')


def _rtt_color(rtt: float) -> QColor:
    if rtt < 0:    return _OVERLAY0
    if rtt < 20:   return _GREEN
    if rtt < 80:   return _YELLOW
    if rtt < 200:  return _ORANGE
    return _RED


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
            self.error.emit("traceroute et tracepath sont introuvables.\n"
                            "Installe l'un des deux : sudo pacman -S traceroute")
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
        self._zoom: float = 1.0
        self._cx:   float = 0.5    # world-x of viewport centre (0-1)
        self._cy:   float = 0.5    # world-y of viewport centre (0-1)
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
        self.update()

    # ── Mouse events ─────────────────────────────────────────────────────────

    def wheelEvent(self, event) -> None:                    # noqa: N802
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
            pos = event.position()
            self._zoom_at(pos.x(), pos.y(), 2.0)

    def contextMenuEvent(self, event) -> None:              # noqa: N802
        self.reset_view()

    # ── Rendering ────────────────────────────────────────────────────────────

    def paintEvent(self, _event) -> None:                   # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        p.fillRect(self.rect(), _BG)

        t = self._make_transform()

        # Countries (drawn in world coords via transform)
        if self._country_paths:
            border = QPen(_SURFACE0, 0)   # cosmetic hairline — 1 px at any zoom
            p.save()
            p.setTransform(t)
            p.setPen(border)
            p.setBrush(QBrush(_SURFACE1))
            for path in self._country_paths:
                p.drawPath(path)
            p.restore()

        # Hint when no hops yet
        if not self._hops:
            p.setPen(_OVERLAY0)
            p.setFont(QFont('Sans', 10))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                       "Lance un traceroute pour voir la route sur la carte\n"
                       "Molette = zoom · Glisser = déplacer · Dbl-clic = zoom ×2 · Clic droit = réinitialiser")
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
            p.setPen(_TEXT)
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
    def __init__(self) -> None:
        super().__init__()
        self._hops: dict[int, dict] = {}
        self._worker: TracerouteWorker | None = None
        self._geo_workers: list[GeolocWorker] = []
        self._build_ui()

    # ── Layout ──────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Toolbar
        bar = QHBoxLayout()
        bar.addWidget(QLabel("Cible :"))
        self._input = QLineEdit()
        self._input.setPlaceholderText("8.8.8.8  ou  example.com")
        self._input.returnPressed.connect(self._on_start)
        self._btn_go   = QPushButton("▶  Démarrer")
        self._btn_go.setDefault(True)
        self._btn_go.clicked.connect(self._on_start)
        self._btn_stop = QPushButton("■  Arrêter")
        self._btn_stop.clicked.connect(self._on_stop)
        self._btn_stop.setEnabled(False)
        self._lbl_status = QLabel("")
        self._lbl_status.setStyleSheet("color: palette(mid);")
        bar.addWidget(self._input, 1)
        bar.addWidget(self._btn_go)
        bar.addWidget(self._btn_stop)
        bar.addWidget(self._lbl_status)
        layout.addLayout(bar)

        # Legend
        legend = QHBoxLayout()
        legend.addStretch()
        for color, label in [(_GREEN, "< 20 ms"), (_YELLOW, "20-80 ms"),
                              (_ORANGE, "80-200 ms"), (_RED, "> 200 ms"),
                              (_OVERLAY0, "timeout")]:
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {color.name()}; font-size: 10px;")
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
        self._table.setHorizontalHeaderLabels(
            ["Hop", "Adresse IP", "Hôte", "RTT moy.", "Localisation"]
        )
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

        self._worker = TracerouteWorker(target)
        self._worker.hop_found.connect(self._on_hop)
        self._worker.star_found.connect(self._on_star)
        self._worker.error.connect(self._on_error)
        self._worker.finished.connect(self._on_finished)
        self._btn_go.setEnabled(False)
        self._btn_stop.setEnabled(True)
        self._lbl_status.setText(f"Traceroute vers {target}…")
        self._worker.start()

    def _on_stop(self) -> None:
        self._stop_all()
        self._lbl_status.setText("Arrêté.")

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
        self._lbl_status.setText(f"Erreur : {msg}")

    def _on_finished(self) -> None:
        n = sum(1 for h in self._hops.values() if h['ip'] != '*')
        self._lbl_status.setText(f"Terminé — {len(self._hops)} hops ({n} répondants)")
        self._btn_go.setEnabled(True)
        self._btn_stop.setEnabled(False)
        self._worker = None

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
                item.setForeground(QBrush(_OVERLAY0))
            self._table.setItem(row, col, item)

    def _table_update_location(self, num: int, location: str) -> None:
        for row in range(self._table.rowCount()):
            item = self._table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == num:
                self._table.item(row, 4).setText(location)
                return
