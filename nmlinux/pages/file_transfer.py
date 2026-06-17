"""File Transfer Server — start/stop TFTP or HTTP server for network device config exchange."""

from __future__ import annotations

import datetime
import threading
from http.server import HTTPServer
from pathlib import Path

from PySide6.QtCore import Qt, QProcess, QThread, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QButtonGroup, QFileDialog, QFormLayout, QFrame, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QRadioButton,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from nmlinux.core.http_server import get_local_ips, make_handler
from nmlinux.core.i18n import tr
from nmlinux.core.theme import color_ok, color_err

_HELPER = Path(__file__).parent.parent / "core" / "tftp_helper.py"


# ── HTTP thread ───────────────────────────────────────────────────────────────

class _HttpThread(QThread):
    log_event = Signal(str, str, str, str, str, str)  # ts, dir, file, client, nbytes, status

    def __init__(self, root: Path, port: int) -> None:
        super().__init__()
        self._root   = root
        self._port   = port
        self._server: HTTPServer | None = None
        self._ready  = threading.Event()

    def run(self) -> None:
        def on_log(direction, filename, client_ip, nbytes, status):
            ts = datetime.datetime.now().strftime("%H:%M:%S")
            self.log_event.emit(ts, direction, filename, client_ip, str(nbytes), status)

        handler_cls  = make_handler(self._root, on_log)
        self._server = HTTPServer(("0.0.0.0", self._port), handler_cls)
        self._ready.set()
        self._server.serve_forever()

    def stop(self) -> None:
        self._ready.wait(timeout=5.0)
        if self._server:
            self._server.shutdown()
            self._server = None


# ── Page ─────────────────────────────────────────────────────────────────────

class FileTransferPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._http_thread:  _HttpThread | None = None
        self._tftp_process: QProcess    | None = None
        self._running = False
        self._build_ui()

    # ── Build UI ─────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        # ── Protocol selector ──────────────────────────────────────────────
        proto_row = QHBoxLayout()
        proto_row.setSpacing(24)
        self._rb_tftp = QRadioButton(tr("ft_proto_tftp"))
        self._rb_http = QRadioButton(tr("ft_proto_http"))
        self._rb_tftp.setChecked(True)
        self._rb_tftp.toggled.connect(self._on_proto_changed)
        bg = QButtonGroup(self)
        bg.addButton(self._rb_tftp)
        bg.addButton(self._rb_http)
        proto_row.addWidget(self._rb_tftp)
        proto_row.addWidget(self._rb_http)
        proto_row.addStretch()
        root.addLayout(proto_row)

        # ── Config form ────────────────────────────────────────────────────
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setSpacing(8)

        self._f_port = QLineEdit("69")
        self._f_port.setFixedWidth(80)
        form.addRow(tr("ft_lbl_port"), self._f_port)

        root_row = QHBoxLayout()
        root_row.setSpacing(6)
        self._f_root = QLineEdit(str(Path.home()))
        self._btn_browse = QPushButton(tr("ft_btn_browse"))
        self._btn_browse.setFixedWidth(100)
        self._btn_browse.clicked.connect(self._on_browse)
        root_row.addWidget(self._f_root, 1)
        root_row.addWidget(self._btn_browse)
        form.addRow(tr("ft_lbl_root"), root_row)
        root.addLayout(form)

        # ── Local IPs ──────────────────────────────────────────────────────
        ip_label = QLabel(tr("ft_lbl_local_ips"))
        ip_label.setStyleSheet("font-weight: bold;")
        root.addWidget(ip_label)

        self._ip_layout = QHBoxLayout()
        self._ip_layout.setSpacing(12)
        self._refresh_ips()
        root.addLayout(self._ip_layout)

        # ── Start / Stop / Root buttons ────────────────────────────────────
        btn_row = QHBoxLayout()
        self._btn_start = QPushButton(tr("ft_btn_start"))
        self._btn_start.setStyleSheet("font-weight: bold; padding: 8px 24px; font-size: 14px;")
        self._btn_start.clicked.connect(self._on_start)

        self._btn_stop = QPushButton(tr("ft_btn_stop"))
        self._btn_stop.setStyleSheet(
            f"font-weight: bold; padding: 8px 24px; font-size: 14px; color: {color_err()};"
        )
        self._btn_stop.setVisible(False)
        self._btn_stop.clicked.connect(self._on_stop)

        self._btn_start_root = QPushButton(tr("ft_btn_start_root"))
        self._btn_start_root.setVisible(False)
        self._btn_start_root.clicked.connect(self._on_start_root)

        btn_row.addWidget(self._btn_start)
        btn_row.addWidget(self._btn_stop)
        btn_row.addWidget(self._btn_start_root)
        btn_row.addStretch()
        root.addLayout(btn_row)

        # ── Status label ───────────────────────────────────────────────────
        self._lbl_status = QLabel(tr("ft_status_stopped"))
        self._lbl_status.setWordWrap(True)
        root.addWidget(self._lbl_status)

        # ── Transfer log ───────────────────────────────────────────────────
        log_hdr = QHBoxLayout()
        log_hdr.addWidget(QLabel("<b>Transfer log</b>"))
        log_hdr.addStretch()
        self._btn_clear = QPushButton(tr("ft_btn_clear_log"))
        self._btn_clear.setFixedWidth(80)
        self._btn_clear.clicked.connect(lambda: self._log_table.setRowCount(0))
        log_hdr.addWidget(self._btn_clear)
        root.addLayout(log_hdr)

        self._log_table = QTableWidget(0, 5)
        self._log_table.setHorizontalHeaderLabels([
            tr("ft_log_col_time"),
            tr("ft_log_col_file"),
            tr("ft_log_col_client"),
            tr("ft_log_col_dir"),
            tr("ft_log_col_size"),
        ])
        hdr = self._log_table.horizontalHeader()
        hdr.setSectionResizeMode(1, hdr.ResizeMode.Stretch)
        self._log_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._log_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._log_table.verticalHeader().setVisible(False)
        self._log_table.setFrameShape(QFrame.Shape.NoFrame)
        root.addWidget(self._log_table, 1)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _refresh_ips(self) -> None:
        while self._ip_layout.count():
            item = self._ip_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for ip in get_local_ips():
            btn = QPushButton(ip)
            btn.setToolTip("Click to copy")
            btn.setStyleSheet("font-family: monospace;")
            btn.clicked.connect(lambda _checked, _ip=ip: self._copy_ip(_ip))
            self._ip_layout.addWidget(btn)
        self._ip_layout.addStretch()

    def _copy_ip(self, ip: str) -> None:
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(ip)

    def _on_proto_changed(self) -> None:
        if self._rb_tftp.isChecked():
            self._f_port.setText("69")
        else:
            self._f_port.setText("8080")

    def _on_browse(self) -> None:
        path = QFileDialog.getExistingDirectory(self, tr("ft_lbl_root"), self._f_root.text())
        if path:
            self._f_root.setText(path)

    def _proto(self) -> str:
        return "TFTP" if self._rb_tftp.isChecked() else "HTTP"

    def _set_running(self, running: bool) -> None:
        self._running = running
        self._btn_start.setVisible(not running)
        self._btn_stop.setVisible(running)
        self._rb_tftp.setEnabled(not running)
        self._rb_http.setEnabled(not running)
        self._f_port.setReadOnly(running)
        self._f_root.setReadOnly(running)
        self._btn_browse.setEnabled(not running)
        if running:
            port = self._f_port.text()
            rdir = self._f_root.text()
            key  = "ft_status_running_tftp" if self._proto() == "TFTP" else "ft_status_running_http"
            self._lbl_status.setStyleSheet(f"color: {color_ok()};")
            self._lbl_status.setText(tr(key, port=port, root=rdir))
        else:
            self._lbl_status.setStyleSheet("")
            self._lbl_status.setText(tr("ft_status_stopped"))

    def _add_log_row(self, ts: str, direction: str, filename: str,
                     client: str, nbytes: str, status: str) -> None:
        row = self._log_table.rowCount()
        self._log_table.insertRow(row)
        for col, val in enumerate([ts, filename, client, direction, nbytes]):
            item = QTableWidgetItem(str(val))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._log_table.setItem(row, col, item)
        if status not in ("OK",):
            for col in range(5):
                item = self._log_table.item(row, col)
                if item:
                    item.setForeground(QColor(color_err()))
        self._log_table.scrollToBottom()

    # ── Start / Stop ──────────────────────────────────────────────────────────

    def _on_start(self) -> None:
        self._btn_start_root.setVisible(False)
        if self._proto() == "TFTP":
            self._start_tftp(as_root=False)
        else:
            self._start_http()

    def _on_start_root(self) -> None:
        self._btn_start_root.setVisible(False)
        self._start_tftp(as_root=True)

    def _start_tftp(self, *, as_root: bool) -> None:
        port_str = self._f_port.text().strip() or "69"
        try:
            port = int(port_str)
        except ValueError:
            self._lbl_status.setStyleSheet(f"color: {color_err()};")
            self._lbl_status.setText(f"Invalid port: {port_str!r}")
            return
        rdir = self._f_root.text().strip() or str(Path.home())

        helper_args = [str(_HELPER), "--port", str(port), "--root", rdir]
        if as_root:
            prog = "pkexec"
            args = ["python3"] + helper_args
        else:
            prog = "python3"
            args = helper_args

        self._tftp_process = QProcess(self)
        self._tftp_process.readyReadStandardOutput.connect(self._on_tftp_stdout)
        self._tftp_process.finished.connect(self._on_tftp_finished)
        self._tftp_process.start(prog, args)
        self._set_running(True)

    def _on_tftp_stdout(self) -> None:
        while self._tftp_process and self._tftp_process.canReadLine():
            raw = self._tftp_process.readLine().data().decode(errors="replace").strip()
            if raw == "READY":
                pass
            elif raw == "EPERM":
                self._set_running(False)
                self._lbl_status.setStyleSheet(f"color: {color_err()};")
                self._lbl_status.setText(tr("ft_err_perm_denied"))
                self._btn_start_root.setVisible(True)
            elif raw.startswith("ERROR|"):
                self._set_running(False)
                self._lbl_status.setStyleSheet(f"color: {color_err()};")
                self._lbl_status.setText(raw[6:])
            elif raw.startswith("TFTP|"):
                parts = raw.split("|")
                if len(parts) == 7:
                    _, ts, direction, filename, client, nbytes, status = parts
                    self._add_log_row(ts, direction, filename, client, nbytes, status)

    def _on_tftp_finished(self, exit_code: int, _exit_status) -> None:
        if self._running:
            self._set_running(False)

    def _start_http(self) -> None:
        port_str = self._f_port.text().strip() or "8080"
        try:
            port = int(port_str)
        except ValueError:
            port = 8080
        rdir = Path(self._f_root.text().strip() or str(Path.home()))
        self._http_thread = _HttpThread(rdir, port)
        self._http_thread.log_event.connect(self._add_log_row)
        self._http_thread.start()
        self._set_running(True)

    def _on_stop(self) -> None:
        if self._tftp_process:
            self._tftp_process.terminate()
            if not self._tftp_process.waitForFinished(2000):
                self._tftp_process.kill()
                self._tftp_process.waitForFinished(500)
            self._tftp_process = None
        if self._http_thread:
            self._http_thread.stop()
            if not self._http_thread.wait(3000):
                self._http_thread.terminate()
            self._http_thread = None
        self._set_running(False)

    def showEvent(self, event) -> None:  # noqa: N802
        self._refresh_ips()
        super().showEvent(event)

    def hideEvent(self, event) -> None:  # noqa: N802
        if self._running:
            self._on_stop()
        super().hideEvent(event)

    def closeEvent(self, event) -> None:  # noqa: N802
        if self._running:
            self._on_stop()
        super().closeEvent(event)
