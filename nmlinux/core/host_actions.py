from __future__ import annotations
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QMenu

ACT_PING       = "ping"
ACT_PORT_SCAN  = "port_scan"
ACT_WHOIS      = "whois"
ACT_DNS        = "dns"
ACT_TRACEROUTE = "traceroute"
ACT_MTR        = "mtr"
ACT_SSH        = "ssh"
ACT_RDP        = "rdp"
ACT_VNC        = "vnc"
ACT_TOPOLOGY   = "topology"
ACT_ASSET      = "asset"

_PORT_SSH = 22
_PORT_RDP = 3389
_PORT_VNC = 5900


class HostActionMenu(QMenu):
    action_chosen = Signal(str, str, str)  # action_key, ip, host

    def __init__(
        self,
        ip: str,
        host: str = '',
        ports: list[int] | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._ip    = ip
        self._host  = host
        self._ports = set(ports) if ports else set()

        title = host if (host and host != ip) else ip
        self.setTitle(title)

        self.addSection("Naviguer vers")
        self._add(ACT_PING,       "Ping")
        self._add(ACT_PORT_SCAN,  "Scanner les ports")
        self._add(ACT_WHOIS,      "Whois")
        self._add(ACT_DNS,        "DNS")
        self._add(ACT_TRACEROUTE, "Traceroute")
        self._add(ACT_MTR,        "MTR")

        self.addSection("Connexion")
        self._add(ACT_SSH, "SSH", bold=_PORT_SSH in self._ports)
        self._add(ACT_RDP, "RDP", bold=_PORT_RDP in self._ports)
        self._add(ACT_VNC, "VNC", bold=_PORT_VNC in self._ports)

        self.addSection("Inventaire")
        self._add(ACT_TOPOLOGY, "Voir en Topologie")
        self._add(ACT_ASSET,    "Ajouter à l'inventaire")

    def _add(self, key: str, label: str, bold: bool = False) -> None:
        action = self.addAction(label)
        if bold:
            f = action.font()
            f.setBold(True)
            action.setFont(f)
        action.triggered.connect(
            lambda _checked=False, k=key: self.action_chosen.emit(k, self._ip, self._host)
        )
