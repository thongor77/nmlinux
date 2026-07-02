"""Network Topology Map — visual LAN discovery via nmap -sn."""
from __future__ import annotations

import json
import math
import platform
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from functools import lru_cache
from ipaddress import IPv4Network
from pathlib import Path

_IS_MACOS = platform.system() == 'Darwin'
_mono = 'Menlo' if _IS_MACOS else 'Monospace'

from PySide6.QtCore import Qt, QLineF, QPointF, QRectF, QThread, Signal
from PySide6.QtGui import (
    QBrush, QColor, QFont, QPainter, QPen, QPalette,
)
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QApplication, QFormLayout, QGraphicsItem, QGraphicsLineItem,
    QGraphicsScene, QGraphicsView, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QSplitter, QVBoxLayout, QWidget,
)

from nmlinux.core.cli_bar import get_cli_bar
from nmlinux.core.host_actions import HostActionMenu
from nmlinux.core.i18n import tr
from nmlinux.core.theme import color_err

_CMD_NMAP  = shutil.which('nmap')
_CMD_AVAHI = shutil.which('avahi-browse')

# Semantic node colours — balanced for both light and dark themes
_C_GATEWAY = QColor('#e8954f')   # amber  — router / gateway
_C_SELF    = QColor('#5b8fda')   # blue   — this machine
_C_HOST    = QColor('#4aaa6e')   # green  — other hosts


def _node_color(node_type: str) -> QColor:
    return {'gateway': _C_GATEWAY, 'self': _C_SELF}.get(node_type, _C_HOST)


# ── SVG icon rendering ────────────────────────────────────────────────────────

_ICONS_DIR = Path(__file__).parent.parent / "assets" / "icons"

_DEV_ICON: dict[str, str] = {
    'router':   'wifi',
    'self':     'monitor',
    'computer': 'laptop',
    'printer':  'printer',
    'nas':      'server',
    'phone':    'smartphone',
    'switch':   'network',
    'rpi':      'cpu',
}


@lru_cache(maxsize=32)
def _svg_renderer(dev_class: str, color_hex: str) -> QSvgRenderer | None:
    svg_name = _DEV_ICON.get(dev_class, 'laptop')
    path = _ICONS_DIR / f"{svg_name}.svg"
    if not path.exists():
        return None
    svg = path.read_text(encoding='utf-8')
    svg = re.sub(r'stroke="currentColor"', f'stroke="{color_hex}"', svg)
    svg = re.sub(r'stroke="#[0-9a-fA-F]+"', f'stroke="{color_hex}"', svg)
    return QSvgRenderer(svg.encode())


# ── Device-class detection (vendor heuristics) ────────────────────────────────

_PRINTER_KW = ('canon', 'epson', 'brother', 'ricoh', 'xerox', 'kyocera',
               'konica', 'lexmark', 'pantum', 'oki data', 'toshiba tec')
_NAS_KW     = ('synology', 'qnap', 'western digital', 'wd technolog',
               'seagate', 'buffalo', 'drobo')
_PHONE_KW   = ('apple', 'samsung electronics', 'xiaomi', 'huawei',
               'oneplus', 'oppo', 'realme', 'vivo mobile',
               'motorola', 'nokia', 'honor device')
_RPI_KW     = ('raspberry pi',)
_SWITCH_KW  = ('cisco', 'ubiquiti', 'mikrotik', 'juniper', 'aruba',
               'ruckus', 'extreme networks', 'tp-link', 'tp link',
               'd-link', 'zyxel', 'fritz!', 'linksys', 'netgear', 'asus')


_HOSTNAME_NAS     = ('diskstation', 'qnap', 'nas', 'readynas', 'freenas', 'truenas',
                     'synology', 'buffalo', 'drobo')
_HOSTNAME_PHONE   = ('android', 'iphone', 'ipad', 'galaxy', 'pixel', 'oneplus',
                     'huawei', 'xiaomi', 'redmi', 'honor')
_HOSTNAME_PRINTER = ('print', 'printer', 'canon', 'epson', 'brother', 'hp-', 'hprt')
_HOSTNAME_RPI     = ('raspberry', 'raspberrypi', 'rpi')
_HOSTNAME_SWITCH  = ('repeater', 'repeta', 'repete', 'extender', 'ap-', 'wap-',
                     'switch', 'ubnt', 'unifi', 'mikrotik', 'router')


def _detect_device_class(data: dict) -> str:
    """Infer device class from node type, MAC vendor, then hostname."""
    if data['type'] == 'self':
        return 'self'
    if data['type'] == 'gateway':
        return 'router'

    v = (data.get('vendor') or '').lower()
    for kw in _RPI_KW:
        if kw in v:
            return 'rpi'
    for kw in _NAS_KW:
        if kw in v:
            return 'nas'
    for kw in _PRINTER_KW:
        if kw in v:
            return 'printer'
    for kw in _PHONE_KW:
        if kw in v:
            return 'phone'
    for kw in _SWITCH_KW:
        if kw in v:
            return 'switch'

    # Fallback: hostname heuristics (vendor may be NIC manufacturer, not device brand)
    h = (data.get('hostname') or '').lower()
    for kw in _HOSTNAME_RPI:
        if kw in h:
            return 'rpi'
    for kw in _HOSTNAME_NAS:
        if kw in h:
            return 'nas'
    for kw in _HOSTNAME_PRINTER:
        if kw in h:
            return 'printer'
    for kw in _HOSTNAME_PHONE:
        if kw in h:
            return 'phone'
    for kw in _HOSTNAME_SWITCH:
        if kw in h:
            return 'switch'

    return 'computer'


def _place_on_ring(nodes: list, R: float) -> None:
    n = len(nodes)
    for i, node in enumerate(nodes):
        angle = 2 * math.pi * i / n - math.pi / 2
        node.setPos(R * math.cos(angle), R * math.sin(angle))


# ── Network helpers ───────────────────────────────────────────────────────────

def _local_network() -> tuple[str, str, str]:
    """Return (cidr, gateway_ip, self_ip) for the default route interface."""
    gateway = self_ip = cidr = ''
    iface = ''

    if _IS_MACOS:
        try:
            raw = subprocess.run(
                ['route', '-n', 'get', 'default'],
                capture_output=True, text=True, timeout=2,
            ).stdout
            m_gw = re.search(r'gateway:\s+(\S+)', raw)
            m_if = re.search(r'interface:\s+(\S+)', raw)
            gateway = m_gw.group(1) if m_gw else ''
            iface   = m_if.group(1) if m_if else ''
        except Exception:
            pass

        if iface:
            try:
                raw = subprocess.run(
                    ['ifconfig', iface],
                    capture_output=True, text=True, timeout=2,
                ).stdout
                m = re.search(r'inet (\d+\.\d+\.\d+\.\d+) netmask (0x[0-9a-f]+)', raw)
                if m:
                    self_ip = m.group(1)
                    prefix  = bin(int(m.group(2), 16)).count('1')
                    cidr    = str(IPv4Network(f'{self_ip}/{prefix}', strict=False))
            except Exception:
                pass
    else:
        try:
            route = subprocess.run(
                ['ip', 'route', 'show', 'default'],
                capture_output=True, text=True, timeout=2,
            ).stdout
            m_gw = re.search(r'via (\S+)', route)
            m_if = re.search(r'dev (\S+)', route)
            gateway = m_gw.group(1) if m_gw else ''
            iface   = m_if.group(1) if m_if else ''
        except Exception:
            pass

        try:
            cmd = (['ip', '-j', 'addr', 'show', iface] if iface
                   else ['ip', '-j', 'addr', 'show'])
            data = json.loads(
                subprocess.run(cmd, capture_output=True, text=True, timeout=2).stdout
            )
            for entry in data:
                if entry.get('ifname') == 'lo':
                    continue
                for addr in entry.get('addr_info', []):
                    if addr.get('family') == 'inet':
                        self_ip = addr['local']
                        prefix  = addr['prefixlen']
                        cidr    = str(IPv4Network(f'{self_ip}/{prefix}', strict=False))
                        break
                if cidr:
                    break
        except Exception:
            pass

    return cidr, gateway, self_ip


# ── Graphics items ────────────────────────────────────────────────────────────

class _EdgeItem(QGraphicsLineItem):
    """Dashed line between two nodes; updates when either node is moved."""

    def __init__(self, src: '_NodeItem', dst: '_NodeItem') -> None:
        super().__init__()
        self._src = src
        self._dst = dst
        src._edges.append(self)
        dst._edges.append(self)
        self.setPen(QPen(QColor(128, 128, 128, 110), 1.5, Qt.PenStyle.DashLine))
        self.setZValue(-1)
        self.sync()

    def boundingRect(self) -> QRectF:
        return super().boundingRect().adjusted(-4, -4, 4, 4)

    def sync(self) -> None:
        self.prepareGeometryChange()
        self.setLine(QLineF(self._src.pos(), self._dst.pos()))


class _NodeItem(QGraphicsItem):
    """Draggable SVG icon node with IP / hostname label."""
    _R    = 18   # half-size for regular hosts
    _R_GW = 24   # half-size for gateway

    def __init__(self, data: dict) -> None:
        super().__init__()
        self.data   = data
        self._color     = _node_color(data['type'])
        self._dev_class = data.get('device_class', 'computer')
        self._edges: list[_EdgeItem] = []
        self._r     = float(self._R_GW if data['type'] == 'gateway' else self._R)
        self._highlight = False
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setToolTip(self._build_tooltip())

    def boundingRect(self) -> QRectF:
        r = self._r + 6
        return QRectF(-r, -r, r * 2, r * 2 + 34)

    def paint(self, painter: QPainter, _option, _widget) -> None:
        r   = self._r
        col = self._color
        pal = QApplication.palette()

        # Origin highlight — node that triggered navigation from another module
        if self._highlight:
            painter.setPen(QPen(QColor('#f38ba8'), 3))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QPointF(0, 0), r + 7, r + 7)

        # Selection highlight
        if self.isSelected():
            painter.setPen(QPen(col.lighter(160), 2.5, Qt.PenStyle.DotLine))
            painter.setBrush(QBrush(QColor(col.red(), col.green(), col.blue(), 40)))
            painter.drawRoundedRect(QRectF(-r - 4, -r - 4, r * 2 + 8, r * 2 + 8), 6, 6)
            painter.setBrush(Qt.BrushStyle.NoBrush)

        # SVG icon
        renderer = _svg_renderer(self._dev_class, col.name())
        if renderer and renderer.isValid():
            renderer.render(painter, QRectF(-r, -r, r * 2, r * 2))
        else:
            # Fallback: plain circle
            painter.setPen(QPen(col.darker(160), 2))
            painter.setBrush(QBrush(col))
            painter.drawEllipse(QPointF(0, 0), r, r)

        # Primary label: hostname or IP
        hostname = self.data.get('hostname', '')
        ip       = self.data['ip']
        primary  = hostname if (hostname and hostname != ip) else ip
        if len(primary) > 22:
            primary = primary[:20] + '…'

        c_text = pal.color(QPalette.ColorRole.Text)
        painter.setPen(c_text)
        painter.setFont(QFont(_mono, 7))
        painter.drawText(QRectF(-55, r + 5, 110, 14),
                         Qt.AlignmentFlag.AlignCenter, primary)

        # Secondary label: IP (only if hostname was shown)
        if hostname and hostname != ip:
            c_sub = pal.color(QPalette.ColorRole.PlaceholderText)
            painter.setPen(c_sub)
            painter.setFont(QFont(_mono, 6))
            painter.drawText(QRectF(-55, r + 19, 110, 12),
                             Qt.AlignmentFlag.AlignCenter, ip)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            for edge in self._edges:
                edge.sync()
        return super().itemChange(change, value)

    def _build_tooltip(self) -> str:
        parts: list[str] = []
        hostname = self.data.get('hostname', '')
        ip       = self.data['ip']
        if hostname and hostname != ip:
            parts.append(hostname)
        parts.append(ip)
        mac = self.data.get('mac', '')
        if mac and mac != '—':
            parts.append(f'MAC: {mac}')
        vendor = self.data.get('vendor', '')
        if vendor:
            parts.append(f'({vendor})')
        return '\n'.join(parts)

    def contextMenuEvent(self, event) -> None:  # noqa: N802
        ports = self.data.get('ports', [])
        ip    = self.data.get('ip', '')
        host  = self.data.get('hostname', '')
        # Remonter à TopologyPage via la scène
        scene = self.scene()
        if scene:
            views = scene.views()
            if views:
                page = views[0].property('topology_page')
                if page is not None:
                    page._show_node_menu(ip, host, ports, event.screenPos())
        event.accept()


# ── Custom view (zoom + pan + selection signal) ───────────────────────────────

class _TopoView(QGraphicsView):
    node_selected = Signal(object)   # dict | None

    def __init__(self, scene: QGraphicsScene) -> None:
        super().__init__(scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setViewportUpdateMode(
            QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self._panning   = False
        self._pan_start = QPointF()
        scene.selectionChanged.connect(self._on_sel)

    def _on_sel(self) -> None:
        items = [i for i in self.scene().selectedItems() if isinstance(i, _NodeItem)]
        self.node_selected.emit(items[0].data if items else None)

    def fit_all(self) -> None:
        r = self.scene().itemsBoundingRect().adjusted(-50, -50, 50, 50)
        if not r.isNull():
            self.fitInView(r, Qt.AspectRatioMode.KeepAspectRatio)

    def wheelEvent(self, event) -> None:
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)

    def mousePressEvent(self, event) -> None:
        if (event.button() == Qt.MouseButton.LeftButton
                and self.itemAt(event.pos()) is None):
            self._panning   = True
            self._pan_start = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._panning:
            d = event.pos() - self._pan_start
            self._pan_start = event.pos()
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - int(d.x()))
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - int(d.y()))
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if self._panning:
            self._panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)


# ── Discovery worker ──────────────────────────────────────────────────────────

class _TopoWorker(QThread):
    node_found = Signal(dict)
    done       = Signal(int)
    error      = Signal(str)

    def __init__(self, cidr: str, gateway: str, self_ip: str) -> None:
        super().__init__()
        self._cidr    = cidr
        self._gateway = gateway
        self._self_ip = self_ip
        self._proc: subprocess.Popen | None = None

    def run(self) -> None:
        if not _CMD_NMAP:
            self.error.emit(tr('topo_err_no_nmap'))
            self.done.emit(0)
            return
        try:
            self._proc = subprocess.Popen(
                [_CMD_NMAP, '-sn', '-oX', '-', self._cidr],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            )
            stdout, _ = self._proc.communicate(timeout=120)
        except subprocess.TimeoutExpired:
            if self._proc:
                self._proc.kill()
            self.error.emit(tr('nmap_err_timeout'))
            self.done.emit(0)
            return
        except Exception as exc:
            self.error.emit(str(exc))
            self.done.emit(0)
            return

        try:
            root = ET.fromstring(stdout)
        except ET.ParseError as exc:
            self.error.emit(tr('nmap_err_xml', exc=exc))
            self.done.emit(0)
            return

        count = 0
        for host in root.findall('host'):
            status = host.find('status')
            if status is None or status.get('state') != 'up':
                continue

            addr_el = (host.find("address[@addrtype='ipv4']")
                       or host.find('address'))
            ip = addr_el.get('addr', '') if addr_el is not None else ''
            if not ip:
                continue

            mac_el = host.find("address[@addrtype='mac']")
            mac    = mac_el.get('addr', '—') if mac_el is not None else '—'
            vendor = mac_el.get('vendor', '') if mac_el is not None else ''

            hostname_el = host.find('.//hostname')
            hostname    = hostname_el.get('name', '') if hostname_el is not None else ''

            node_type = ('gateway' if ip == self._gateway
                         else 'self' if ip == self._self_ip
                         else 'host')

            self.node_found.emit({
                'ip': ip, 'mac': mac, 'vendor': vendor,
                'hostname': hostname, 'type': node_type,
            })
            count += 1

        self.done.emit(count)

    def stop(self) -> None:
        if self._proc and self._proc.poll() is None:
            self._proc.kill()
        self.wait(3000)


# ── mDNS detection ───────────────────────────────────────────────────────────

_MDNS_CLASS: dict[str, str] = {
    # Standard _type._proto
    '_ipp._tcp':              'printer',
    '_printer._tcp':          'printer',
    '_pdl-datastream._tcp':   'printer',
    '_scanner._tcp':          'printer',
    '_uscan._tcp':            'printer',
    '_uscans._tcp':           'printer',
    '_apple-mobdev2._tcp':    'phone',
    '_googlecast._tcp':       'phone',
    '_androidtvremote2._tcp':  'phone',
    '_nv_shield_remote._tcp':  'phone',
    '_companion-link._tcp':    'computer',
    '_kdeconnect._udp':       'computer',
    '_kdeconnect_phone':      'phone',
    '_workstation._tcp':      'computer',
    '_rfb._tcp':              'computer',
    '_smb._tcp':              'computer',
    '_afpovertcp._tcp':       'nas',
    '_nfs._tcp':              'nas',
    # Human-readable names avahi-browse substitutes for some types
    'AirTunes Remote Audio':  'computer',
    'AirPlay Remote Video':   'computer',
    'PDL Printer':            'printer',
    'Internet Printer':       'printer',
    'Microsoft Windows Network': 'computer',
}

_MDNS_MODEL_CLASS: dict[str, str] = {
    'iphone':  'phone',
    'ipad':    'phone',
    'ipod':    'phone',
    'mac':     'computer',
    'xserve':  'nas',    # Synology NASes report model=Xserve
}


def _class_from_mdns(services: list[str], model: str) -> str | None:
    model_l = model.lower()
    for kw, cls in _MDNS_MODEL_CLASS.items():
        if kw in model_l:
            return cls
    for svc in services:
        cls = _MDNS_CLASS.get(svc)
        if cls:
            return cls
    return None


class _MDNSWorker(QThread):
    result = Signal(dict)   # ip -> {'services': [str], 'model': str}

    def run(self) -> None:
        if not _CMD_AVAHI:
            self.result.emit({})
            return
        try:
            proc = subprocess.run(
                [_CMD_AVAHI, '-a', '-t', '-r', '-p'],
                capture_output=True, text=True, timeout=8,
            )
        except Exception:
            self.result.emit({})
            return

        data: dict[str, dict] = {}
        for line in proc.stdout.splitlines():
            if not line.startswith('='):
                continue
            parts = line.split(';')
            if len(parts) < 9 or parts[2] != 'IPv4':
                continue
            svc_type = parts[4]
            ip       = parts[7]
            txt      = ' '.join(parts[9:]) if len(parts) > 9 else ''
            if not ip:
                continue
            if ip not in data:
                data[ip] = {'services': [], 'model': ''}
            if svc_type not in data[ip]['services']:
                data[ip]['services'].append(svc_type)

            # KDE Connect: refine via type= in TXT
            if svc_type == '_kdeconnect._udp':
                m = re.search(r'"type=([^"]+)"', txt)
                if m and m.group(1) == 'phone':
                    if '_kdeconnect_phone' not in data[ip]['services']:
                        data[ip]['services'].append('_kdeconnect_phone')

            # Extract device model from TXT records (various service types)
            if not data[ip]['model']:
                for key in ('model=', 'am='):
                    m = re.search(rf'{key}([^";\s]+)', txt)
                    if m:
                        data[ip]['model'] = m.group(1)
                        break

            # "Device Info" is avahi's human-readable name for _device-info._tcp
            if svc_type == 'Device Info' and not data[ip]['model']:
                m = re.search(r'model=([^";\s]+)', txt)
                if m:
                    data[ip]['model'] = m.group(1)

        self.result.emit(data)


# ── Page ─────────────────────────────────────────────────────────────────────

class TopologyPage(QWidget):
    action_requested = Signal(str, str, str)  # action_key, ip, host

    def __init__(self) -> None:
        super().__init__()
        self._worker:       _TopoWorker  | None = None
        self._mdns_worker:  _MDNSWorker  | None = None
        self._mdns_cache:   dict[str, dict]     = {}
        self._nodes:        dict[str, _NodeItem] = {}
        self._gateway_node: _NodeItem | None     = None
        self._scene_hint                          = None
        self._build_ui()
        self._init_network()

    # ── Layout ───────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Toolbar
        bar = QHBoxLayout()
        bar.addWidget(QLabel(tr('topo_cidr_lbl')))
        self._cidr_edit = QLineEdit()
        self._cidr_edit.setMaximumWidth(185)
        self._cidr_edit.setPlaceholderText('192.168.1.0/24')
        self._cidr_edit.textChanged.connect(self._update_cli)
        self._cidr_edit.returnPressed.connect(self._scan)
        bar.addWidget(self._cidr_edit)
        bar.addSpacing(6)
        self._btn_scan = QPushButton(tr('topo_scan_btn'))
        self._btn_scan.setDefault(True)
        self._btn_scan.clicked.connect(self._scan)
        self._btn_stop = QPushButton(tr('topo_stop_btn'))
        self._btn_stop.setEnabled(False)
        self._btn_stop.clicked.connect(self._stop)
        self._btn_fit = QPushButton(tr('topo_fit_btn'))
        self._btn_fit.clicked.connect(lambda: self._view.fit_all())
        bar.addWidget(self._btn_scan)
        bar.addWidget(self._btn_stop)
        bar.addWidget(self._btn_fit)
        bar.addStretch()
        self._lbl_status = QLabel('')
        self._lbl_status.setStyleSheet('color: palette(mid);')
        bar.addWidget(self._lbl_status)
        layout.addLayout(bar)

        # Legend
        legend = QHBoxLayout()
        legend.addStretch()
        for col, key in (
            (_C_GATEWAY, 'topo_legend_gw'),
            (_C_SELF,    'topo_legend_self'),
            (_C_HOST,    'topo_legend_host'),
        ):
            dot = QLabel('●')
            dot.setStyleSheet(f'color: {col.name()}; font-size: 11px;')
            legend.addWidget(dot)
            legend.addWidget(QLabel(tr(key)))
            legend.addSpacing(14)
        layout.addLayout(legend)

        # Splitter: map | detail panel
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        self._scene = QGraphicsScene()
        self._view  = _TopoView(self._scene)
        self._view.setMinimumHeight(300)
        self._view.setProperty('topology_page', self)
        self._view.node_selected.connect(self._on_node_selected)
        splitter.addWidget(self._view)

        det_box = QGroupBox(tr('topo_detail_title'))
        det_box.setMinimumWidth(180)
        det_box.setMaximumWidth(230)
        self._det_form = QFormLayout(det_box)
        self._det_form.setHorizontalSpacing(12)
        self._det_form.setVerticalSpacing(6)
        self._det_form.setContentsMargins(8, 12, 8, 8)
        self._det_form.addRow(self._make_hint_label())
        splitter.addWidget(det_box)
        splitter.setSizes([760, 210])

        layout.addWidget(splitter, 1)

        self._add_scene_hint()

    def _make_hint_label(self) -> QLabel:
        lbl = QLabel(tr('topo_no_sel'))
        lbl.setStyleSheet('color: palette(mid);')
        lbl.setWordWrap(True)
        return lbl

    def _add_scene_hint(self) -> None:
        pal  = QApplication.palette()
        item = self._scene.addText(tr('topo_map_hint'))
        item.setFont(QFont('Sans', 10))
        item.setDefaultTextColor(pal.color(QPalette.ColorRole.PlaceholderText))
        item.setPos(-item.boundingRect().width() / 2, -14)
        self._scene_hint = item

    def _init_network(self) -> None:
        cidr, _, _ = _local_network()
        if cidr:
            self._cidr_edit.setText(cidr)
        self._update_cli()

    def _update_cli(self) -> None:
        bar = get_cli_bar()
        if bar:
            cidr = self._cidr_edit.text().strip()
            bar.set_cmd(f'nmap -sn {cidr}' if cidr else '')

    # ── Scan ─────────────────────────────────────────────────────────────────

    def _scan(self) -> None:
        cidr = self._cidr_edit.text().strip()
        if not cidr or (self._worker and self._worker.isRunning()):
            return

        _, gateway, self_ip = _local_network()

        # Reset
        self._scene_hint = None
        self._scene.clear()
        self._nodes.clear()
        self._gateway_node = None
        self._mdns_cache.clear()
        self._add_scene_hint()

        self._btn_scan.setEnabled(False)
        self._btn_stop.setEnabled(True)
        self._lbl_status.setText(tr('topo_scanning'))
        self._lbl_status.setStyleSheet('color: palette(mid);')

        if _CMD_AVAHI:
            self._mdns_worker = _MDNSWorker()
            self._mdns_worker.result.connect(self._on_mdns_result)
            self._mdns_worker.start()

        self._worker = _TopoWorker(cidr, gateway, self_ip)
        self._worker.node_found.connect(self._on_node)
        self._worker.done.connect(self._on_done)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _stop(self) -> None:
        if self._worker:
            self._worker.stop()
        if self._mdns_worker and self._mdns_worker.isRunning():
            self._mdns_worker.terminate()
        self._btn_scan.setEnabled(True)
        self._btn_stop.setEnabled(False)
        self._lbl_status.setText(tr('topo_stopped'))

    # ── Node handling ─────────────────────────────────────────────────────────

    def _on_mdns_result(self, mdns_data: dict) -> None:
        self._mdns_cache = mdns_data
        for ip, info in mdns_data.items():
            cls = _class_from_mdns(info['services'], info['model'])
            if cls and ip in self._nodes:
                node = self._nodes[ip]
                node.data['device_class'] = cls
                node._dev_class = cls
                node.update()

    def _on_node(self, data: dict) -> None:
        data['device_class'] = _detect_device_class(data)
        mdns = self._mdns_cache.get(data['ip'])
        if mdns:
            cls = _class_from_mdns(mdns['services'], mdns['model'])
            if cls:
                data['device_class'] = cls

        if self._scene_hint is not None:
            self._scene.removeItem(self._scene_hint)
            self._scene_hint = None

        node = _NodeItem(data)
        self._scene.addItem(node)
        self._nodes[data['ip']] = node

        if data['type'] == 'gateway':
            self._gateway_node = node
            node.setPos(0, 0)
        else:
            # Temporary position — overwritten by _do_layout
            idx   = sum(1 for n in self._nodes.values() if n.data['type'] != 'gateway')
            angle = 2 * math.pi * (idx - 1) / max(idx, 1)
            node.setPos(180 * math.cos(angle), 180 * math.sin(angle))

        if self._gateway_node and node is not self._gateway_node:
            self._scene.addItem(_EdgeItem(self._gateway_node, node))

    def _on_done(self, count: int) -> None:
        self._btn_scan.setEnabled(True)
        self._btn_stop.setEnabled(False)
        self._worker = None
        self._lbl_status.setText(tr('topo_done', n=count))
        self._lbl_status.setStyleSheet('color: palette(mid);')
        self._do_layout()
        self._view.fit_all()

    def _on_error(self, msg: str) -> None:
        self._btn_scan.setEnabled(True)
        self._btn_stop.setEnabled(False)
        self._worker = None
        self._lbl_status.setText(f'⚠  {msg}')
        self._lbl_status.setStyleSheet(f'color: {color_err()};')

    def _do_layout(self) -> None:
        """Star layout: gateway at centre; 1 or 2 rings depending on host count."""
        if self._gateway_node:
            self._gateway_node.setPos(0, 0)
            others = [n for n in self._nodes.values()
                      if n.data['type'] != 'gateway']
        else:
            others = list(self._nodes.values())

        n = len(others)
        if n == 0:
            return

        _SPLIT = 12
        if n <= _SPLIT:
            _place_on_ring(others, max(160, n * 42))
        else:
            n1 = max(6, round(n * 0.4))
            R1 = max(150, n1 * 42)
            R2 = R1 + max(110, (n - n1) * 30)
            _place_on_ring(others[:n1], R1)
            _place_on_ring(others[n1:], R2)

        for node in self._nodes.values():
            for edge in node._edges:
                edge.sync()

    # ── Detail panel ─────────────────────────────────────────────────────────

    def _on_node_selected(self, data: dict | None) -> None:
        while self._det_form.rowCount():
            self._det_form.removeRow(0)

        if data is None:
            self._det_form.addRow(self._make_hint_label())
            return

        def row(key: str, val: str) -> None:
            lbl = QLabel(val or '—')
            lbl.setWordWrap(True)
            lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self._det_form.addRow(tr(key) + ' :', lbl)

        row('topo_lbl_type',     tr(f'topo_type_{data.get("device_class", data["type"])}'))
        row('topo_lbl_ip',       data['ip'])
        row('topo_lbl_hostname', data.get('hostname', ''))
        row('topo_lbl_mac',      data.get('mac', '—'))
        row('topo_lbl_vendor',   data.get('vendor', '—'))

        if data['ip'] in self._nodes:
            node_item = self._nodes[data['ip']]
            vp_rect = self._view.mapToScene(self._view.viewport().rect()).boundingRect()
            if not vp_rect.contains(node_item.pos()):
                self._view.centerOn(node_item)

    # ── Context menu (node right-click) ──────────────────────────────────────

    def _show_node_menu(self, ip: str, host: str, ports: list[int], screen_pos) -> None:
        menu = HostActionMenu(ip, host, ports or None, parent=self)
        menu.action_chosen.connect(self.action_requested)
        menu.exec(screen_pos.toPoint())

    # ── load_hosts (inject from IP Scanner) ──────────────────────────────────

    def load_hosts(self, hosts: list[dict], highlight_ip: str = '') -> None:
        if not hosts:
            return
        self._scene_hint = None
        self._scene.clear()
        self._nodes.clear()
        self._gateway_node = None

        # Inject gateway first so _on_node draws edges automatically.
        # Always inject as 'gateway' type, even if IP Scanner found it,
        # so _gateway_node is set before host nodes are added.
        _, gateway_ip, _ = _local_network()
        if gateway_ip:
            gw_data = next((h for h in hosts if h.get('ip') == gateway_ip), {})
            self._on_node({
                'ip':       gateway_ip,
                'hostname': gw_data.get('hostname', ''),
                'mac':      gw_data.get('mac', ''),
                'vendor':   gw_data.get('vendor', ''),
                'type':     'gateway',
                'rtt':      0.0,
            })

        for data in hosts:
            if data.get('ip') == gateway_ip:
                continue  # already injected as gateway
            self._on_node({
                'ip':       data.get('ip', ''),
                'hostname': data.get('hostname', ''),
                'mac':      data.get('mac', ''),
                'vendor':   data.get('vendor', ''),
                'type':     'host',
                'rtt':      0.0,
            })

        if highlight_ip and highlight_ip in self._nodes:
            node = self._nodes[highlight_ip]
            node._highlight = True
            self._view.centerOn(node)

        self._do_layout()
        self._view.fit_all()
        self._lbl_status.setText(f"{len(hosts)} hôtes importés")

    # ── Visibility ────────────────────────────────────────────────────────────

    def showEvent(self, event) -> None:  # noqa: N802
        self._update_cli()
        super().showEvent(event)
