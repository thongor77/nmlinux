from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QListWidgetItem, QStackedWidget, QFrame, QSizePolicy,
    QStyledItemDelegate, QStyle,
)
from PySide6.QtCore import QSize, Qt, QTimer, Signal
from PySide6.QtGui import QPainter, QColor, QFont, QShortcut, QKeySequence
from nmlinux.command_palette import CommandPalette

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
from nmlinux.pages.tls import TlsPage
from nmlinux.pages.smb_nfs import SmbNfsPage
from nmlinux.pages.hosts import HostsPage
from nmlinux.pages.snmp import SnmpPage
from nmlinux.pages.sntp import SntpPage
from nmlinux.pages.ssh import SshPage
from nmlinux.pages.ssh_keys import SshKeysPage
from nmlinux.pages.rdp import RdpPage
from nmlinux.pages.vnc import VncPage
from nmlinux.pages.traceroute import TraceroutePage
from nmlinux.pages.mtr import MtrPage
from nmlinux.pages.firewall import FirewallPage
from nmlinux.pages.speedtest import SpeedTestPage
from nmlinux.pages.bandwidth import BandwidthPage
from nmlinux.pages.wol import WolPage
from nmlinux.pages.file_transfer import FileTransferPage
from nmlinux.pages.connection_manager import ConnectionManagerPage
from nmlinux.pages.topology import TopologyPage
from nmlinux.pages.asset_inventory import AssetInventoryPage
from nmlinux.pages.settings import SettingsPage
from nmlinux.pages.about import AboutPage
from nmlinux.pages.help_page import HelpPage

from nmlinux.core.host_actions import (
    ACT_PING, ACT_PORT_SCAN, ACT_WHOIS, ACT_DNS,
    ACT_TRACEROUTE, ACT_MTR, ACT_SSH, ACT_RDP,
    ACT_VNC, ACT_TOPOLOGY, ACT_ASSET,
)


# (icon_names, label, PageClass, description)
_TOOLS = [
    (
        ("go-home", "user-home", "folder-home"),
        "Dashboard", DashboardPage,
        tr("nav_hint_dashboard"),
    ),
    (
        ("network-wired", "network-manager", "preferences-system-network"),
        "Connections", ConnectionManagerPage,
        tr("nav_hint_connections"),
    ),
    (
        ("network-connect", "network-transmit-receive", "network-wired", "computer"),
        "Interfaces", InterfacesPage,
        tr("nav_hint_interfaces"),
    ),
    (
        ("network-wireless", "network-wireless-signal-excellent", "network-wireless-signal-good", "network-workgroup"),
        "Wi-Fi", WifiPage,
        tr("nav_hint_wifi"),
    ),
    (
        ("network-wired", "network-server"),
        "Subnet", SubnetPage,
        tr("nav_hint_subnet"),
    ),
    (
        ("network-server", "server", "network-wired"),
        "DNS", DnsPage,
        tr("nav_hint_dns"),
    ),
    (
        ("chronometer", "appointment-soon", "clock"),
        "Ping", PingPage,
        tr("nav_hint_ping"),
    ),
    (
        ("network-workgroup", "network-wired", "computer"),
        "IP Scanner", IpScannerPage,
        tr("nav_hint_ip_scanner"),
    ),
    (
        ("security-medium", "security-high", "dialog-password", "changes-prevent", "system-lock-screen"),
        "Port Scanner", PortScannerPage,
        tr("nav_hint_port_scanner"),
    ),
    (
        ("system-search", "edit-find"),
        "Nmap", NmapPage,
        tr("nav_hint_nmap"),
    ),
    (
        ("dialog-information", "help-about"),
        "Whois", WhoisPage,
        tr("nav_hint_whois"),
    ),
    (
        ("security-high", "changes-prevent", "system-lock-screen", "dialog-password"),
        "TLS Inspector", TlsPage,
        tr("nav_hint_tls"),
    ),
    (
        ("network-workgroup", "folder-remote", "network-server", "network-wired"),
        "SMB / NFS", SmbNfsPage,
        tr("nav_hint_smb_nfs"),
    ),
    (
        ("text-x-generic", "document-edit", "preferences-system"),
        "Hosts File", HostsPage,
        tr("nav_hint_hosts"),
    ),
    (
        ("preferences-system", "system-settings", "configure"),
        "SNMP", SnmpPage,
        tr("nav_hint_snmp"),
    ),
    (
        ("clock", "chronometer", "appointment-soon"),
        "SNTP / NTP", SntpPage,
        tr("nav_hint_sntp"),
    ),
    (
        ("utilities-terminal", "terminal", "gnome-terminal"),
        "SSH", SshPage,
        tr("nav_hint_ssh"),
    ),
    (
        ("dialog-password", "security-high", "changes-prevent"),
        "SSH Keys", SshKeysPage,
        tr("nav_hint_ssh_keys"),
    ),
    (
        ("computer", "network-workgroup", "preferences-desktop-remote-desktop"),
        "Remote Desktop", RdpPage,
        tr("nav_hint_rdp"),
    ),
    (
        ("computer", "video-display", "network-workgroup"),
        "VNC", VncPage,
        tr("nav_hint_vnc"),
    ),
    (
        ("network-wired", "network-transmit-receive", "go-next", "go-jump", "mail-send", "network-workgroup"),
        "Traceroute", TraceroutePage,
        tr("nav_hint_traceroute"),
    ),
    (
        ("network-wired", "network-transmit-receive", "chronometer", "appointment-soon"),
        "MTR", MtrPage,
        tr("nav_hint_mtr"),
    ),
    (
        ("security-medium", "security-high", "firewall", "system-lock-screen", "changes-prevent", "dialog-warning"),
        "Firewall", FirewallPage,
        tr("nav_hint_firewall"),
    ),
    (
        ("network-transmit-receive", "modem", "network-wired", "go-down", "utilities-system-monitor", "appointment-soon"),
        "Speed Test", SpeedTestPage,
        tr("nav_hint_speedtest"),
    ),
    (
        ("network-transmit-receive", "network-wired", "utilities-system-monitor"),
        "Bandwidth", BandwidthPage,
        tr("nav_hint_bandwidth"),
    ),
    (
        ("system-shutdown", "system-reboot", "media-playback-start"),
        "Wake on LAN", WolPage,
        tr("nav_hint_wol"),
    ),
    (
        ("folder-remote", "document-send", "network-server", "folder-upload"),
        "File Transfer", FileTransferPage,
        tr("ft_nav_hint"),
    ),
    (
        ("network-workgroup", "computer", "network-wired"),
        "Topology", TopologyPage,
        tr("nav_hint_topology"),
    ),
    (
        ("system-search", "edit-find", "network-workgroup", "computer"),
        "Asset Inventory", AssetInventoryPage,
        tr("nav_hint_asset_inventory"),
    ),
]

class _NavList(QListWidget):
    """QListWidget that detects clicks on the ? badge and emits help_requested."""

    help_requested = Signal(int)   # row index
    _BADGE_W = 25                  # px from right edge that counts as badge zone

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        # QListWidget is a QAbstractScrollArea — mouse events hit the viewport,
        # not the widget itself, so we must filter at the viewport level.
        self.viewport().installEventFilter(self)

    def eventFilter(self, obj, event) -> bool:
        from PySide6.QtCore import QEvent
        if obj is self.viewport() and event.type() == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
                item = self.itemAt(event.pos())
                if item is not None:
                    rect = self.visualRect(self.indexFromItem(item))
                    if event.pos().x() >= rect.right() - self._BADGE_W:
                        self.help_requested.emit(self.row(item))
                        return True   # consume — don't also select the item
        return super().eventFilter(obj, event)


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

        # Status dot (left of ? badge) for watchlist alerts
        status = index.data(Qt.ItemDataRole.UserRole)
        if status in ("expired", "warning"):
            dot_color = QColor(239, 83, 80) if status == "expired" else QColor(255, 167, 38)
            dot_d = 7
            dot_x = r.right() - 40
            dot_y = r.top() + (r.height() - dot_d) // 2
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(dot_color)
            painter.drawEllipse(dot_x, dot_y, dot_d, dot_d)

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

        self._setup_palette()
        self._setup_export_menu()

    def _build_sidebar(self) -> QFrame:
        frame = QFrame()
        frame.setFixedWidth(190)
        frame.setFrameShape(QFrame.Shape.NoFrame)
        frame.setObjectName("sidebar")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Tools navigation (scrollable, fills available space) ──────────
        self._nav = _NavList()
        self._nav.setIconSize(QSize(20, 20))
        self._nav.setSpacing(2)
        self._nav.setFrameShape(QFrame.Shape.NoFrame)
        self._nav.setItemDelegate(_NavHintDelegate(self._nav))
        self._nav.currentRowChanged.connect(self._on_nav_changed)
        self._nav.help_requested.connect(self._on_help_requested)

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

        # Connect TLS watchlist status to sidebar indicator
        tls_row = next((i for i, (_, lbl, _, _) in enumerate(_TOOLS) if lbl == "TLS Inspector"), -1)
        if tls_row >= 0:
            tls_page = self._pages[tls_row]
            tls_page.watchlist_status_changed.connect(
                lambda status, row=tls_row: self._set_nav_status(row, status)
            )
            QTimer.singleShot(2000, tls_page.start_watchlist_check)

        # Settings page — index = len(_TOOLS)
        self._settings_page = SettingsPage()
        self._settings_page.language_changed.connect(self._on_language_changed)
        self._stack.addWidget(self._settings_page)

        # About page — index = len(_TOOLS) + 1
        self._about_page = AboutPage()
        self._stack.addWidget(self._about_page)

        # Help page — index = len(_TOOLS) + 2
        self._help_page = HelpPage()
        self._help_page.back_requested.connect(self._on_help_back)
        self._stack.addWidget(self._help_page)

        # Auto-connect source pages
        for page in self._pages:
            if hasattr(page, 'action_requested'):
                page.action_requested.connect(self._on_host_action)

        # Build routing table (requires all pages to be instantiated)
        self._setup_host_action_routes()

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

    def _on_help_requested(self, row: int) -> None:
        if 0 <= row < len(_TOOLS):
            label = _TOOLS[row][1]
            self._help_page.load(label)
            self._stack.setCurrentIndex(len(self._pages) + 2)

    def _on_help_back(self) -> None:
        # Return to whichever page was active before help
        row = self._nav.currentRow()
        if row >= 0:
            self._stack.setCurrentIndex(row)
        else:
            self._stack.setCurrentIndex(0)

    def _on_language_changed(self) -> None:
        self._settings_item.setText(tr("nav_settings"))
        self._about_item.setText(tr("nav_about"))

    def _setup_palette(self) -> None:
        labels = [label for _, label, _, _ in _TOOLS]
        self._palette = CommandPalette(labels, self.navigate_to, parent=self)
        QShortcut(QKeySequence("Ctrl+P"), self).activated.connect(self._open_palette)

    def _setup_export_menu(self) -> None:
        file_menu = self.menuBar().addMenu("File")
        export_action = file_menu.addAction("Export Network Report…")
        export_action.triggered.connect(self._on_export_report)

    def _on_export_report(self) -> None:
        from PySide6.QtWidgets import QMessageBox
        from nmlinux.export_manager import collect_snapshot, save_export
        from nmlinux.core.export_dialog import open_export_dialog

        filepath, fmt = open_export_dialog(self, "Export Network Report", "network-report")
        if not filepath:
            return
        data = collect_snapshot()
        error = save_export(data, fmt, filepath)
        if error:
            QMessageBox.warning(self, "Export Error", error)
        else:
            QMessageBox.information(self, "Export", f"Report saved to:\n{filepath}")

    def _set_nav_status(self, row: int, status: str) -> None:
        item = self._nav.item(row)
        if item:
            item.setData(Qt.ItemDataRole.UserRole, status)
            self._nav.viewport().update()

    def navigate_to(self, index: int) -> None:
        if 0 <= index < len(_TOOLS):
            self._nav.setCurrentRow(index)

    def _page_index(self, class_name: str) -> int:
        for i, page in enumerate(self._pages):
            if type(page).__name__ == class_name:
                return i
        raise ValueError(f"Page class not found: {class_name}")

    def _setup_host_action_routes(self) -> None:
        self._host_routes: dict[str, tuple[int, object]] = {
            ACT_PING:       (self._page_index('PingPage'),
                             lambda p, ip, h, _s: p.set_target(h or ip)),
            ACT_PORT_SCAN:  (self._page_index('PortScannerPage'),
                             lambda p, ip, h, _s: p.set_target(ip)),
            ACT_WHOIS:      (self._page_index('WhoisPage'),
                             lambda p, ip, h, _s: p.set_target(h or ip)),
            ACT_DNS:        (self._page_index('DnsPage'),
                             lambda p, ip, h, _s: p.set_target(h or ip)),
            ACT_TRACEROUTE: (self._page_index('TraceroutePage'),
                             lambda p, ip, h, _s: p.set_target(h or ip)),
            ACT_MTR:        (self._page_index('MtrPage'),
                             lambda p, ip, h, _s: p.set_target(h or ip)),
            ACT_SSH:        (self._page_index('SshPage'),
                             lambda p, ip, h, _s: p.set_target(ip, h)),
            ACT_RDP:        (self._page_index('RdpPage'),
                             lambda p, ip, h, _s: p.set_target(ip, h)),
            ACT_VNC:        (self._page_index('VncPage'),
                             lambda p, ip, h, _s: p.set_target(ip, h)),
            ACT_TOPOLOGY:   (self._page_index('TopologyPage'),
                             lambda p, ip, h, src: p.load_hosts(
                                 getattr(src, '_last_scan_hosts', []))),
            ACT_ASSET:      (self._page_index('AssetInventoryPage'),
                             lambda p, ip, h, src: p.prefill_hosts(
                                 getattr(src, '_last_scan_hosts', []))),
        }

    def _on_host_action(self, action: str, ip: str, host: str) -> None:
        if action not in self._host_routes:
            return
        idx, fn = self._host_routes[action]
        sender = self.sender()
        fn(self._pages[idx], ip, host, sender)
        self.navigate_to(idx)

    def _open_palette(self) -> None:
        self._palette.open_palette()
