from __future__ import annotations

import socket
import time as _time
from concurrent.futures import ThreadPoolExecutor, as_completed

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QProgressBar, QFileDialog, QMessageBox,
)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt, QThread, Signal

from nmlinux.core.cli_bar import get_cli_bar
from nmlinux.core.i18n import tr


_C_PORT, _C_SERVICE, _C_RTT = range(3)
_GREEN = QColor("#a6e3a1")

_PRESETS_VALUES: dict[str, str] = {
    "custom":   "",
    "top20":    "21,22,23,25,53,80,110,135,139,143,443,445,993,995,1723,3306,3389,5900,8080,8443",
    "1-1024":   "1-1024",
    "1-65535":  "1-65535",
}


def _parse_ports(text: str) -> list[int] | str:
    ports: set[int] = set()
    for token in text.replace(' ', '').split(','):
        if not token:
            continue
        if '-' in token:
            parts = token.split('-', 1)
            try:
                lo, hi = int(parts[0]), int(parts[1])
            except ValueError:
                return tr("pscan_err_inv_range", token=token)
            if lo < 1 or hi > 65535 or lo > hi:
                return tr("pscan_err_range_oor", token=token)
            ports.update(range(lo, hi + 1))
        else:
            try:
                p = int(token)
            except ValueError:
                return tr("pscan_err_inv_port", token=token)
            if p < 1 or p > 65535:
                return tr("pscan_err_port_oor", p=p)
            ports.add(p)

    if not ports:
        return tr("pscan_err_no_port")
    if len(ports) > 65535:
        return tr("pscan_err_too_many")
    return sorted(ports)


class ScanWorker(QThread):
    found    = Signal(int, str, float)
    progress = Signal(int, int)
    finished = Signal()

    def __init__(self, host: str, ports: list[int], timeout: float, n_threads: int) -> None:
        super().__init__()
        self._host      = host
        self._ports     = ports
        self._timeout   = timeout
        self._n_threads = n_threads
        self._cancelled = False

    def run(self) -> None:
        try:
            host_ip = socket.gethostbyname(self._host)
        except socket.gaierror as exc:
            self.found.emit(-1, str(exc), -1.0)
            self.finished.emit()
            return

        total = len(self._ports)
        done  = 0
        with ThreadPoolExecutor(max_workers=self._n_threads) as pool:
            futures = {pool.submit(self._probe, host_ip, p): p for p in self._ports}
            for future in as_completed(futures):
                if self._cancelled:
                    for f in futures:
                        f.cancel()
                    break
                port = futures[future]
                try:
                    open_, rtt = future.result()
                except Exception:
                    open_, rtt = False, -1.0
                done += 1
                self.progress.emit(done, total)
                if open_:
                    try:
                        service = socket.getservbyport(port, 'tcp')
                    except OSError:
                        service = ""
                    self.found.emit(port, service, rtt)

        self.finished.emit()

    def _probe(self, host: str, port: int) -> tuple[bool, float]:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self._timeout)
            t0 = _time.monotonic()
            err = sock.connect_ex((host, port))
            rtt = (_time.monotonic() - t0) * 1000
            sock.close()
            return err == 0, rtt
        except Exception:
            return False, -1.0

    def cancel(self) -> None:
        self._cancelled = True


class PortScannerPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._worker: ScanWorker | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel(tr("pscan_title"))
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        bar = QHBoxLayout()

        self._host_input = QLineEdit()
        self._host_input.setPlaceholderText(tr("pscan_host_ph"))
        self._host_input.returnPressed.connect(self._on_scan)
        self._host_input.textChanged.connect(self._update_cli)

        self._ports_input = QLineEdit()
        self._ports_input.setPlaceholderText(tr("pscan_ports_ph"))
        self._ports_input.setFixedWidth(220)
        self._ports_input.textChanged.connect(self._update_cli)

        self._preset_cb = QComboBox()
        self._preset_keys = list(_PRESETS_VALUES.keys())
        preset_labels = [
            tr("pscan_preset_custom"),
            "Top 20",
            "1 – 1024",
            "1 – 65535",
        ]
        self._preset_cb.addItems(preset_labels)
        self._preset_cb.currentIndexChanged.connect(self._on_preset)

        self._timeout_cb = QComboBox()
        for label in ["0.3 s", "0.5 s", "1 s", "2 s"]:
            self._timeout_cb.addItem(label)
        self._timeout_cb.setCurrentIndex(1)
        self._timeout_cb.setFixedWidth(72)
        self._timeouts = [0.3, 0.5, 1.0, 2.0]

        self._btn = QPushButton(tr("pscan_scan_btn"))
        self._btn.setDefault(True)
        self._btn.clicked.connect(self._on_scan)

        bar.addWidget(self._host_input, 2)
        bar.addWidget(self._ports_input, 1)
        bar.addWidget(self._preset_cb)
        bar.addWidget(QLabel(tr("pscan_timeout_lbl")))
        bar.addWidget(self._timeout_cb)
        bar.addWidget(self._btn)
        layout.addLayout(bar)

        self._progress = QProgressBar()
        self._progress.setTextVisible(True)
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        self._table = QTableWidget(0, 3)
        self._table.setHorizontalHeaderLabels([tr("common_port"), tr("common_service"), "RTT (ms)"])
        hdr = self._table.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(_C_SERVICE, QHeaderView.ResizeMode.Stretch)
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

    def _on_preset(self, idx: int) -> None:
        key   = self._preset_keys[idx]
        value = _PRESETS_VALUES.get(key, "")
        if value:
            self._ports_input.setText(value)

    def _update_cli(self) -> None:
        bar = get_cli_bar()
        if not bar:
            return
        host  = self._host_input.text().strip()
        ports = self._ports_input.text().strip()
        if not host:
            bar.set_cmd('')
            return
        p = f'-p {ports}' if ports else '-p 1-1024'
        bar.set_cmd(f'nmap -sT {p} {host}')

    def _on_scan(self) -> None:
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._btn.setText(tr("pscan_scan_btn"))
            return

        host = self._host_input.text().strip()
        if not host:
            return

        ports = _parse_ports(self._ports_input.text())
        if isinstance(ports, str):
            self._status.setStyleSheet("color: #f38ba8;")
            self._status.setText(tr("common_error_prefix", msg=ports))
            return

        self._table.setRowCount(0)
        self._table.setVisible(False)
        self._btn_csv.setVisible(False)
        self._btn_txt.setVisible(False)
        self._progress.setMaximum(len(ports))
        self._progress.setValue(0)
        self._progress.setFormat(f"0 / {len(ports)}")
        self._progress.setVisible(True)
        self._status.setStyleSheet("color: palette(mid);")
        self._status.setText(tr("pscan_scanning", n=len(ports), host=host))
        self._btn.setText(tr("pscan_stop_btn"))

        timeout = self._timeouts[self._timeout_cb.currentIndex()]
        self._worker = ScanWorker(host, ports, timeout, n_threads=200)
        self._worker.found.connect(self._on_found)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _on_found(self, port: int, service: str, rtt: float) -> None:
        if port == -1:
            self._status.setStyleSheet("color: #f38ba8;")
            self._status.setText(tr("common_error_prefix", msg=service))
            return

        r = self._table.rowCount()
        self._table.insertRow(r)
        self._table.setVisible(True)

        port_item = QTableWidgetItem(str(port))
        port_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        port_item.setForeground(_GREEN)
        self._table.setItem(r, _C_PORT, port_item)
        self._table.setItem(r, _C_SERVICE, QTableWidgetItem(service))
        rtt_item = QTableWidgetItem(f"{rtt:.1f}")
        rtt_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self._table.setItem(r, _C_RTT, rtt_item)

    def _on_progress(self, done: int, total: int) -> None:
        self._progress.setValue(done)
        self._progress.setFormat(f"{done} / {total}")

    def _on_finished(self) -> None:
        self._btn.setText(tr("pscan_scan_btn"))
        self._progress.setVisible(False)
        self._sort_by_port()
        open_count = self._table.rowCount()
        scanned    = self._progress.maximum()
        self._status.setStyleSheet("color: palette(mid);")
        self._status.setText(tr("pscan_done", n=open_count, scanned=scanned))
        if open_count:
            self._btn_csv.setVisible(True)
            self._btn_txt.setVisible(True)

    def _sort_by_port(self) -> None:
        rows = []
        for r in range(self._table.rowCount()):
            rows.append((
                int(self._table.item(r, _C_PORT).text()),
                self._table.item(r, _C_SERVICE).text(),
                self._table.item(r, _C_RTT).text(),
            ))
        rows.sort(key=lambda x: x[0])
        for r, (port, service, rtt) in enumerate(rows):
            self._table.item(r, _C_PORT).setText(str(port))
            self._table.item(r, _C_SERVICE).setText(service)
            self._table.item(r, _C_RTT).setText(rtt)

    def _table_rows(self) -> list[tuple[str, str, str]]:
        rows = []
        for r in range(self._table.rowCount()):
            port    = self._table.item(r, _C_PORT).text()
            service = self._table.item(r, _C_SERVICE).text()
            rtt     = self._table.item(r, _C_RTT).text()
            rows.append((port, service, rtt))
        return rows

    def _export_csv(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, tr("pscan_export_csv_dlg"), "port_scan.csv", "CSV (*.csv);;All (*)",
        )
        if not path:
            return
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write("Port,Service,RTT_ms\n")
                for port, service, rtt in self._table_rows():
                    f.write(f"{port},{service},{rtt}\n")
        except OSError as exc:
            QMessageBox.critical(self, "Error", str(exc))

    def _export_txt(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, tr("pscan_export_txt_dlg"), "port_scan.txt", "Text (*.txt);;All (*)",
        )
        if not path:
            return
        try:
            rows = self._table_rows()
            h_port = tr("common_port")
            h_svc  = tr("common_service")
            h_rtt  = "RTT (ms)"
            w_port = max(len(h_port), max((len(r[0]) for r in rows), default=0))
            w_svc  = max(len(h_svc),  max((len(r[1]) for r in rows), default=0))
            w_rtt  = max(len(h_rtt),  max((len(r[2]) for r in rows), default=0))
            sep    = f"+{'-'*(w_port+2)}+{'-'*(w_svc+2)}+{'-'*(w_rtt+2)}+"
            header = f"| {h_port:<{w_port}} | {h_svc:<{w_svc}} | {h_rtt:<{w_rtt}} |"
            with open(path, 'w', encoding='utf-8') as f:
                f.write(tr("pscan_target_label", target=self._host_input.text().strip()) + "\n")
                f.write(f"{self._status.text()}\n\n")
                f.write(sep + "\n")
                f.write(header + "\n")
                f.write(sep + "\n")
                for port, service, rtt in rows:
                    f.write(f"| {port:<{w_port}} | {service:<{w_svc}} | {rtt:<{w_rtt}} |\n")
                f.write(sep + "\n")
        except OSError as exc:
            QMessageBox.critical(self, "Error", str(exc))

    def closeEvent(self, event) -> None:
        if self._worker:
            self._worker.cancel()
            self._worker.wait(5000)
        super().closeEvent(event)
