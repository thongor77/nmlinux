from __future__ import annotations

import ipaddress
import re
import socket
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QSpinBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QProgressBar, QFileDialog, QMessageBox,
)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt, QThread, Signal

from nmlinux.core.i18n import tr


_C_DOT, _C_IP, _C_HOST, _C_RTT = range(4)
_GREEN = QColor("#a6e3a1")


class ScanWorker(QThread):
    found    = Signal(str, str, float)
    progress = Signal(int, int)
    finished = Signal()

    def __init__(self, hosts: list[str], timeout: int, n_threads: int) -> None:
        super().__init__()
        self._hosts     = hosts
        self._timeout   = timeout
        self._n_threads = n_threads
        self._cancelled = False

    def run(self) -> None:
        total = len(self._hosts)
        done  = 0
        with ThreadPoolExecutor(max_workers=self._n_threads) as pool:
            futures = {pool.submit(self._ping_one, ip): ip for ip in self._hosts}
            for future in as_completed(futures):
                if self._cancelled:
                    for f in futures:
                        f.cancel()
                    break
                ip = futures[future]
                try:
                    alive, rtt, hostname = future.result()
                except Exception:
                    alive, rtt, hostname = False, -1.0, ""
                done += 1
                self.progress.emit(done, total)
                if alive:
                    self.found.emit(ip, hostname, rtt)
        self.finished.emit()

    def _ping_one(self, ip: str) -> tuple[bool, float, str]:
        try:
            proc = subprocess.run(
                ['ping', '-c', '1', '-W', str(self._timeout), ip],
                capture_output=True, text=True, timeout=self._timeout + 2,
            )
            if proc.returncode == 0:
                m = re.search(r'time=(\d+\.?\d*)', proc.stdout)
                rtt = float(m.group(1)) if m else 0.0
                try:
                    hostname = socket.gethostbyaddr(ip)[0]
                except Exception:
                    hostname = ""
                return True, rtt, hostname
        except Exception:
            pass
        return False, -1.0, ""

    def cancel(self) -> None:
        self._cancelled = True


def _parse_range(text: str) -> list[str] | str:
    text = text.strip()

    try:
        net   = ipaddress.ip_network(text, strict=False)
        hosts = list(net.hosts()) or [net.network_address]
        if len(hosts) > 65536:
            return tr("ipscan_err_too_large", n=len(hosts))
        return [str(h) for h in hosts]
    except ValueError:
        pass

    if '-' in text:
        start_s, _, end_s = text.partition('-')
        start_s, end_s = start_s.strip(), end_s.strip()
        try:
            start = ipaddress.ip_address(start_s)
            try:
                end = ipaddress.ip_address(end_s)
            except ValueError:
                prefix = '.'.join(start_s.split('.')[:3])
                end = ipaddress.ip_address(f"{prefix}.{end_s}")
            if end < start:
                return tr("ipscan_err_end_lt")
            count = int(end) - int(start) + 1
            if count > 65536:
                return tr("ipscan_err_too_large", n=count)
            return [str(ipaddress.ip_address(int(start) + i)) for i in range(count)]
        except ValueError:
            pass

    return tr("ipscan_err_format")


class IpScannerPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._worker: ScanWorker | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel(tr("ipscan_title"))
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        bar = QHBoxLayout()

        self._input = QLineEdit()
        self._input.setPlaceholderText(
            "192.168.1.0/24   ou   192.168.1.1-254   ou   10.0.0.1-10.0.0.50"
        )
        self._input.returnPressed.connect(self._on_scan)

        self._timeout_sb = QSpinBox()
        self._timeout_sb.setRange(1, 10)
        self._timeout_sb.setValue(1)
        self._timeout_sb.setSuffix(" s")
        self._timeout_sb.setFixedWidth(64)

        self._btn = QPushButton(tr("ipscan_scan_btn"))
        self._btn.setDefault(True)
        self._btn.clicked.connect(self._on_scan)

        bar.addWidget(self._input, 1)
        bar.addWidget(QLabel(tr("ipscan_timeout_lbl")))
        bar.addWidget(self._timeout_sb)
        bar.addWidget(self._btn)
        layout.addLayout(bar)

        self._progress = QProgressBar()
        self._progress.setTextVisible(True)
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels([
            "", tr("ipscan_col_ip"), tr("ipscan_col_host"), tr("ipscan_col_rtt"),
        ])
        hdr = self._table.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(_C_HOST, QHeaderView.ResizeMode.Stretch)
        self._table.setColumnWidth(_C_DOT, 28)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.verticalHeader().setVisible(False)
        self._table.setVisible(False)
        layout.addWidget(self._table, 10)

        bottom = QHBoxLayout()

        self._status = QLabel("")
        self._status.setWordWrap(True)

        self._btn_csv = QPushButton(tr("common_export_csv"))
        self._btn_csv.setVisible(False)
        self._btn_csv.clicked.connect(self._export_csv)

        self._btn_txt = QPushButton(tr("common_export_txt"))
        self._btn_txt.setVisible(False)
        self._btn_txt.clicked.connect(self._export_txt)

        bottom.addWidget(self._status, 1)
        bottom.addWidget(self._btn_csv)
        bottom.addWidget(self._btn_txt)
        layout.addLayout(bottom)
        layout.addStretch(1)

    def _on_scan(self) -> None:
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._btn.setText(tr("ipscan_scan_btn"))
            return

        text = self._input.text().strip()
        if not text:
            return

        hosts = _parse_range(text)
        if isinstance(hosts, str):
            self._status.setStyleSheet("color: #f38ba8;")
            self._status.setText(tr("common_error_prefix", msg=hosts))
            return

        self._table.setRowCount(0)
        self._table.setVisible(False)
        self._btn_csv.setVisible(False)
        self._btn_txt.setVisible(False)
        self._progress.setMaximum(len(hosts))
        self._progress.setValue(0)
        self._progress.setFormat(f"0 / {len(hosts)}")
        self._progress.setVisible(True)
        self._status.setStyleSheet("color: palette(mid);")
        self._status.setText(tr("ipscan_scanning", n=len(hosts)))
        self._btn.setText(tr("ipscan_stop_btn"))

        self._worker = ScanWorker(hosts, self._timeout_sb.value(), n_threads=50)
        self._worker.found.connect(self._on_found)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _on_found(self, ip: str, hostname: str, rtt: float) -> None:
        r = self._table.rowCount()
        self._table.insertRow(r)
        self._table.setVisible(True)

        dot = QTableWidgetItem("●")
        dot.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        dot.setForeground(_GREEN)
        self._table.setItem(r, _C_DOT, dot)

        self._table.setItem(r, _C_IP, QTableWidgetItem(ip))
        self._table.setItem(r, _C_HOST, QTableWidgetItem(hostname))
        rtt_item = QTableWidgetItem(f"{rtt:.1f}")
        rtt_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self._table.setItem(r, _C_RTT, rtt_item)

    def _on_progress(self, done: int, total: int) -> None:
        self._progress.setValue(done)
        self._progress.setFormat(f"{done} / {total}")

    def _on_finished(self) -> None:
        self._btn.setText(tr("ipscan_scan_btn"))
        self._progress.setVisible(False)
        alive   = self._table.rowCount()
        scanned = self._progress.maximum()
        self._status.setStyleSheet("color: palette(mid);")
        self._status.setText(tr("ipscan_done", alive=alive, scanned=scanned))
        if alive:
            self._btn_csv.setVisible(True)
            self._btn_txt.setVisible(True)

    def _table_rows(self) -> list[tuple[str, str, str]]:
        rows = []
        for r in range(self._table.rowCount()):
            ip       = self._table.item(r, _C_IP).text()
            hostname = self._table.item(r, _C_HOST).text()
            rtt      = self._table.item(r, _C_RTT).text()
            rows.append((ip, hostname, rtt))
        return rows

    def _export_csv(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, tr("ipscan_export_csv_dlg"), "scan_result.csv",
            "CSV (*.csv);;All (*)",
        )
        if not path:
            return
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write("IP,Hostname,RTT_ms\n")
                for ip, hostname, rtt in self._table_rows():
                    f.write(f"{ip},{hostname},{rtt}\n")
        except OSError as exc:
            QMessageBox.critical(self, "Error", str(exc))

    def _export_txt(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, tr("ipscan_export_txt_dlg"), "scan_result.txt",
            "Text (*.txt);;All (*)",
        )
        if not path:
            return
        try:
            rows = self._table_rows()
            h_ip   = tr("ipscan_txt_ip_hdr")
            h_host = tr("ipscan_txt_host_hdr")
            h_rtt  = tr("ipscan_txt_rtt_hdr")
            w_ip   = max(len(h_ip),   max((len(r[0]) for r in rows), default=0))
            w_host = max(len(h_host), max((len(r[1]) for r in rows), default=0))
            w_rtt  = max(len(h_rtt),  max((len(r[2]) for r in rows), default=0))
            sep    = f"+{'-'*(w_ip+2)}+{'-'*(w_host+2)}+{'-'*(w_rtt+2)}+"
            header = f"| {h_ip:<{w_ip}} | {h_host:<{w_host}} | {h_rtt:<{w_rtt}} |"
            with open(path, 'w', encoding='utf-8') as f:
                f.write(f"{self._input.text().strip()}\n")
                f.write(f"{self._status.text()}\n\n")
                f.write(sep + "\n")
                f.write(header + "\n")
                f.write(sep + "\n")
                for ip, hostname, rtt in rows:
                    f.write(f"| {ip:<{w_ip}} | {hostname:<{w_host}} | {rtt:<{w_rtt}} |\n")
                f.write(sep + "\n")
        except OSError as exc:
            QMessageBox.critical(self, "Error", str(exc))

    def closeEvent(self, event) -> None:
        if self._worker:
            self._worker.cancel()
            self._worker.wait(5000)
        super().closeEvent(event)
