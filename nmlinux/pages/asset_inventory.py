from __future__ import annotations

import csv
import json

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QGroupBox, QFormLayout, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QProgressBar, QFileDialog,
    QScrollArea,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from nmlinux.core.i18n import tr
from nmlinux.core.asset_collectors import AssetScanWorker, _HAS_WINRM, _CMD_SSHPASS

_COL_IP, _COL_HOST, _COL_PLATFORM, _COL_OS, _COL_CPU, _COL_RAM, _COL_DISK, _COL_UPTIME, _COL_METHOD = range(9)


def _item(text: str, color: QColor | None = None) -> QTableWidgetItem:
    it = QTableWidgetItem(str(text) if text else '—')
    it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)
    if color:
        it.setForeground(color)
    return it


class AssetInventoryPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._worker: AssetScanWorker | None = None
        self._build_ui()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        # ── Toolbar ───────────────────────────────────────────────────────────
        bar = QHBoxLayout()
        bar.addWidget(QLabel(tr("inv_target_label")))
        self._cidr = QLineEdit()
        self._cidr.setPlaceholderText(tr("inv_target_ph"))
        self._cidr.returnPressed.connect(self._on_scan)
        self._btn_scan  = QPushButton(tr("inv_scan_btn"))
        self._btn_scan.setDefault(True)
        self._btn_scan.clicked.connect(self._on_scan)
        self._btn_stop  = QPushButton(tr("inv_stop_btn"))
        self._btn_stop.clicked.connect(self._on_stop)
        self._btn_stop.setEnabled(False)
        self._btn_clear = QPushButton(tr("inv_clear_btn"))
        self._btn_clear.clicked.connect(self._clear_results)
        bar.addWidget(self._cidr, 1)
        bar.addWidget(self._btn_scan)
        bar.addWidget(self._btn_stop)
        bar.addWidget(self._btn_clear)
        root.addLayout(bar)

        # ── Credentials ───────────────────────────────────────────────────────
        creds_scroll = QScrollArea()
        creds_scroll.setWidgetResizable(True)
        creds_scroll.setFrameShape(creds_scroll.Shape.NoFrame)
        creds_scroll.setFixedHeight(155)
        creds_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        creds_w = QWidget()
        creds_h = QHBoxLayout(creds_w)
        creds_h.setContentsMargins(0, 0, 0, 0)
        creds_h.setSpacing(8)

        # SSH
        ssh_box  = QGroupBox(tr("inv_creds_ssh_group"))
        ssh_form = QFormLayout(ssh_box)
        ssh_form.setHorizontalSpacing(8)
        ssh_form.setVerticalSpacing(4)
        self._ssh_user = QLineEdit()
        self._ssh_user.setPlaceholderText("user")
        self._ssh_pass = QLineEdit()
        self._ssh_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self._ssh_key  = QLineEdit()
        self._ssh_key.setPlaceholderText("~/.ssh/id_ed25519")
        if not _CMD_SSHPASS:
            self._ssh_pass.setEnabled(False)
            self._ssh_pass.setPlaceholderText(tr("inv_warn_sshpass"))
        ssh_form.addRow(tr("inv_user_label") + ":", self._ssh_user)
        ssh_form.addRow(tr("inv_pass_label") + ":", self._ssh_pass)
        ssh_form.addRow(tr("inv_key_label")  + ":", self._ssh_key)
        creds_h.addWidget(ssh_box, 1)

        # WinRM
        winrm_box  = QGroupBox(tr("inv_creds_winrm_group"))
        winrm_form = QFormLayout(winrm_box)
        winrm_form.setHorizontalSpacing(8)
        winrm_form.setVerticalSpacing(4)
        self._winrm_user   = QLineEdit()
        self._winrm_pass   = QLineEdit()
        self._winrm_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self._winrm_domain = QLineEdit()
        if not _HAS_WINRM:
            for w in (self._winrm_user, self._winrm_pass, self._winrm_domain):
                w.setEnabled(False)
                w.setPlaceholderText(tr("inv_warn_pywinrm"))
        winrm_form.addRow(tr("inv_user_label")   + ":", self._winrm_user)
        winrm_form.addRow(tr("inv_pass_label")   + ":", self._winrm_pass)
        winrm_form.addRow(tr("inv_domain_label") + ":", self._winrm_domain)
        creds_h.addWidget(winrm_box, 1)

        # SNMP
        snmp_box  = QGroupBox(tr("inv_creds_snmp_group"))
        snmp_form = QFormLayout(snmp_box)
        snmp_form.setHorizontalSpacing(8)
        snmp_form.setVerticalSpacing(4)
        self._snmp_version    = QComboBox()
        self._snmp_version.addItems(['v2c', 'v1', 'v3'])
        self._snmp_version.currentTextChanged.connect(self._on_snmp_version_changed)
        self._snmp_community  = QLineEdit()
        self._snmp_community.setText('public')
        self._snmp_v3_user    = QLineEdit()
        self._snmp_v3_auth    = QLineEdit()
        self._snmp_v3_auth.setEchoMode(QLineEdit.EchoMode.Password)
        self._snmp_v3_priv    = QLineEdit()
        self._snmp_v3_priv.setEchoMode(QLineEdit.EchoMode.Password)
        self._snmp_auth_proto = QComboBox()
        self._snmp_auth_proto.addItems(['SHA', 'MD5'])
        self._snmp_priv_proto = QComboBox()
        self._snmp_priv_proto.addItems(['AES', 'DES'])
        snmp_form.addRow(tr("inv_snmp_version") + ":", self._snmp_version)
        snmp_form.addRow(tr("inv_community")    + ":", self._snmp_community)
        self._snmp_v3_widgets: list[QWidget] = []
        for label, widget in [
            (tr("inv_v3_user")      + ":", self._snmp_v3_user),
            (tr("inv_v3_auth_pass") + ":", self._snmp_v3_auth),
            (tr("inv_v3_priv_pass") + ":", self._snmp_v3_priv),
            ("Auth proto:",               self._snmp_auth_proto),
            ("Priv proto:",               self._snmp_priv_proto),
        ]:
            snmp_form.addRow(label, widget)
            self._snmp_v3_widgets.append(widget)
        self._on_snmp_version_changed('v2c')
        creds_h.addWidget(snmp_box, 1)

        creds_scroll.setWidget(creds_w)
        root.addWidget(creds_scroll)

        # ── Progress ──────────────────────────────────────────────────────────
        self._progress = QProgressBar()
        self._progress.setVisible(False)
        self._lbl_status = QLabel("")
        self._lbl_status.setStyleSheet("color: palette(mid);")
        prog_row = QHBoxLayout()
        prog_row.addWidget(self._progress, 1)
        prog_row.addWidget(self._lbl_status)
        root.addLayout(prog_row)

        # ── Table ─────────────────────────────────────────────────────────────
        self._table = QTableWidget(0, 9)
        self._table.setHorizontalHeaderLabels([
            tr("inv_col_ip"), tr("inv_col_hostname"), tr("inv_col_platform"),
            tr("inv_col_os"), tr("inv_col_cpu"), tr("inv_col_ram"),
            tr("inv_col_disk"), tr("inv_col_uptime"), tr("inv_col_method"),
        ])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.setSortingEnabled(True)
        root.addWidget(self._table, 1)

        # ── Export ────────────────────────────────────────────────────────────
        export_row = QHBoxLayout()
        export_row.addStretch(1)
        self._btn_json = QPushButton(tr("inv_export_json"))
        self._btn_csv  = QPushButton(tr("inv_export_csv"))
        self._btn_md   = QPushButton(tr("inv_export_md"))
        for btn in (self._btn_json, self._btn_csv, self._btn_md):
            btn.setVisible(False)
            export_row.addWidget(btn)
        self._btn_json.clicked.connect(lambda: self._export('json'))
        self._btn_csv.clicked.connect(lambda: self._export('csv'))
        self._btn_md.clicked.connect(lambda: self._export('md'))
        root.addLayout(export_row)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _on_snmp_version_changed(self, val: str) -> None:
        is_v3 = val == 'v3'
        self._snmp_community.setVisible(not is_v3)
        for w in self._snmp_v3_widgets:
            w.setVisible(is_v3)

    def _clear_results(self) -> None:
        self._table.setRowCount(0)
        self._lbl_status.setText("")
        for btn in (self._btn_json, self._btn_csv, self._btn_md):
            btn.setVisible(False)

    def _get_ssh_creds(self) -> dict:
        u = self._ssh_user.text().strip()
        if not u:
            return {}
        return {'user': u, 'password': self._ssh_pass.text(), 'key': self._ssh_key.text().strip()}

    def _get_winrm_creds(self) -> dict:
        u = self._winrm_user.text().strip()
        if not u:
            return {}
        return {'user': u, 'password': self._winrm_pass.text(), 'domain': self._winrm_domain.text().strip()}

    def _get_snmp_creds(self) -> dict:
        ver = self._snmp_version.currentText().lstrip('v')
        if ver in ('1', '2c'):
            return {'version': ver, 'community': self._snmp_community.text().strip() or 'public'}
        return {
            'version':    '3',
            'user':       self._snmp_v3_user.text().strip(),
            'auth_pass':  self._snmp_v3_auth.text(),
            'priv_pass':  self._snmp_v3_priv.text(),
            'auth_proto': self._snmp_auth_proto.currentText(),
            'priv_proto': self._snmp_priv_proto.currentText(),
        }

    # ── Scan ──────────────────────────────────────────────────────────────────

    def _on_scan(self) -> None:
        cidr = self._cidr.text().strip()
        if not cidr:
            return
        if self._worker and self._worker.isRunning():
            return

        self._clear_results()
        self._btn_scan.setEnabled(False)
        self._btn_stop.setEnabled(True)
        self._progress.setValue(0)
        self._progress.setVisible(True)
        self._lbl_status.setText(tr("inv_scanning"))

        ssh_creds   = self._get_ssh_creds()
        winrm_creds = self._get_winrm_creds()
        snmp_creds  = self._get_snmp_creds()

        self._worker = AssetScanWorker(cidr, ssh_creds, winrm_creds, snmp_creds)
        del ssh_creds, winrm_creds, snmp_creds

        self._worker.host_found.connect(self._on_host)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished_.connect(self._on_finished)
        self._worker.start()

    def _on_stop(self) -> None:
        if self._worker:
            self._worker.stop()

    def _on_progress(self, done: int, total: int) -> None:
        self._progress.setMaximum(total)
        self._progress.setValue(done)
        self._lbl_status.setText(f"{done}/{total}")

    def _on_host(self, asset: dict) -> None:
        self._table.setSortingEnabled(False)
        row = self._table.rowCount()
        self._table.insertRow(row)

        method = asset.get('method', '?')
        error  = asset.get('error', '')

        color_map = {'SSH': QColor('#60a5fa'), 'WinRM': QColor('#a78bfa'), 'SNMP': QColor('#34d399')}
        c_method = color_map.get(method)

        self._table.setItem(row, _COL_IP,       _item(asset.get('ip', '')))
        self._table.setItem(row, _COL_HOST,     _item(asset.get('hostname', '')))
        self._table.setItem(row, _COL_PLATFORM, _item(asset.get('platform', '?')))
        self._table.setItem(row, _COL_OS,       _item(error or asset.get('os', '')))
        self._table.setItem(row, _COL_CPU,      _item(asset.get('cpu', '')))
        self._table.setItem(row, _COL_RAM,      _item(asset.get('ram', '')))
        self._table.setItem(row, _COL_DISK,     _item(asset.get('disk', '')))
        self._table.setItem(row, _COL_UPTIME,   _item(asset.get('uptime', '')))
        self._table.setItem(row, _COL_METHOD,   _item(method, c_method))
        self._table.setSortingEnabled(True)

    def _on_finished(self) -> None:
        self._btn_scan.setEnabled(True)
        self._btn_stop.setEnabled(False)
        self._progress.setVisible(False)
        n = self._table.rowCount()
        if n:
            self._lbl_status.setText(f"{n} host{'s' if n != 1 else ''} found")
            for btn in (self._btn_json, self._btn_csv, self._btn_md):
                btn.setVisible(True)
        else:
            self._lbl_status.setText(tr("inv_no_results"))

    # ── Export (manual only) ──────────────────────────────────────────────────

    def _collect_data(self) -> list[dict]:
        headers = ['IP', 'Hostname', 'Platform', 'OS', 'CPU', 'RAM', 'Disk', 'Uptime', 'Method']
        rows = []
        for r in range(self._table.rowCount()):
            rows.append({
                h: (self._table.item(r, c).text() if self._table.item(r, c) else '')
                for c, h in enumerate(headers)
            })
        return rows

    def _export(self, fmt: str) -> None:
        filters = {'json': "JSON (*.json)", 'csv': "CSV (*.csv)", 'md': "Markdown (*.md)"}
        path, _ = QFileDialog.getSaveFileName(self, "Export", 'assets', filters[fmt])
        if not path:
            return
        data = self._collect_data()
        if not data:
            return
        if fmt == 'json':
            with open(path, 'w') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        elif fmt == 'csv':
            with open(path, 'w', newline='') as f:
                w = csv.DictWriter(f, fieldnames=list(data[0].keys()))
                w.writeheader()
                w.writerows(data)
        elif fmt == 'md':
            hdrs  = list(data[0].keys())
            lines = ['| ' + ' | '.join(hdrs) + ' |', '|' + '---|' * len(hdrs)]
            for row in data:
                lines.append('| ' + ' | '.join(str(row[h]) for h in hdrs) + ' |')
            with open(path, 'w') as f:
                f.write('\n'.join(lines) + '\n')
