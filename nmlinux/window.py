from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QListWidgetItem, QStackedWidget, QFrame, QSizePolicy,
    QStyledItemDelegate, QStyle,
)
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPainter, QColor, QFont

from nmlinux.core.i18n import tr
from nmlinux.core.icons import themed_icon
from nmlinux.core.cli_bar import CliBar, get_cli_bar

from nmlinux.pages.dashboard import DashboardPage
from nmlinux.pages.interfaces import InterfacesPage
from nmlinux.pages.wifi import WifiPage
from nmlinux.pages.subnet import SubnetPage
from nmlinux.pages.dns import DnsPage
from nmlinux.pages.ping import PingPage
from nmlinux.pages.ip_scanner import IpScannerPage
from nmlinux.pages.port_scanner import PortScannerPage
from nmlinux.pages.nmap_scan import NmapPage
from nmlinux.pages.whois import WhoisPage
from nmlinux.pages.snmp import SnmpPage
from nmlinux.pages.sntp import SntpPage
from nmlinux.pages.ssh import SshPage
from nmlinux.pages.rdp import RdpPage
from nmlinux.pages.vnc import VncPage
from nmlinux.pages.traceroute import TraceroutePage
from nmlinux.pages.mtr import MtrPage
from nmlinux.pages.firewall import FirewallPage
from nmlinux.pages.speedtest import SpeedTestPage
from nmlinux.pages.bandwidth import BandwidthPage
from nmlinux.pages.wol import WolPage
from nmlinux.pages.connection_manager import ConnectionManagerPage
from nmlinux.pages.topology import TopologyPage
from nmlinux.pages.settings import SettingsPage
from nmlinux.pages.about import AboutPage


# (icon_names, label, PageClass, description)
_TOOLS = [
    (
        ("go-home", "user-home", "folder-home"),
        "Dashboard", DashboardPage,
        "Vue d'ensemble du réseau : IP locale, passerelle, DNS,\ngéolocalisation et accès Internet.",
    ),
    (
        ("network-wired", "network-manager", "preferences-system-network"),
        "Connexions", ConnectionManagerPage,
        "Gère les profils réseau NetworkManager :\ncréer, modifier, activer ou désactiver des connexions.",
    ),
    (
        ("network-connect", "network-transmit-receive", "network-wired", "computer"),
        "Interfaces", InterfacesPage,
        "Affiche les interfaces réseau actives (Ethernet, Wi-Fi, loopback…)\navec état, adresse MAC et adresses IP.",
    ),
    (
        ("network-wireless", "network-wireless-signal-excellent", "network-wireless-signal-good", "network-workgroup"),
        "Wi-Fi", WifiPage,
        "Scanne les réseaux sans fil disponibles, affiche\nle niveau de signal et la sécurité, et permet de s'y connecter.",
    ),
    (
        ("network-wired", "network-server"),
        "Sous-réseau", SubnetPage,
        "Calcule la plage d'adresses, le masque, le broadcast\net le nombre d'hôtes d'un réseau CIDR.",
    ),
    (
        ("network-server", "server", "network-wired"),
        "DNS", DnsPage,
        "Interroge un ou plusieurs serveurs DNS\net mesure leur temps de réponse.",
    ),
    (
        ("chronometer", "appointment-soon", "clock"),
        "Ping", PingPage,
        "Envoie des paquets ICMP pour tester la latence\net la disponibilité d'un hôte.",
    ),
    (
        ("network-workgroup", "network-wired", "computer"),
        "IP Scanner", IpScannerPage,
        "Découvre les équipements actifs sur le réseau local\npar balayage ARP/ping.",
    ),
    (
        ("security-medium", "security-high", "dialog-password", "changes-prevent", "system-lock-screen"),
        "Port Scanner", PortScannerPage,
        "Scanne les ports TCP/UDP d'un hôte\npour identifier les services réseau ouverts.",
    ),
    (
        ("system-search", "edit-find"),
        "Nmap", NmapPage,
        "Scan réseau avancé : services, versions,\nOS détecté et scripts NSE de sécurité.",
    ),
    (
        ("dialog-information", "help-about"),
        "Whois", WhoisPage,
        "Affiche les informations d'enregistrement\nd'un domaine ou d'une adresse IP.",
    ),
    (
        ("preferences-system", "system-settings", "configure"),
        "SNMP", SnmpPage,
        "Interroge des équipements réseau compatibles SNMP (v1/v2c/v3)\npour lire leurs variables MIB.",
    ),
    (
        ("clock", "chronometer", "appointment-soon"),
        "SNTP / NTP", SntpPage,
        "Teste la synchronisation avec un serveur de temps NTP\net mesure la dérive d'horloge.",
    ),
    (
        ("utilities-terminal", "terminal", "gnome-terminal"),
        "SSH", SshPage,
        "Terminal SSH embarqué pour se connecter à distance\nà un serveur ou un équipement réseau.",
    ),
    (
        ("computer", "network-workgroup", "preferences-desktop-remote-desktop"),
        "Remote Desktop", RdpPage,
        "Gère les profils de connexion Bureau à distance (RDP)\net lance xfreerdp vers des machines Windows.",
    ),
    (
        ("computer", "video-display", "network-workgroup"),
        "VNC", VncPage,
        "Gère les profils de connexion VNC\net lance vncviewer vers des machines macOS, Linux ou Windows.",
    ),
    (
        ("network-wired", "network-transmit-receive", "go-next", "go-jump", "mail-send", "network-workgroup"),
        "Traceroute", TraceroutePage,
        "Affiche le chemin réseau vers une destination\net la latence de chaque routeur traversé.",
    ),
    (
        ("network-wired", "network-transmit-receive", "chronometer", "appointment-soon"),
        "MTR", MtrPage,
        "Combine traceroute et ping : statistiques de perte\net de latence en continu sur chaque saut réseau.",
    ),
    (
        ("security-medium", "security-high", "firewall", "system-lock-screen", "changes-prevent", "dialog-warning"),
        "Firewall", FirewallPage,
        "Lit et affiche les règles pare-feu nftables et iptables\nsans nécessiter les droits root.",
    ),
    (
        ("network-transmit-receive", "modem", "network-wired", "go-down", "utilities-system-monitor", "appointment-soon"),
        "Speed Test", SpeedTestPage,
        "Mesure le débit descendant, montant et le ping\nvia les serveurs Cloudflare.",
    ),
    (
        ("network-transmit-receive", "network-wired", "utilities-system-monitor"),
        "Bandwidth", BandwidthPage,
        "Surveille le débit réseau en temps réel\nsur une interface sélectionnée.",
    ),
    (
        ("system-shutdown", "system-reboot", "media-playback-start"),
        "Wake on LAN", WolPage,
        "Envoie un Magic Packet pour démarrer à distance\nun équipement via le réseau local.",
    ),
    (
        ("network-workgroup", "computer", "network-wired"),
        "Topologie", TopologyPage,
        "Génère une carte visuelle des équipements\ndécouverts sur le réseau local.",
    ),
]


class _NavHintDelegate(QStyledItemDelegate):
    """Draws a subtle ⓘ badge at the right edge of each nav item."""

    _D = 15  # diameter of the badge circle

    def paint(self, painter: QPainter, option, index) -> None:
        super().paint(painter, option, index)

        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        r = option.rect
        d = self._D
        x = r.right() - d - 5
        y = r.top() + (r.height() - d) // 2

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if selected:
            circle_col = QColor(255, 255, 255, 55)
            text_col   = QColor(255, 255, 255, 200)
        else:
            circle_col = QColor(128, 128, 128, 45)
            text_col   = QColor(160, 160, 160, 210)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(circle_col)
        painter.drawEllipse(x, y, d, d)

        font = QFont(painter.font())
        font.setPointSize(7)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(text_col)
        painter.drawText(x, y, d, d, Qt.AlignmentFlag.AlignCenter, "?")

        painter.restore()


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("NMLinux")
        self.setMinimumSize(960, 820)
        self.resize(1180, 900)

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_sidebar())

        # Vertical separator between sidebar and content area
        vsep = QFrame()
        vsep.setFrameShape(QFrame.Shape.VLine)
        vsep.setFrameShadow(QFrame.Shadow.Sunken)
        vsep.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        root.addWidget(vsep)

        right = QWidget()
        rv = QVBoxLayout(right)
        rv.setContentsMargins(0, 0, 0, 0)
        rv.setSpacing(0)
        rv.addWidget(self._build_stack(), 1)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        sep.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        rv.addWidget(sep)

        rv.addWidget(CliBar())
        root.addWidget(right, 1)

    def _build_sidebar(self) -> QFrame:
        frame = QFrame()
        frame.setFixedWidth(190)
        frame.setFrameShape(QFrame.Shape.NoFrame)
        frame.setObjectName("sidebar")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Tools navigation (scrollable, fills available space) ──────────
        self._nav = QListWidget()
        self._nav.setIconSize(QSize(20, 20))
        self._nav.setSpacing(2)
        self._nav.setFrameShape(QFrame.Shape.NoFrame)
        self._nav.setItemDelegate(_NavHintDelegate(self._nav))
        self._nav.currentRowChanged.connect(self._on_nav_changed)

        for icon_names, label, _, tip in _TOOLS:
            item = QListWidgetItem(themed_icon(*icon_names), label)
            item.setToolTip(tip)
            self._nav.addItem(item)

        layout.addWidget(self._nav, 1)

        # ── Separator ─────────────────────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(sep)

        # ── Settings (fixed at bottom) ────────────────────────────────────
        self._nav_settings = QListWidget()
        self._nav_settings.setIconSize(QSize(20, 20))
        self._nav_settings.setSpacing(2)
        self._nav_settings.setFrameShape(QFrame.Shape.NoFrame)
        self._nav_settings.setFixedHeight(72)
        self._nav_settings.currentRowChanged.connect(self._on_settings_nav_changed)

        self._settings_item = QListWidgetItem(
            themed_icon("preferences-system", "system-settings", "configure"),
            tr("nav_settings"),
        )
        self._nav_settings.addItem(self._settings_item)

        self._about_item = QListWidgetItem(
            themed_icon("help-about", "dialog-information"),
            tr("nav_about"),
        )
        self._nav_settings.addItem(self._about_item)

        layout.addWidget(self._nav_settings)
        return frame

    def _build_stack(self) -> QStackedWidget:
        self._stack = QStackedWidget()
        self._pages: list[QWidget] = []

        for _, _, PageClass, _ in _TOOLS:  # type: ignore[misc]
            page = PageClass()
            self._stack.addWidget(page)
            self._pages.append(page)

        # Settings page — index = len(_TOOLS)
        self._settings_page = SettingsPage()
        self._settings_page.language_changed.connect(self._on_language_changed)
        self._stack.addWidget(self._settings_page)

        # About page — index = len(_TOOLS) + 1
        self._about_page = AboutPage()
        self._stack.addWidget(self._about_page)

        self._nav.setCurrentRow(0)
        return self._stack

    def _on_nav_changed(self, row: int) -> None:
        if 0 <= row < len(self._pages):
            self._nav_settings.blockSignals(True)
            self._nav_settings.clearSelection()
            self._nav_settings.setCurrentRow(-1)
            self._nav_settings.blockSignals(False)
            bar = get_cli_bar()
            if bar:
                bar.set_cmd('')
            self._stack.setCurrentIndex(row)

    def _on_settings_nav_changed(self, row: int) -> None:
        if row < 0:
            return
        self._nav.blockSignals(True)
        self._nav.clearSelection()
        self._nav.setCurrentRow(-1)
        self._nav.blockSignals(False)
        if row == 0:
            self._stack.setCurrentIndex(len(self._pages))
        elif row == 1:
            self._stack.setCurrentIndex(len(self._pages) + 1)

    def _on_language_changed(self) -> None:
        self._settings_item.setText(tr("nav_settings"))
        self._about_item.setText(tr("nav_about"))
