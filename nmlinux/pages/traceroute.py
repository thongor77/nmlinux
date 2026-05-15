"""Visual Traceroute — world map with geolocation of each hop."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from urllib.request import urlopen, Request

from PySide6.QtCore import Qt, QThread, Signal, QPointF
from PySide6.QtGui import (
    QBrush, QColor, QFont, QPainter, QPainterPath, QPen,
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

# Matches:  " 3  hostname (1.2.3.4)  5.1 ms  6.2 ms  5.9 ms"
# Also:     " 3  1.2.3.4  5.1 ms  6.2 ms  5.9 ms"  (traceroute -n)
_HOP_RE = re.compile(
    r'^\s*(\d+)\s+'
    r'(?:(\S+)\s+\(([^)]+)\)|(\S+))'   # host (ip)  OR  ip-only
    r'((?:\s+[\d.]+\s+ms)*)'           # RTT fields
)
_RTT_RE = re.compile(r'([\d.]+)\s+ms')
_STAR_RE = re.compile(r'^\s*(\d+)\s+\*')


class TracerouteWorker(QThread):
    hop_found  = Signal(int, str, str, float)   # num, ip, hostname, avg_rtt
    star_found = Signal(int)
    finished   = Signal()

    def __init__(self, target: str) -> None:
        super().__init__()
        self._target = target
        self._proc: subprocess.Popen | None = None

    def run(self) -> None:
        try:
            self._proc = subprocess.Popen(
                ['traceroute', '-w', '2', '-q', '3', self._target],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True,
            )
            for line in self._proc.stdout:
                m = _HOP_RE.match(line)
                if m:
                    num = int(m.group(1))
                    if m.group(2):          # hostname (ip) form
                        hostname, ip = m.group(2), m.group(3)
                    else:                   # ip-only form
                        hostname = ip = m.group(4)
                    rtts = [float(v) for v in _RTT_RE.findall(m.group(5))]
                    avg = sum(rtts) / len(rtts) if rtts else 0.0
                    self.hop_found.emit(num, ip, hostname, avg)
                    continue
                sm = _STAR_RE.match(line)
                if sm:
                    self.star_found.emit(int(sm.group(1)))
            self._proc.wait()
        except Exception:
            pass
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

    def _to_px(self, lat: float, lon: float) -> QPointF:
        return QPointF(
            (lon + 180) / 360 * self.width(),
            (90 - lat)  / 180 * self.height(),
        )

    def paintEvent(self, _event) -> None:                  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        p.fillRect(self.rect(), _BG)

        # Countries
        if self._country_paths:
            p.save()
            p.scale(w, h)
            p.setPen(QPen(_SURFACE0, 0))
            p.setBrush(QBrush(_SURFACE1))
            for path in self._country_paths:
                p.drawPath(path)
            p.restore()

        if not self._hops:
            p.setPen(_OVERLAY0)
            p.setFont(QFont('Sans', 10))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                       "Lance un traceroute pour voir la route sur la carte")
            return

        # Route lines
        if len(self._hops) >= 2:
            pen = QPen(_BLUE, 1.5, Qt.PenStyle.DashLine)
            p.setPen(pen)
            for i in range(len(self._hops) - 1):
                a = self._to_px(self._hops[i][0], self._hops[i][1])
                b = self._to_px(self._hops[i + 1][0], self._hops[i + 1][1])
                p.drawLine(a, b)

        # Hop dots + labels
        p.setPen(Qt.PenStyle.NoPen)
        label_font = QFont('Monospace', 7)
        for i, (lat, lon, num, rtt) in enumerate(self._hops):
            pt = self._to_px(lat, lon)
            radius = 7 if i in (0, len(self._hops) - 1) else 5
            # Glow ring
            p.setBrush(QBrush(_rtt_color(rtt).darker(160)))
            p.drawEllipse(pt, radius + 2, radius + 2)
            # Fill
            p.setBrush(QBrush(_rtt_color(rtt)))
            p.drawEllipse(pt, radius, radius)
            # Number
            p.setPen(_TEXT)
            p.setFont(label_font)
            p.drawText(int(pt.x()) + radius + 2, int(pt.y()) + 4, str(num))
            p.setPen(Qt.PenStyle.NoPen)


# ── Page ─────────────────────────────────────────────────────────────────────

class TraceroutePage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._hops: dict[int, dict] = {}
        self._worker:  TracerouteWorker | None = None
        self._geoloc:  GeolocWorker    | None = None
        self._pending: dict[str, int]  = {}    # ip → hop_num (awaiting geoloc)
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
        self._pending.clear()
        self._table.setRowCount(0)
        self._map.set_hops([])

        self._worker = TracerouteWorker(target)
        self._worker.hop_found.connect(self._on_hop)
        self._worker.star_found.connect(self._on_star)
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
                self._worker.finished.disconnect()
            except Exception:
                pass
            self._worker.stop()
            self._worker = None
        if self._geoloc:
            try: self._geoloc.result.disconnect()
            except Exception: pass
            self._geoloc = None
        self._btn_go.setEnabled(True)
        self._btn_stop.setEnabled(False)

    # ── Hop handling ─────────────────────────────────────────────────────────

    def _on_hop(self, num: int, ip: str, hostname: str, rtt: float) -> None:
        self._hops[num] = {
            'ip': ip, 'hostname': hostname, 'rtt': rtt,
            'lat': None, 'lon': None, 'location': '',
        }
        self._table_add(num, ip, hostname, rtt, '')
        if ip and ip != '*':
            self._pending[ip] = num
        # Batch geolocate every 8 new IPs, or immediately on star
        if len(self._pending) >= 8:
            self._flush_geo()

    def _on_star(self, num: int) -> None:
        self._hops[num] = {
            'ip': '*', 'hostname': '*', 'rtt': -1,
            'lat': None, 'lon': None, 'location': '',
        }
        self._table_add(num, '*', '—', -1, '')

    def _on_finished(self) -> None:
        self._flush_geo()
        n = sum(1 for h in self._hops.values() if h['ip'] != '*')
        self._lbl_status.setText(f"Terminé — {len(self._hops)} hops ({n} répondants)")
        self._btn_go.setEnabled(True)
        self._btn_stop.setEnabled(False)
        self._worker = None

    # ── Geolocation ──────────────────────────────────────────────────────────

    def _flush_geo(self) -> None:
        ips = list(self._pending)
        self._pending.clear()
        if not ips:
            return
        geo = GeolocWorker(ips)
        geo.result.connect(self._on_geo_result)
        self._geoloc = geo
        geo.start()

    def _on_geo_result(self, results: list) -> None:
        for r in results:
            if r.get('status') != 'success':
                continue
            ip = r['query']
            lat, lon = r['lat'], r['lon']
            city    = r.get('city', '')
            country = r.get('country', '')
            loc = f"{city}, {country}" if city else country
            for hop in self._hops.values():
                if hop['ip'] == ip:
                    hop['lat'] = lat
                    hop['lon'] = lon
                    hop['location'] = loc
            for num, hop in self._hops.items():
                if hop['ip'] == ip:
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
