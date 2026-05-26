from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QImage, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

_ICONS_DIR = Path(__file__).parent.parent / "assets" / "icons"
_ICON_COLOR = "#60a5fa"  # blue — applied to all bundled icons

# Maps the legacy themed_icon() name variants to bundled SVG filenames
_NAME_MAP: dict[str, str] = {
    # Dashboard
    "go-home": "gauge", "user-home": "gauge", "folder-home": "gauge",
    # Connexions
    "network-manager": "network", "preferences-system-network": "network",
    # Interfaces
    "network-connect": "monitor", "network-transmit-receive": "monitor",
    "computer": "monitor",
    # Wi-Fi
    "network-wireless": "wifi", "network-wireless-signal-excellent": "wifi",
    "network-wireless-signal-good": "wifi", "network-workgroup": "wifi",
    # Sous-réseau / DNS
    "network-server": "globe", "server": "globe",
    # Ping / SNTP
    "chronometer": "timer", "appointment-soon": "timer", "clock": "clock",
    # IP Scanner
    "network-wired": "radar",
    # Port Scanner
    "security-medium": "shield-check", "security-high": "shield-check",
    "dialog-password": "shield-check", "changes-prevent": "shield-check",
    "system-lock-screen": "shield-check",
    # Nmap
    "system-search": "telescope", "edit-find": "telescope",
    # Whois
    "dialog-information": "info", "help-about": "info",
    # SNMP / Settings
    "preferences-system": "sliders-horizontal", "system-settings": "sliders-horizontal",
    "configure": "sliders-horizontal",
    # SSH
    "utilities-terminal": "terminal", "terminal": "terminal",
    "gnome-terminal": "terminal",
    # Traceroute
    "go-next": "route", "go-jump": "route", "mail-send": "route",
    # MTR
    "modem": "activity",
    # Firewall
    "firewall": "flame", "dialog-warning": "flame",
    # Speed Test
    "network-wireless-signal": "zap",
    # Wake on LAN
    "system-shutdown": "power", "system-reboot": "power",
    "media-playback-start": "power",
    # Topology
    "network-workgroup-topology": "workflow",
    # Calculator
    "accessories-calculator": "calculator",
    # Globe / DNS
    "globe": "globe",
}


@lru_cache(maxsize=64)
def _load_icon(svg_name: str, size: int = 22) -> QIcon:
    path = _ICONS_DIR / f"{svg_name}.svg"
    if not path.exists():
        return QIcon()

    svg_text = path.read_text(encoding="utf-8")
    # Replace stroke color (Lucide uses currentColor)
    svg_text = re.sub(r'stroke="currentColor"', f'stroke="{_ICON_COLOR}"', svg_text)
    svg_text = re.sub(r'stroke="#[0-9a-fA-F]+"', f'stroke="{_ICON_COLOR}"', svg_text)

    renderer = QSvgRenderer(svg_text.encode())
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()

    return QIcon(pixmap)


def themed_icon(*names: str) -> QIcon:
    """Return a bundled Lucide icon for the first recognised name, else empty."""
    for name in names:
        svg_name = _NAME_MAP.get(name) or (name if (_ICONS_DIR / f"{name}.svg").exists() else None)
        if svg_name:
            icon = _load_icon(svg_name)
            if not icon.isNull():
                return icon
    return QIcon()
