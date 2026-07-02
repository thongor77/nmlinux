from __future__ import annotations

import json
import platform
import re
import socket
import subprocess
import urllib.request
from concurrent.futures import ThreadPoolExecutor, wait as _wait
from ipaddress import IPv4Address, IPv4Network
from pathlib import Path

_IS_MACOS = platform.system() == 'Darwin'

from PySide6.QtGui import QBrush, QColor, QPainter, QPainterPath, QPen, QTransform
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QGroupBox, QFormLayout,
    QScrollArea, QSizePolicy,
)
from PySide6.QtCore import Qt, QPointF, QThread, Signal, QTimer

from nmlinux.core.i18n import tr
from nmlinux.core.theme import color_ok, color_err


_GEOJSON    = Path(__file__).parent.parent / "assets" / "world.geojson"
_MAP_ACCENT = QColor('#60a5fa')


# ── Geo map widget ────────────────────────────────────────────────────────────

class GeoMapWidget(QWidget):
    _ZOOM_FRAMES     = 40
    _RIPPLE_MAX      = 3
    _RIPPLE_PERIOD   = 20
    _RIPPLE_DURATION = 45

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(240)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._country_paths: list[QPainterPath] = []
        self._lat: float | None = None
        self._lon: float | None = None
        self._zoom      = 1.0
        self._cx        = 0.5
        self._cy        = 0.5
        self._target_zoom = 4.5
        self._target_cx   = 0.5
        self._target_cy   = 0.5
        self._step        = 0
        self._ripples: list[int] = []
        self._ripple_count = 0
        self._pulse      = 0.0
        self._pulse_dir  = 1.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
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
                        y = (90  - lat) / 180
                        if first:
                            path.moveTo(x, y)
                            first = False
                        else:
                            path.lineTo(x, y)
                    path.closeSubpath()
                    self._country_paths.append(path)

    def set_location(self, lat: float, lon: float) -> None:
        self._lat = lat
        self._lon = lon
        self._target_cx = (lon + 180) / 360
        self._target_cy = (90  - lat) / 180
        self._zoom = 1.0
        self._cx   = 0.5
        self._cy   = 0.5
        self._step = 0
        self._ripples = []
        self._ripple_count = 0
        self._pulse = 0.0
        self._pulse_dir = 1.0
        self._timer.start(33)

    def _tick(self) -> None:
        self._step += 1
        s = self._step

        if s <= self._ZOOM_FRAMES:
            t    = s / self._ZOOM_FRAMES
            ease = 1.0 - (1.0 - t) ** 3
            self._zoom = 1.0 + (self._target_zoom - 1.0) * ease
            self._cx   = 0.5  + (self._target_cx  - 0.5)  * ease
            self._cy   = 0.5  + (self._target_cy  - 0.5)  * ease
        else:
            rel = s - self._ZOOM_FRAMES
            if self._ripple_count < self._RIPPLE_MAX and rel % self._RIPPLE_PERIOD == 0:
                self._ripples.append(s)
                self._ripple_count += 1
            self._pulse += 0.06 * self._pulse_dir
            if self._pulse >= 1.0:
                self._pulse_dir = -1.0
            elif self._pulse <= 0.0:
                self._pulse_dir = 1.0
            if (self._ripple_count >= self._RIPPLE_MAX
                    and self._ripples
                    and (s - self._ripples[-1]) >= self._RIPPLE_DURATION):
                self._timer.stop()

        self.update()

    def _make_transform(self) -> QTransform:
        w, h = self.width(), self.height()
        t = QTransform()
        t.translate(w / 2, h / 2)
        t.scale(self._zoom * w, self._zoom * h)
        t.translate(-self._cx, -self._cy)
        return t

    def _world_to_screen(self, lat: float, lon: float) -> QPointF:
        wx = (lon + 180) / 360
        wy = (90  - lat) / 180
        return self._make_transform().map(QPointF(wx, wy))

    def paintEvent(self, _event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor('#1a2f4a'))

        t = self._make_transform()
        if self._country_paths:
            p.save()
            p.setTransform(t)
            p.setPen(QPen(QColor('#1e3d2a'), 0))
            p.setBrush(QBrush(QColor('#2d5a3d')))
            for path in self._country_paths:
                p.drawPath(path)
            p.restore()

        if self._lat is None:
            return

        pt = self._world_to_screen(self._lat, self._lon)

        # Ripple rings
        for born in self._ripples:
            age = self._step - born
            if age < 0 or age > self._RIPPLE_DURATION:
                continue
            progress = age / self._RIPPLE_DURATION
            radius   = int(10 + progress * 40)
            alpha    = int(180 * (1.0 - progress))
            c = QColor(_MAP_ACCENT)
            c.setAlpha(alpha)
            p.setPen(QPen(c, 1.5))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(pt, radius, radius)

        # Glow halo
        pulse_r = int(6 + self._pulse * 3)
        glow = QColor(_MAP_ACCENT)
        glow.setAlpha(50)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(glow))
        p.drawEllipse(pt, pulse_r + 5, pulse_r + 5)

        # Outer ring
        p.setPen(QPen(_MAP_ACCENT, 1.5))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(pt, pulse_r, pulse_r)

        # Centre dot
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor('#ffffff')))
        p.drawEllipse(pt, 3, 3)


# ── Data collectors (run in threads) ─────────────────────────────────────────

def _collect_local() -> dict:
    out: dict = {}

    try:
        out['hostname'] = socket.gethostname()
    except Exception:
        out['hostname'] = '—'

    # ── Default gateway + interface ───────────────────────────────────────────
    try:
        if _IS_MACOS:
            raw = subprocess.run(
                ['route', '-n', 'get', 'default'],
                capture_output=True, text=True, timeout=3,
            ).stdout
            m_gw = re.search(r'gateway:\s+(\S+)', raw)
            m_if = re.search(r'interface:\s+(\S+)', raw)
        else:
            raw = subprocess.run(
                ['ip', 'route', 'show', 'default'],
                capture_output=True, text=True, timeout=3,
            ).stdout
            m_gw = re.search(r'via (\S+)', raw)
            m_if = re.search(r'dev (\S+)', raw)
        out['gateway'] = m_gw.group(1) if m_gw else '—'
        out['iface']   = m_if.group(1) if m_if else ''
    except Exception:
        out['gateway'] = '—'
        out['iface']   = ''

    iface = out['iface']

    # ── IPv4 address + subnet mask ────────────────────────────────────────────
    try:
        if _IS_MACOS:
            cmd = ['ifconfig'] + ([iface] if iface else [])
            raw = subprocess.run(cmd, capture_output=True, text=True, timeout=3).stdout
            m = re.search(r'inet (\d+\.\d+\.\d+\.\d+) netmask (0x[0-9a-f]+)', raw)
            if m:
                out['local_ipv4']  = m.group(1)
                out['subnet_mask'] = str(IPv4Address(int(m.group(2), 16)))
            else:
                out['local_ipv4']  = '—'
                out['subnet_mask'] = '—'
        else:
            cmd = ['ip', '-4', 'addr', 'show'] + ([iface] if iface else [])
            raw = subprocess.run(cmd, capture_output=True, text=True, timeout=3).stdout
            m = re.search(r'inet (\d+\.\d+\.\d+\.\d+)/(\d+)', raw)
            out['local_ipv4']  = m.group(1) if m else '—'
            out['subnet_mask'] = str(IPv4Network(f'0.0.0.0/{m.group(2)}', strict=False).netmask) if m else '—'
    except Exception:
        out['local_ipv4']  = '—'
        out['subnet_mask'] = '—'

    # ── IPv6 address ──────────────────────────────────────────────────────────
    try:
        if _IS_MACOS:
            cmd = ['ifconfig'] + ([iface] if iface else [])
            raw = subprocess.run(cmd, capture_output=True, text=True, timeout=3).stdout
            addrs = re.findall(r'inet6 (\S+) prefixlen', raw)
            global_v6 = [a.split('%')[0] for a in addrs
                         if not a.lower().startswith('fe80') and a.split('%')[0] != '::1']
            out['local_ipv6'] = global_v6[0] if global_v6 else '—'
        else:
            cmd = ['ip', '-6', 'addr', 'show', 'scope', 'global'] + \
                  (['dev', iface] if iface else [])
            raw = subprocess.run(cmd, capture_output=True, text=True, timeout=3).stdout
            m = re.search(r'inet6 (\S+)/', raw)
            out['local_ipv6'] = m.group(1) if m else '—'
    except Exception:
        out['local_ipv6'] = '—'

    # ── DNS servers ───────────────────────────────────────────────────────────
    try:
        if _IS_MACOS:
            raw = subprocess.run(
                ['scutil', '--dns'],
                capture_output=True, text=True, timeout=3,
            ).stdout
            seen: set[str] = set()
            dns: list[str] = []
            for ip in re.findall(r'nameserver\[\d+\]\s*:\s*(\S+)', raw):
                if ip not in seen:
                    seen.add(ip)
                    dns.append(ip)
            out['dns_servers'] = dns[:3]
        else:
            with open('/etc/resolv.conf') as f:
                content = f.read()
            out['dns_servers'] = re.findall(r'^nameserver\s+(\S+)', content, re.MULTILINE)[:3]
    except Exception:
        out['dns_servers'] = []

    return out


def _collect_internet() -> dict:
    out: dict = {
        'public_ipv4':    '—',
        'public_ipv6_ok': False,
        'dns_ok':         False,
        'geo':            {},
    }

    try:
        fields = ('status,query,country,countryCode,regionName,city,'
                  'zip,lat,lon,timezone,isp,org,as,asname')
        req = urllib.request.Request(
            f'http://ip-api.com/json/?fields={fields}',
            headers={'User-Agent': 'NMLinux/1.0'},
        )
        with urllib.request.urlopen(req, timeout=6) as r:
            data = json.loads(r.read())
        if data.get('status') == 'success':
            out['public_ipv4'] = data.get('query', '—')
            out['geo'] = data
    except Exception:
        pass

    try:
        s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        s.settimeout(2)
        s.connect(('2001:4860:4860::8888', 53))
        s.close()
        out['public_ipv6_ok'] = True
    except Exception:
        pass

    try:
        socket.gethostbyname('www.google.com')
        out['dns_ok'] = True
    except Exception:
        pass

    return out


def _resolve(ip: str) -> str:
    try:
        return socket.gethostbyaddr(ip)[0]
    except Exception:
        return '—'


class DashboardWorker(QThread):
    ready = Signal(dict)

    def run(self) -> None:
        with ThreadPoolExecutor(max_workers=2) as pool:
            f_local    = pool.submit(_collect_local)
            f_internet = pool.submit(_collect_internet)
            _wait([f_local, f_internet])

        local    = f_local.result()
        internet = f_internet.result()

        gw = local.get('gateway', '—')
        local['gateway_hostname'] = _resolve(gw) if gw != '—' else '—'

        local['dns_details'] = [
            (ip, _resolve(ip)) for ip in local.get('dns_servers', [])
        ]

        self.ready.emit({**local, **internet})


# ── Gateway ping worker ───────────────────────────────────────────────────────

class _GatewayPingWorker(QThread):
    rtt_ready = Signal(float)   # ms, ou -1.0 si timeout

    def __init__(self, gateway: str) -> None:
        super().__init__()
        self._running = True   # instance attribute — not class attribute
        self._gateway = gateway

    def run(self) -> None:
        import time
        while self._running:
            try:
                proc = subprocess.run(
                    ['ping', '-c', '1', '-W', '1000' if _IS_MACOS else '1', self._gateway],
                    capture_output=True, text=True, timeout=3,
                )
                if proc.returncode == 0:
                    m = re.search(r'time=(\d+\.?\d*)', proc.stdout)
                    self.rtt_ready.emit(float(m.group(1)) if m else 0.0)
                else:
                    self.rtt_ready.emit(-1.0)
            except Exception:
                self.rtt_ready.emit(-1.0)
            time.sleep(2)

    def stop(self) -> None:
        self._running = False
        self.quit()


# ── Mini ping graph ───────────────────────────────────────────────────────────

class _MiniPingGraph(QWidget):
    _MAX = 60
    _H   = 60

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedHeight(self._H)
        self._data: list[float] = []   # ms, -1.0 = timeout

    def push(self, rtt: float) -> None:
        self._data.append(rtt)
        if len(self._data) > self._MAX:
            self._data.pop(0)
        self.update()

    def paintEvent(self, _event) -> None:  # noqa: N802
        if not self._data:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        valid = [v for v in self._data if v > 0]
        if not valid:
            return
        max_rtt = max(max(valid), 100.0)

        def _color(rtt: float) -> QColor:
            if rtt < 0:
                return QColor('#f38ba8')   # timeout rouge
            if rtt < 20:
                return QColor('#a6e3a1')   # vert
            if rtt < 100:
                return QColor('#fab387')   # orange
            return QColor('#f38ba8')       # rouge

        step = w / max(len(self._data), 1)
        pts  = []
        for i, rtt in enumerate(self._data):
            x = i * step + step / 2
            y = h - (max(rtt, 0) / max_rtt) * (h - 4) - 2 if rtt > 0 else h - 2
            pts.append((x, y, rtt))

        for x, y, rtt in pts:
            painter.setPen(QPen(_color(rtt), 2))
            painter.drawEllipse(QPointF(x, y), 2, 2)

        if len(pts) > 1:
            for i in range(len(pts) - 1):
                x1, y1, r1 = pts[i]
                x2, y2, r2 = pts[i + 1]
                if r1 > 0 and r2 > 0:
                    painter.setPen(QPen(_color(r1), 1))
                    painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))


# ── UI helpers ────────────────────────────────────────────────────────────────

_GREY  = 'palette(mid)'


def _card(title: str) -> tuple[QGroupBox, QFormLayout]:
    box  = QGroupBox(title)
    form = QFormLayout(box)
    form.setHorizontalSpacing(16)
    form.setVerticalSpacing(6)
    form.setContentsMargins(12, 12, 12, 12)
    form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    return box, form


def _val(text: str, ok: bool | None = None) -> QLabel:
    if ok is None:
        lbl = QLabel(text or '—')
    else:
        color  = color_ok() if ok else color_err()
        symbol = '✓' if ok else '✗'
        lbl = QLabel(f'<span style="color:{color}">{symbol}</span>  {text or "—"}')
        lbl.setTextFormat(Qt.TextFormat.RichText)
    lbl.setWordWrap(True)
    lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    return lbl


def _loading(form: QFormLayout) -> None:
    form.addRow(QLabel(tr("dash_loading")))


# ── Page ──────────────────────────────────────────────────────────────────────

class DashboardPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._worker: DashboardWorker | None = None
        self._ping_worker: _GatewayPingWorker | None = None
        self._build_ui()
        self._refresh()
        QTimer.singleShot(1000, self._start_gateway_ping)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(12)

        header = QHBoxLayout()
        title  = QLabel(tr("dash_title"))
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        self._btn_refresh = QPushButton(tr("common_refresh"))
        self._btn_refresh.setFixedWidth(100)
        self._btn_refresh.clicked.connect(self._refresh)
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(self._btn_refresh)
        root.addLayout(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(scroll.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        container = QWidget()
        vbox = QVBoxLayout(container)
        vbox.setSpacing(12)
        vbox.setContentsMargins(0, 0, 0, 0)

        self._box_pc,  self._form_pc  = _card(tr("dash_card_pc"))
        self._box_net, self._form_net = _card(tr("dash_card_net"))

        # Gateway card — manual layout so mini-graph survives form clears
        self._box_gw = QGroupBox(tr("dash_card_gw"))
        _gw_vbox = QVBoxLayout(self._box_gw)
        _gw_vbox.setContentsMargins(12, 12, 12, 12)
        _gw_vbox.setSpacing(6)
        _gw_form_w = QWidget()
        self._form_gw = QFormLayout(_gw_form_w)
        self._form_gw.setHorizontalSpacing(16)
        self._form_gw.setVerticalSpacing(6)
        self._form_gw.setContentsMargins(0, 0, 0, 0)
        _gw_vbox.addWidget(_gw_form_w)
        self._mini_graph = _MiniPingGraph()
        _lat_row = QHBoxLayout()
        _lat_row.setContentsMargins(0, 0, 0, 0)
        _lat_row.addWidget(QLabel("Latence :"))
        _lat_row.addWidget(self._mini_graph, 1)
        _gw_vbox.addLayout(_lat_row)
        top = QHBoxLayout()
        top.setSpacing(12)
        top.addWidget(self._box_pc,  1)
        top.addWidget(self._box_gw,  1)
        top.addWidget(self._box_net, 1)
        vbox.addLayout(top)

        self._box_geo, self._form_geo = _card(tr("dash_card_geo"))
        self._box_dns, self._form_dns = _card(tr("dash_card_dns"))
        bot = QHBoxLayout()
        bot.setSpacing(12)
        bot.addWidget(self._box_geo, 3)
        bot.addWidget(self._box_dns, 2)
        vbox.addLayout(bot, 1)

        # TLS Watchlist summary card
        self._box_tls, self._form_tls = _card("TLS Watchlist")
        self._lbl_tls = _val("—")
        self._form_tls.addRow("Statut :", self._lbl_tls)
        vbox.addWidget(self._box_tls)

        scroll.setWidget(container)
        root.addWidget(scroll, 1)

        for form in (self._form_pc, self._form_gw, self._form_net,
                     self._form_geo, self._form_dns):
            _loading(form)

    def _refresh(self) -> None:
        if self._worker and self._worker.isRunning():
            return
        self._btn_refresh.setEnabled(False)
        for form in (self._form_pc, self._form_gw, self._form_net,
                     self._form_geo, self._form_dns):
            self._clear_form(form)
            _loading(form)
        self._worker = DashboardWorker()
        self._worker.ready.connect(self._on_ready)
        self._worker.start()

    @staticmethod
    def _clear_form(form: QFormLayout) -> None:
        while form.rowCount():
            form.removeRow(0)

    def _on_ready(self, d: dict) -> None:
        self._btn_refresh.setEnabled(True)
        self._fill_pc(d)
        self._fill_gateway(d)
        self._fill_internet(d)
        self._fill_geo(d)
        self._fill_dns(d)

    def _fill_pc(self, d: dict) -> None:
        f = self._form_pc
        self._clear_form(f)
        ipv4 = d.get('local_ipv4', '—')
        mask = d.get('subnet_mask', '—')
        ipv6 = d.get('local_ipv6', '—')
        dns  = d.get('dns_servers', [])
        f.addRow(tr("dash_lbl_host") + " :", _val(d.get('hostname', '—')))
        f.addRow("IPv4 :", _val(ipv4, ok=ipv4 != '—'))
        f.addRow(tr("dash_lbl_mask") + " :", _val(mask, ok=mask != '—'))
        f.addRow("IPv6 :", _val(ipv6, ok=ipv6 != '—'))
        f.addRow("DNS  :", _val(', '.join(dns) if dns else '—', ok=bool(dns)))

    def _fill_gateway(self, d: dict) -> None:
        f = self._form_gw
        self._clear_form(f)
        gw   = d.get('gateway', '—')
        gw_h = d.get('gateway_hostname', '—')
        f.addRow("IPv4 :", _val(gw,   ok=gw != '—'))
        f.addRow("IPv6 :", _val('—',  ok=False))
        f.addRow("DNS  :", _val(gw_h, ok=gw_h != '—'))

    def _fill_internet(self, d: dict) -> None:
        f = self._form_net
        self._clear_form(f)
        ipv4    = d.get('public_ipv4', '—')
        ipv6_ok = d.get('public_ipv6_ok', False)
        dns_ok  = d.get('dns_ok', False)
        f.addRow("IPv4 :", _val(ipv4, ok=ipv4 != '—'))
        f.addRow("IPv6 :", _val(tr("dash_ipv6_ok") if ipv6_ok else tr("dash_ipv6_fail"), ok=ipv6_ok))
        f.addRow("DNS  :", _val(tr("dash_dns_ok")  if dns_ok  else tr("dash_dns_fail"),  ok=dns_ok))

    def _fill_geo(self, d: dict) -> None:
        f   = self._form_geo
        geo = d.get('geo', {})
        self._clear_form(f)

        if not geo:
            f.addRow(QLabel(tr("dash_geo_unavail")))
            return

        wrapper = QWidget()
        v_outer = QVBoxLayout(wrapper)
        v_outer.setContentsMargins(0, 0, 0, 0)
        v_outer.setSpacing(12)

        # Text columns (unchanged layout)
        text_w = QWidget()
        h_text = QHBoxLayout(text_w)
        h_text.setContentsMargins(0, 0, 0, 0)
        h_text.setSpacing(32)

        left  = QFormLayout()
        right = QFormLayout()
        for fl in (left, right):
            fl.setHorizontalSpacing(16)
            fl.setVerticalSpacing(6)

        def row(form, label_key, key, fallback='—'):
            v = str(geo.get(key, fallback)) or fallback
            lbl = QLabel(v)
            lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            form.addRow(tr(label_key) + " :", lbl)

        row(left,  "geo_country",  'country')
        row(left,  "geo_code",     'countryCode')
        row(left,  "geo_region",   'regionName')
        row(left,  "geo_city",     'city')
        row(left,  "geo_zip",      'zip')
        row(left,  "geo_lat",      'lat')
        row(left,  "geo_lon",      'lon')
        row(left,  "geo_timezone", 'timezone')
        row(right, "geo_isp",      'isp')
        row(right, "geo_org",      'org')
        row(right, "geo_as",       'as')
        row(right, "geo_asname",   'asname')

        h_text.addLayout(left)
        h_text.addLayout(right)
        h_text.addStretch(1)
        v_outer.addWidget(text_w)

        # Animated map — below the text
        lat = geo.get('lat')
        lon = geo.get('lon')
        if lat is not None and lon is not None:
            geo_map = GeoMapWidget()
            geo_map.set_location(float(lat), float(lon))
            v_outer.addWidget(geo_map)

        f.addRow(wrapper)

    def _fill_dns(self, d: dict) -> None:
        f       = self._form_dns
        details = d.get('dns_details', [])
        self._clear_form(f)
        if not details:
            f.addRow(QLabel(tr("dash_no_dns")))
            return
        for i, (ip, hostname) in enumerate(details, 1):
            ip_lbl = QLabel(ip)
            ip_lbl.setWordWrap(True)
            ip_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            f.addRow(f"#{i} :", ip_lbl)
            if hostname != '—':
                h = QLabel(hostname)
                h.setWordWrap(True)
                h.setStyleSheet(f"color: {_GREY};")
                h.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                f.addRow("", h)

    # ── Ping worker ───────────────────────────────────────────────────────────

    def _start_gateway_ping(self) -> None:
        try:
            if _IS_MACOS:
                raw = subprocess.run(
                    ['route', '-n', 'get', 'default'],
                    capture_output=True, text=True, timeout=3,
                )
                m = re.search(r'gateway:\s+(\S+)', raw.stdout)
            else:
                raw = subprocess.run(
                    ['ip', 'route', 'show', 'default'],
                    capture_output=True, text=True, timeout=3,
                )
                m = re.search(r'via\s+(\S+)', raw.stdout)
            gateway = m.group(1) if m else ''
        except Exception:
            gateway = ''
        if not gateway:
            return
        self._ping_worker = _GatewayPingWorker(gateway)
        self._ping_worker.rtt_ready.connect(self._mini_graph.push)
        self._ping_worker.start()

    def stop_ping_worker(self) -> None:
        if self._ping_worker and self._ping_worker.isRunning():
            self._ping_worker.stop()
            self._ping_worker.wait(1000)

    # ── TLS summary slot ──────────────────────────────────────────────────────

    def set_tls_summary(self, status: str) -> None:
        if status == 'red':
            self._lbl_tls.setText("⚠ Alerte")
            self._lbl_tls.setStyleSheet(f"color: {color_err()};")
        elif status == 'orange':
            self._lbl_tls.setText("Expiration proche")
            self._lbl_tls.setStyleSheet("color: orange;")
        else:
            self._lbl_tls.setText("OK")
            self._lbl_tls.setStyleSheet(f"color: {color_ok()};")
