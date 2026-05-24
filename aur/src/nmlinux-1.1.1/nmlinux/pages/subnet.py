import ipaddress

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton,
    QGroupBox, QGridLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox,
)
from PySide6.QtCore import Qt

from nmlinux.core.i18n import tr


class SubnetPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel(tr("subnet_title"))
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        row = QHBoxLayout()
        self._input = QLineEdit()
        self._input.setPlaceholderText(tr("subnet_placeholder"))
        self._input.returnPressed.connect(self._calculate)
        btn = QPushButton(tr("subnet_calc_btn"))
        btn.setDefault(True)
        btn.clicked.connect(self._calculate)
        row.addWidget(self._input, 1)
        row.addWidget(btn)
        layout.addLayout(row)

        self._grp_info = QGroupBox(tr("subnet_info_box"))
        grid = QGridLayout(self._grp_info)
        grid.setColumnStretch(1, 1)

        self._fields: dict[str, QLabel] = {}
        label_keys = [
            ("subnet_lbl_network",  "network"),
            ("subnet_lbl_netmask",  "netmask"),
            ("subnet_lbl_wildcard", "wildcard"),
            ("subnet_lbl_broadcast","broadcast"),
            ("subnet_lbl_prefix",   "prefix"),
            ("subnet_lbl_range",    "host_range"),
            ("subnet_lbl_usable",   "usable"),
            ("subnet_lbl_type",     "type_"),
            ("subnet_lbl_class",    "class_"),
        ]
        for r, (lbl_key, key) in enumerate(label_keys):
            grid.addWidget(QLabel(tr(lbl_key) + " :"), r, 0, Qt.AlignmentFlag.AlignTop)
            val = QLabel("—")
            val.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            val.setWordWrap(True)
            self._fields[key] = val
            grid.addWidget(val, r, 1)

        self._grp_info.setVisible(False)
        layout.addWidget(self._grp_info)

        self._grp_hosts = QGroupBox(tr("subnet_hosts_box"))
        vbox = QVBoxLayout(self._grp_hosts)
        self._table = QTableWidget(0, 1)
        self._table.setHorizontalHeaderLabels([tr("subnet_col_ip")])
        self._table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        vbox.addWidget(self._table)

        self._grp_hosts.setVisible(False)
        layout.addWidget(self._grp_hosts, 10)
        layout.addStretch(1)

    def _calculate(self) -> None:
        text = self._input.text().strip()
        if not text:
            return

        try:
            net = ipaddress.ip_network(text, strict=False)
        except ValueError as exc:
            QMessageBox.warning(self, tr("subnet_invalid_title"), str(exc))
            return

        n = net.num_addresses
        usable = max(0, n - 2) if net.version == 4 and net.prefixlen < 31 else n

        first_host = net.network_address + (1 if usable < n else 0)
        last_host  = net.broadcast_address - (1 if usable < n else 0)

        self._fields["network"].setText(str(net.network_address))
        self._fields["netmask"].setText(str(net.netmask))
        self._fields["wildcard"].setText(str(net.hostmask))
        self._fields["broadcast"].setText(
            str(net.broadcast_address) if net.version == 4 else "N/A (IPv6)"
        )
        self._fields["prefix"].setText(f"/{net.prefixlen}")
        self._fields["host_range"].setText(
            f"{first_host}  →  {last_host}" if usable > 0 else tr("common_na")
        )
        self._fields["usable"].setText(f"{usable:,}".replace(",", " "))
        self._fields["type_"].setText(self._net_type(net))
        self._fields["class_"].setText(self._net_class(net))

        self._grp_info.setVisible(True)

        self._table.setRowCount(0)
        hosts = list(net.hosts()) if usable <= 4096 else []
        cap = 4096

        if usable > cap:
            for i, h in enumerate(net.hosts()):
                if i >= cap:
                    break
                self._table.insertRow(i)
                self._table.setItem(i, 0, QTableWidgetItem(str(h)))
            extra = QTableWidgetItem(tr("subnet_more_hosts", n=usable - cap))
            r = self._table.rowCount()
            self._table.insertRow(r)
            self._table.setItem(r, 0, extra)
        else:
            for i, h in enumerate(hosts):
                self._table.insertRow(i)
                self._table.setItem(i, 0, QTableWidgetItem(str(h)))

        self._grp_hosts.setVisible(True)

    @staticmethod
    def _net_type(net: ipaddress.IPv4Network | ipaddress.IPv6Network) -> str:
        if net.is_loopback:   return "Loopback"
        if net.is_multicast:  return "Multicast"
        if net.is_link_local: return "Link-local"
        if net.is_private:    return tr("subnet_type_private")
        return tr("subnet_type_public")

    @staticmethod
    def _net_class(net: ipaddress.IPv4Network | ipaddress.IPv6Network) -> str:
        if net.version == 6:
            return "IPv6"
        first = int(net.network_address) >> 24
        if first < 128: return "A"
        if first < 192: return "B"
        if first < 224: return "C"
        if first < 240: return tr("subnet_class_multi")
        return tr("subnet_class_reserved")
