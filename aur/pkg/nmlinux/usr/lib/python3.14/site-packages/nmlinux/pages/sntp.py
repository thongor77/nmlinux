from __future__ import annotations

import socket
import struct
import time

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QGroupBox, QFormLayout,
    QSpinBox,
)
from PySide6.QtCore import Qt, QThread, Signal

from nmlinux.core.i18n import tr


_NTP_DELTA = 2208988800
_SERVERS = [
    "pool.ntp.org",
    "time.google.com",
    "time.cloudflare.com",
    "time.windows.com",
    "fr.pool.ntp.org",
    "europe.pool.ntp.org",
]

_GREEN = '#a6e3a1'
_RED   = '#f38ba8'


def _query_ntp(host: str, port: int = 123, timeout: float = 5.0) -> dict:
    packet = bytearray(48)
    packet[0] = 0x1B

    t0 = time.time()
    t0_ntp = t0 + _NTP_DELTA
    t0_sec  = int(t0_ntp)
    t0_frac = int((t0_ntp - t0_sec) * (2 ** 32))
    struct.pack_into('!II', packet, 40, t0_sec, t0_frac)

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.settimeout(timeout)
        s.sendto(bytes(packet), (host, port))
        data, _ = s.recvfrom(1024)

    t3 = time.time()

    if len(data) < 48:
        raise ValueError(tr("sntp_err_short"))

    u = struct.unpack('!12I', data[:48])
    b0       = (u[0] >> 24) & 0xFF
    li       = (b0 >> 6) & 0x3
    vn       = (b0 >> 3) & 0x7
    stratum  = (u[0] >> 16) & 0xFF
    poll_raw = (u[0] >> 8) & 0xFF
    prec_raw = u[0] & 0xFF
    if prec_raw > 127:
        prec_raw -= 256

    root_delay = u[1] / (2 ** 16)
    root_disp  = u[2] / (2 ** 16)

    if stratum <= 1:
        ref_id = data[12:16].decode('ascii', errors='replace').rstrip('\x00')
    else:
        ref_id = '.'.join(str(b) for b in data[12:16])

    t2     = (u[8]  - _NTP_DELTA) + u[9]  / (2 ** 32)
    t1_srv = (u[10] - _NTP_DELTA) + u[11] / (2 ** 32)

    offset_s = ((t2 - t0) + (t1_srv - t3)) / 2
    delay_s  = (t3 - t0) - (t1_srv - t2)

    server_time = t1_srv + (t3 - t0) / 2

    li_keys = ["sntp_li_0", "sntp_li_1", "sntp_li_2", "sntp_li_3"]
    li_label = tr(li_keys[li]) if li < len(li_keys) else str(li)

    return {
        'server_time': time.strftime('%Y-%m-%d  %H:%M:%S  UTC', time.gmtime(server_time)),
        'local_time':  time.strftime('%Y-%m-%d  %H:%M:%S', time.localtime()),
        'offset_ms':   offset_s * 1000,
        'delay_ms':    delay_s  * 1000,
        'root_delay_ms': root_delay * 1000,
        'root_disp_ms':  root_disp  * 1000,
        'stratum':     stratum,
        'ref_id':      ref_id,
        'precision':   f"2^{prec_raw} ≈ {abs(2 ** prec_raw) * 1e6:.1f} µs",
        'version':     vn,
        'li':          li_label,
    }


class SntpWorker(QThread):
    result   = Signal(list)
    error    = Signal(str)

    def __init__(self, host: str, port: int, queries: int) -> None:
        super().__init__()
        self._host    = host
        self._port    = port
        self._queries = queries

    def run(self) -> None:
        results = []
        for _ in range(self._queries):
            try:
                results.append(_query_ntp(self._host, self._port))
                if self._queries > 1:
                    time.sleep(0.5)
            except Exception as exc:
                self.error.emit(str(exc))
                return
        self.result.emit(results)


class SntpPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._worker: SntpWorker | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel(tr("sntp_title"))
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(8)
        grid.setColumnStretch(1, 1)

        grid.addWidget(QLabel(tr("sntp_server_lbl")), 0, 0)
        srv_row = QHBoxLayout()
        self._server = QLineEdit()
        self._server.setPlaceholderText("pool.ntp.org")
        self._server.returnPressed.connect(self._query)
        self._preset = QComboBox()
        self._preset.addItem(tr("sntp_preset_ph"))
        for s in _SERVERS:
            self._preset.addItem(s)
        self._preset.currentIndexChanged.connect(self._on_preset)
        srv_row.addWidget(self._server, 1)
        srv_row.addWidget(self._preset)
        grid.addLayout(srv_row, 0, 1)

        grid.addWidget(QLabel(tr("sntp_port_lbl")), 1, 0)
        self._port = QLineEdit("123")
        self._port.setFixedWidth(70)
        grid.addWidget(self._port, 1, 1)

        grid.addWidget(QLabel(tr("sntp_queries_lbl")), 2, 0)
        self._queries = QSpinBox()
        self._queries.setRange(1, 5)
        self._queries.setValue(1)
        self._queries.setFixedWidth(70)
        grid.addWidget(self._queries, 2, 1)

        layout.addLayout(grid)

        btn_row = QHBoxLayout()
        self._btn = QPushButton(tr("sntp_query_btn"))
        self._btn.setDefault(True)
        self._btn.clicked.connect(self._query)
        btn_row.addWidget(self._btn)
        btn_row.addStretch(1)
        self._status = QLabel("")
        btn_row.addWidget(self._status)
        layout.addLayout(btn_row)

        self._grp = QGroupBox(tr("sntp_results_box"))
        self._form = QFormLayout(self._grp)
        self._form.setHorizontalSpacing(20)
        self._form.setVerticalSpacing(8)
        self._form.setContentsMargins(16, 12, 16, 12)
        self._grp.setVisible(False)
        layout.addWidget(self._grp)

        layout.addStretch(1)

    def _on_preset(self, idx: int) -> None:
        if idx > 0:
            self._server.setText(_SERVERS[idx - 1])

    def _query(self) -> None:
        host = self._server.text().strip()
        if not host or (self._worker and self._worker.isRunning()):
            return
        try:
            port = int(self._port.text().strip() or '123')
        except ValueError:
            port = 123

        self._btn.setEnabled(False)
        self._status.setText(tr("sntp_querying"))
        self._status.setStyleSheet("")
        self._grp.setVisible(False)

        self._worker = SntpWorker(host, port, self._queries.value())
        self._worker.result.connect(self._on_result)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_result(self, results: list) -> None:
        self._btn.setEnabled(True)
        self._status.setText(tr("sntp_responses", n=len(results)))

        avg_offset = sum(r['offset_ms'] for r in results) / len(results)
        avg_delay  = sum(r['delay_ms']  for r in results) / len(results)

        d = results[-1]

        while self._form.rowCount():
            self._form.removeRow(0)

        avg_suffix = tr("sntp_avg") if len(results) > 1 else ""

        def row(label_key: str, value: str, ok: bool | None = None) -> None:
            if ok is None:
                lbl = QLabel(value)
            else:
                color  = _GREEN if ok else _RED
                symbol = '✓' if ok else '✗'
                lbl = QLabel(f'<span style="color:{color}">{symbol}</span>  {value}')
                lbl.setTextFormat(Qt.TextFormat.RichText)
            lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self._form.addRow(tr(label_key) + " :", lbl)

        row("sntp_row_server_time", d['server_time'])
        row("sntp_row_local_time",  d['local_time'])
        ok_offset = abs(avg_offset) < 1000
        row("sntp_row_offset",
            f"{avg_offset:+.3f} ms{avg_suffix}", ok=ok_offset)
        row("sntp_row_delay",
            f"{avg_delay:.3f} ms{avg_suffix}")
        row("sntp_row_root_delay",  f"{d['root_delay_ms']:.3f} ms")
        row("sntp_row_root_disp",   f"{d['root_disp_ms']:.3f} ms")
        row("sntp_row_stratum",     str(d['stratum']), ok=0 < d['stratum'] < 15)
        row("sntp_row_ref",         d['ref_id'])
        row("sntp_row_precision",   d['precision'])
        row("sntp_row_version",     str(d['version']))
        row("sntp_row_li",          d['li'])

        self._grp.setVisible(True)

    def _on_error(self, msg: str) -> None:
        self._btn.setEnabled(True)
        self._status.setText(tr("common_error_prefix", msg=msg))
        self._status.setStyleSheet("color: #f38ba8;")
