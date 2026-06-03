from __future__ import annotations

import re
import subprocess

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QAbstractItemView, QFrame, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QPushButton, QTabWidget,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from nmlinux.core.cli_bar import get_cli_bar
from nmlinux.core.i18n import tr

# ── Workers ───────────────────────────────────────────────────────────────────

class _SmbWorker(QThread):
    result = Signal(list)   # [(name, type, comment), …]
    error  = Signal(str)

    def __init__(self, host: str, user: str, password: str) -> None:
        super().__init__()
        self._host     = host
        self._user     = user
        self._password = password

    def run(self) -> None:
        try:
            cmd = ["smbclient", "-L", self._host, "-N", "--no-pass"]
            if self._user:
                cmd = ["smbclient", "-L", self._host,
                       "-U", f"{self._user}%{self._password}"]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            output = proc.stdout + proc.stderr

            shares = []
            in_shares = False
            for line in output.splitlines():
                if re.match(r"\s+Sharename\s+Type\s+Comment", line):
                    in_shares = True
                    continue
                if in_shares:
                    if not line.strip() or re.match(r"\s+-+", line):
                        continue
                    if re.match(r"\s+Server\s+Comment", line):
                        break
                    m = re.match(r"\s+(\S+)\s+(Disk|IPC\$?|Printer|Special)\s*(.*)", line)
                    if m:
                        shares.append((m.group(1), m.group(2), m.group(3).strip()))

            if not shares and proc.returncode != 0:
                self.error.emit(tr("smb_err_failed", msg=proc.stderr.strip()[:120]))
                return
            self.result.emit(shares)
        except FileNotFoundError:
            self.error.emit(tr("smb_err_not_found"))
        except subprocess.TimeoutExpired:
            self.error.emit(tr("smb_err_timeout"))
        except Exception as exc:
            self.error.emit(str(exc))


class _NfsWorker(QThread):
    result = Signal(list)   # [(path, access), …]
    error  = Signal(str)

    def __init__(self, host: str) -> None:
        super().__init__()
        self._host = host

    def run(self) -> None:
        try:
            proc = subprocess.run(
                ["showmount", "-e", "--no-headers", self._host],
                capture_output=True, text=True, timeout=10,
            )
            exports = []
            for line in proc.stdout.splitlines():
                m = re.match(r"^(/\S+)\s+(.*)", line.strip())
                if m:
                    exports.append((m.group(1), m.group(2).strip()))

            if not exports and proc.returncode != 0:
                self.error.emit(tr("nfs_err_failed", msg=proc.stderr.strip()[:120]))
                return
            self.result.emit(exports)
        except FileNotFoundError:
            self.error.emit(tr("nfs_err_not_found"))
        except subprocess.TimeoutExpired:
            self.error.emit(tr("nfs_err_timeout"))
        except Exception as exc:
            self.error.emit(str(exc))


# ── Page ──────────────────────────────────────────────────────────────────────

class SmbNfsPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._worker: QThread | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 8)
        root.setSpacing(8)

        # ── Toolbar ───────────────────────────────────────────────────────
        bar = QHBoxLayout()
        self._host_edit = QLineEdit()
        self._host_edit.setPlaceholderText(tr("smb_host_placeholder"))
        self._host_edit.returnPressed.connect(self._start)

        self._btn_scan = QPushButton(tr("smb_btn_scan"))
        self._btn_scan.setFixedWidth(90)
        self._btn_scan.clicked.connect(self._start)

        self._btn_stop = QPushButton(tr("smb_btn_stop"))
        self._btn_stop.setFixedWidth(70)
        self._btn_stop.setEnabled(False)
        self._btn_stop.clicked.connect(self._stop)

        bar.addWidget(self._host_edit, 1)
        bar.addWidget(self._btn_scan)
        bar.addWidget(self._btn_stop)
        root.addLayout(bar)

        # ── Tabs ──────────────────────────────────────────────────────────
        self._tabs = QTabWidget()
        self._smb_tab = self._build_smb_tab()
        self._nfs_tab = self._build_nfs_tab()
        self._tabs.addTab(self._smb_tab, "SMB / Samba")
        self._tabs.addTab(self._nfs_tab, "NFS")
        root.addWidget(self._tabs, 1)

        # ── Status ────────────────────────────────────────────────────────
        self._status = QLabel("")
        self._status.setStyleSheet("font-size: 12px; color: gray;")
        root.addWidget(self._status)

    def _build_smb_tab(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 8, 0, 0)

        # Optional credentials
        cred = QHBoxLayout()
        cred.addWidget(QLabel(tr("smb_lbl_user")))
        self._user_edit = QLineEdit()
        self._user_edit.setPlaceholderText(tr("smb_user_placeholder"))
        self._user_edit.setFixedWidth(140)
        cred.addWidget(self._user_edit)
        cred.addWidget(QLabel(tr("smb_lbl_pass")))
        self._pass_edit = QLineEdit()
        self._pass_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._pass_edit.setFixedWidth(140)
        cred.addWidget(self._pass_edit)
        cred.addStretch(1)
        note = QLabel(tr("smb_anon_note"))
        note.setStyleSheet("font-size: 11px; color: gray;")
        cred.addWidget(note)
        v.addLayout(cred)

        self._smb_table = self._make_table(
            [tr("smb_col_name"), tr("smb_col_type"), tr("smb_col_comment")]
        )
        v.addWidget(self._smb_table, 1)
        return w

    def _build_nfs_tab(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 8, 0, 0)
        self._nfs_table = self._make_table(
            [tr("nfs_col_path"), tr("nfs_col_access")]
        )
        v.addWidget(self._nfs_table, 1)
        return w

    @staticmethod
    def _make_table(headers: list[str]) -> QTableWidget:
        t = QTableWidget(0, len(headers))
        t.setHorizontalHeaderLabels(headers)
        t.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, len(headers)):
            t.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        t.setAlternatingRowColors(True)
        t.verticalHeader().setVisible(False)
        t.setFrameShape(QFrame.Shape.NoFrame)
        return t

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._update_cli()

    def _update_cli(self) -> None:
        h = self._host_edit.text().strip() or "<host>"
        cli = get_cli_bar()
        if not cli:
            return
        if self._tabs.currentIndex() == 0:
            cli.set_cmd(f"smbclient -L {h} -N")
        else:
            cli.set_cmd(f"showmount -e {h}")

    def _start(self) -> None:
        host = self._host_edit.text().strip()
        if not host:
            return
        self._btn_scan.setEnabled(False)
        self._btn_stop.setEnabled(True)
        self._status.setText(tr("smb_scanning"))

        if self._tabs.currentIndex() == 0:
            self._smb_table.setRowCount(0)
            get_cli_bar() and get_cli_bar().set_cmd(
                f"smbclient -L {host} -N"
            )
            self._worker = _SmbWorker(
                host,
                self._user_edit.text().strip(),
                self._pass_edit.text(),
            )
            self._worker.result.connect(self._on_smb_result)
            self._worker.error.connect(self._on_error)
        else:
            self._nfs_table.setRowCount(0)
            get_cli_bar() and get_cli_bar().set_cmd(
                f"showmount -e {host}"
            )
            self._worker = _NfsWorker(host)
            self._worker.result.connect(self._on_nfs_result)
            self._worker.error.connect(self._on_error)

        self._worker.finished.connect(self._on_done)
        self._worker.start()

    def _stop(self) -> None:
        if self._worker and self._worker.isRunning():
            self._worker.terminate()
        self._on_done()

    def _on_done(self) -> None:
        self._btn_scan.setEnabled(True)
        self._btn_stop.setEnabled(False)

    def _on_error(self, msg: str) -> None:
        self._status.setText(msg)
        self._status.setStyleSheet("font-size: 12px; color: #f38ba8;")

    def _on_smb_result(self, shares: list) -> None:
        self._status.setText(tr("smb_found", n=len(shares)))
        self._status.setStyleSheet("font-size: 12px; color: gray;")
        t = self._smb_table
        t.setRowCount(len(shares))
        for row, (name, stype, comment) in enumerate(shares):
            t.setItem(row, 0, QTableWidgetItem(name))
            t.setItem(row, 1, QTableWidgetItem(stype))
            t.setItem(row, 2, QTableWidgetItem(comment))

    def _on_nfs_result(self, exports: list) -> None:
        self._status.setText(tr("nfs_found", n=len(exports)))
        self._status.setStyleSheet("font-size: 12px; color: gray;")
        t = self._nfs_table
        t.setRowCount(len(exports))
        for row, (path, access) in enumerate(exports):
            t.setItem(row, 0, QTableWidgetItem(path))
            t.setItem(row, 1, QTableWidgetItem(access))
