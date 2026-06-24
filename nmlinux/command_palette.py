from __future__ import annotations
from typing import Callable

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem,
)
from PySide6.QtCore import Qt

_KEYWORDS: dict[str, list[str]] = {
    "Dashboard":      ["home", "overview", "status", "summary"],
    "Connections":    ["connection", "manager", "nmcli", "network", "profile"],
    "Interfaces":     ["interface", "ip", "eth", "link", "adapter", "nic", "ifconfig"],
    "Wi-Fi":          ["wifi", "wireless", "wlan", "signal", "ssid", "wpa"],
    "Subnet":         ["subnet", "mask", "cidr", "network", "calculator", "netmask"],
    "DNS":            ["dns", "resolver", "nameserver", "lookup", "resolve"],
    "Ping":           ["ping", "icmp", "latency", "reachability", "echo"],
    "IP Scanner":     ["scan", "arp", "discovery", "hosts", "lan", "devices"],
    "Port Scanner":   ["port", "tcp", "udp", "open", "closed", "service"],
    "Nmap":           ["nmap", "scan", "security", "vulnerability", "probe"],
    "Whois":          ["whois", "domain", "registrar", "info", "lookup"],
    "TLS Inspector":  ["tls", "ssl", "certificate", "https", "security", "cert"],
    "SMB / NFS":      ["smb", "nfs", "samba", "shares", "windows", "mount"],
    "Hosts File":     ["hosts", "hostname", "etc", "local", "dns", "override"],
    "SNMP":           ["snmp", "monitoring", "oid", "trap", "agent"],
    "SNTP / NTP":     ["sntp", "ntp", "time", "sync", "clock", "date"],
    "SSH":            ["ssh", "remote", "terminal", "shell", "connect", "secure"],
    "SSH Keys":       ["ssh keys", "keygen", "ed25519", "rsa", "authorized", "public key"],
    "Remote Desktop": ["rdp", "remote desktop", "windows", "xfreerdp", "mstsc"],
    "VNC":            ["vnc", "remote", "display", "tigervnc", "desktop", "screen"],
    "Traceroute":     ["traceroute", "route", "hops", "path", "trace", "ttl"],
    "MTR":            ["mtr", "traceroute", "latency", "packet loss", "network", "path"],
    "Firewall":       ["firewall", "iptables", "nftables", "ufw", "rules", "block"],
    "Speed Test":     ["speed", "bandwidth", "download", "upload", "iperf", "throughput"],
    "Bandwidth":      ["bandwidth", "monitor", "rx", "tx", "traffic", "usage"],
    "Wake on LAN":    ["wol", "wake on lan", "magic packet", "boot", "remote", "power"],
    "Topology":       ["topology", "map", "network", "devices", "graph", "visual"],
    "Asset Inventory": ["asset", "inventory", "scan", "ssh", "winrm", "snmp", "devices", "lan", "hardware"],
}


def filter_modules(query: str, module_labels: list[str]) -> list[tuple[int, str]]:
    """Return (index, label) pairs matching query against labels and keywords.
    Empty query returns all modules."""
    q = query.lower().strip()
    if not q:
        return [(i, label) for i, label in enumerate(module_labels)]
    results = []
    for i, label in enumerate(module_labels):
        keywords = _KEYWORDS.get(label, [])
        if q in label.lower() or any(q in kw for kw in keywords):
            results.append((i, label))
    return results


class CommandPalette(QDialog):
    def __init__(
        self,
        module_labels: list[str],
        navigate_fn: Callable[[int], None],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._labels = module_labels
        self._navigate_fn = navigate_fn
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setWindowTitle("")
        self.setFixedWidth(500)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Go to module…  (Esc to close)")
        self._search.textChanged.connect(self._on_text_changed)
        self._search.returnPressed.connect(self._navigate_selected)
        layout.addWidget(self._search)

        self._list = QListWidget()
        self._list.setMaximumHeight(240)
        self._list.itemClicked.connect(self._navigate_selected)
        layout.addWidget(self._list)

    def _on_text_changed(self, text: str) -> None:
        self._list.clear()
        query = text.strip()
        # Only filter when 2+ chars to avoid noisy single-character results
        effective_query = query if len(query) >= 2 else ""
        for idx, label in filter_modules(effective_query, self._labels):
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, idx)
            self._list.addItem(item)
        if self._list.count() > 0:
            self._list.setCurrentRow(0)

    def _navigate_selected(self) -> None:
        item = self._list.currentItem()
        if item:
            idx = item.data(Qt.ItemDataRole.UserRole)
            self._navigate_fn(idx)
            self.accept()

    def keyPressEvent(self, event) -> None:
        key = event.key()
        if key == Qt.Key.Key_Down:
            row = min(self._list.currentRow() + 1, self._list.count() - 1)
            self._list.setCurrentRow(row)
        elif key == Qt.Key.Key_Up:
            row = max(self._list.currentRow() - 1, 0)
            self._list.setCurrentRow(row)
        else:
            super().keyPressEvent(event)

    def open_palette(self) -> None:
        """Show palette centered at the top of the parent window."""
        self._search.clear()
        self._search.setFocus()
        if self.parent():
            pw = self.parent().geometry()  # type: ignore[union-attr]
            self.adjustSize()
            x = pw.x() + (pw.width() - self.width()) // 2
            y = pw.y() + 60
            self.move(x, y)
        self.exec()
