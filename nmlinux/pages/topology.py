"""Network Topology Map — visual LAN discovery via nmap -sn."""
from __future__ import annotations

import json
import math
import platform
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from ipaddress import IPv4Network

_IS_MACOS = platform.system() == 'Darwin'
_mono = 'Menlo' if _IS_MACOS else 'Monospace'

from PySide6.QtCore import Qt, QLineF, QPointF, QRectF, QThread, Signal
from PySide6.QtGui import (
    QBrush, QColor, QFont, QPainter, QPen, QPalette,
)
from PySide6.QtWidgets import (
    QApplication, QFormLayout, QGraphicsItem, QGraphicsLineItem,
    QGraphicsScene, QGraphicsView, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QSplitter, QVBoxLayout, QWidget,
)

from nmlinux.core.cli_bar import get_cli_bar
from nmlinux.core.i18n import tr
from nmlinux.core.theme import color_err

_CMD_NMAP = shutil.which('nmap')

# Semantic node colours — balanced for both light and dark themes
_C_GATEWAY = QColor('#e8954f')   # amber  — router / gateway
_C_SELF    = QColor('#5b8fda')   # blue   — this machine
_C_HOST    = QColor('#4aaa6e')   # green  — other hosts


def _node_color(node_type: str) -> QColor:
    return {'gateway': _C_GATEWAY, 'self': _C_SELF}.get(node_type, _C_HOST)


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
    """Draggable circle node with IP / hostname label."""
    _R    = 18   # radius for regular hosts
    _R_GW = 24   # larger radius for gateway

    def __init__(self, data: dict) -> None:
        super().__init__()
        self.data   = data
        self._color = _node_color(data['type'])
        self._edges: list[_EdgeItem] = []
        self._r     = float(self._R_GW if data['type'] == 'gateway' else self._R)
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

        # Selection ring
        if self.isSelected():
            painter.setPen(QPen(col.lighter(160), 3, Qt.PenStyle.DotLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QPointF(0, 0), r + 5, r + 5)

        # Circle body
        painter.setPen(QPen(col.darker(160), 2))
        painter.setBrush(QBrush(col))
        painter.drawEllipse(QPointF(0, 0), r, r)

        # Icon
        self._paint_icon(painter)

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

    def _paint_icon(self, painter: QPainter) -> None:
        r   = self._r
        s   = r * 0.38
        typ = self.data['type']

        pen = QPen(QColor(255, 255, 255, 210), 1.3)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        if typ == 'gateway':
            # Router: rectangular body + 2 antennas
            bw, bh = s * 1.7, s * 0.75
            painter.drawRoundedRect(QRectF(-bw / 2, -bh / 2, bw, bh), 1.5, 1.5)
            for dx in (-s * 0.45, s * 0.45):
                painter.drawLine(QLineF(dx, -bh / 2, dx, -bh / 2 - s * 0.8))
        elif typ == 'self':
            # Monitor: screen rectangle + vertical stand + horizontal base
            sw, sh = s * 1.6, s * 1.1
            painter.drawRoundedRect(QRectF(-sw / 2, -sh * 0.8, sw, sh), 1.5, 1.5)
            cy = sh * 0.2
            painter.drawLine(QLineF(0.0, cy, 0.0, cy + s * 0.55))
            painter.drawLine(QLineF(-s * 0.5, cy + s * 0.55, s * 0.5, cy + s * 0.55))
        else:
            # PC tower: tall rounded rect + small power-button dot
            tw, th = s * 0.85, s * 1.6
            painter.drawRoundedRect(QRectF(-tw / 2, -th / 2, tw, th), 1.5, 1.5)
            painter.setBrush(QBrush(QColor(255, 255, 255, 160)))
            painter.drawEllipse(QPointF(0.0, -th / 2 + s * 0.5), s * 0.22, s * 0.22)


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


# ── Page ─────────────────────────────────────────────────────────────────────

class TopologyPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._worker:       _TopoWorker | None = None
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
        self._add_scene_hint()

        self._btn_scan.setEnabled(False)
        self._btn_stop.setEnabled(True)
        self._lbl_status.setText(tr('topo_scanning'))
        self._lbl_status.setStyleSheet('color: palette(mid);')

        self._worker = _TopoWorker(cidr, gateway, self_ip)
        self._worker.node_found.connect(self._on_node)
        self._worker.done.connect(self._on_done)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _stop(self) -> None:
        if self._worker:
            self._worker.stop()
        self._btn_scan.setEnabled(True)
        self._btn_stop.setEnabled(False)
        self._lbl_status.setText(tr('topo_stopped'))

    # ── Node handling ─────────────────────────────────────────────────────────

    def _on_node(self, data: dict) -> None:
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

        row('topo_lbl_type',     tr(f'topo_type_{data["type"]}'))
        row('topo_lbl_ip',       data['ip'])
        row('topo_lbl_hostname', data.get('hostname', ''))
        row('topo_lbl_mac',      data.get('mac', '—'))
        row('topo_lbl_vendor',   data.get('vendor', '—'))

        if data['ip'] in self._nodes:
            node_item = self._nodes[data['ip']]
            vp_rect = self._view.mapToScene(self._view.viewport().rect()).boundingRect()
            if not vp_rect.contains(node_item.pos()):
                self._view.centerOn(node_item)

    # ── Visibility ────────────────────────────────────────────────────────────

    def showEvent(self, event) -> None:  # noqa: N802
        self._update_cli()
        super().showEvent(event)
