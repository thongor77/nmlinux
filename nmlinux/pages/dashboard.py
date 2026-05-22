from __future__ import annotations

import json
import re
import socket
import subprocess
import urllib.request
from concurrent.futures import ThreadPoolExecutor, wait as _wait
from ipaddress import IPv4Network

from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QGroupBox, QFormLayout,
    QScrollArea,
)
from PySide6.QtCore import Qt, QThread, Signal

from nmlinux.core.i18n import tr
from nmlinux.core.theme import color_ok, color_err


# ── Data collectors (run in threads) ─────────────────────────────────────────

def _collect_local() -> dict:
    out: dict = {}

    try:
        out['hostname'] = socket.gethostname()
    except Exception:
        out['hostname'] = '—'

    try:
        route = subprocess.run(
            ['ip', 'route', 'show', 'default'],
            capture_output=True, text=True, timeout=3,
        ).stdout
        m_gw = re.search(r'via (\S+)', route)
        m_if = re.search(r'dev (\S+)', route)
        out['gateway'] = m_gw.group(1) if m_gw else '—'
        out['iface']   = m_if.group(1) if m_if else ''
    except Exception:
        out['gateway'] = '—'
        out['iface']   = ''

    iface = out['iface']

    try:
        cmd = ['ip', '-4', 'addr', 'show'] + ([iface] if iface else [])
        raw = subprocess.run(cmd, capture_output=True, text=True, timeout=3).stdout
        m = re.search(r'inet (\d+\.\d+\.\d+\.\d+)/(\d+)', raw)
        out['local_ipv4']   = m.group(1) if m else '—'
        out['subnet_mask']  = str(IPv4Network(f'0.0.0.0/{m.group(2)}', strict=False).netmask) if m else '—'
    except Exception:
        out['local_ipv4']  = '—'
        out['subnet_mask'] = '—'

    try:
        cmd = ['ip', '-6', 'addr', 'show', 'scope', 'global'] + \
              (['dev', iface] if iface else [])
        raw = subprocess.run(cmd, capture_output=True, text=True, timeout=3).stdout
        m = re.search(r'inet6 (\S+)/', raw)
        out['local_ipv6'] = m.group(1) if m else '—'
    except Exception:
        out['local_ipv6'] = '—'

    try:
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


# ── UI helpers ────────────────────────────────────────────────────────────────

_GREY  = 'palette(mid)'


def _card(title: str) -> tuple[QGroupBox, QFormLayout]:
    box  = QGroupBox(title)
    form = QFormLayout(box)
    form.setHorizontalSpacing(16)
    form.setVerticalSpacing(6)
    form.setContentsMargins(12, 12, 12, 12)
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
        self._build_ui()
        self._refresh()

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
        self._box_gw,  self._form_gw  = _card(tr("dash_card_gw"))
        self._box_net, self._form_net = _card(tr("dash_card_net"))
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

        inner   = QWidget()
        hlayout = QHBoxLayout(inner)
        hlayout.setContentsMargins(0, 0, 0, 0)
        hlayout.setSpacing(32)

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

        row(left,  "geo_country",   'country')
        row(left,  "geo_code",      'countryCode')
        row(left,  "geo_region",    'regionName')
        row(left,  "geo_city",      'city')
        row(left,  "geo_zip",       'zip')
        row(left,  "geo_lat",       'lat')
        row(left,  "geo_lon",       'lon')
        row(left,  "geo_timezone",  'timezone')

        row(right, "geo_isp",    'isp')
        row(right, "geo_org",    'org')
        row(right, "geo_as",     'as')
        row(right, "geo_asname", 'asname')

        hlayout.addLayout(left)
        hlayout.addLayout(right)
        hlayout.addStretch(1)

        f.addRow(inner)

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
