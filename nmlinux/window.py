from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QListWidgetItem, QStackedWidget, QFrame,
)
from PySide6.QtCore import QSize

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
from nmlinux.pages.traceroute import TraceroutePage
from nmlinux.pages.bandwidth import BandwidthPage
from nmlinux.pages.wol import WolPage
from nmlinux.pages.connection_manager import ConnectionManagerPage
from nmlinux.pages.settings import SettingsPage
from nmlinux.pages.about import AboutPage


_TOOLS = [
    (("go-home", "user-home", "folder-home"),                                        "Dashboard",    DashboardPage),
    (("network-wired", "network-manager", "preferences-system-network"),            "Connexions",   ConnectionManagerPage),
    (("network-connect", "network-transmit-receive", "network-wired"),               "Interfaces",   InterfacesPage),
    (("network-wireless", "network-wireless-signal-excellent"),                      "Wi-Fi",        WifiPage),
    (("network-wired", "network-server"),                                            "Sous-réseau",  SubnetPage),
    (("network-server", "server", "network-wired"),                                  "DNS",          DnsPage),
    (("chronometer", "appointment-soon", "clock"),                                   "Ping",         PingPage),
    (("network-workgroup", "network-wired", "computer"),                             "IP Scanner",   IpScannerPage),
    (("security-medium", "security-high", "dialog-password", "changes-prevent"),    "Port Scanner", PortScannerPage),
    (("system-search", "edit-find"),                                                 "Nmap",         NmapPage),
    (("dialog-information", "help-about"),                                           "Whois",        WhoisPage),
    (("preferences-system", "system-settings", "configure"),                        "SNMP",         SnmpPage),
    (("clock", "chronometer", "appointment-soon"),                                   "SNTP / NTP",   SntpPage),
    (("utilities-terminal", "terminal", "gnome-terminal"),                           "SSH",          SshPage),
    (("network-wired", "network-transmit-receive"),                                  "Traceroute",   TraceroutePage),
    (("network-transmit-receive", "network-wired", "utilities-system-monitor"),      "Bandwidth",    BandwidthPage),
    (("system-shutdown", "system-reboot", "media-playback-start"),                  "Wake on LAN",  WolPage),
]


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("NMLinux")
        self.setMinimumSize(960, 620)
        self.resize(1100, 700)

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_sidebar())

        right = QWidget()
        rv = QVBoxLayout(right)
        rv.setContentsMargins(0, 0, 0, 0)
        rv.setSpacing(0)
        rv.addWidget(self._build_stack(), 1)
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
        self._nav.currentRowChanged.connect(self._on_nav_changed)

        for icon_names, label, _ in _TOOLS:
            item = QListWidgetItem(themed_icon(*icon_names), label)
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

        for _, _, PageClass in _TOOLS:  # type: ignore[misc]
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
