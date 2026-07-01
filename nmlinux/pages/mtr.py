"""MTR — combinaison ping + traceroute avec statistiques par hop."""

from __future__ import annotations

import platform
import re
import shutil
import subprocess

_IS_MACOS = platform.system() == 'Darwin'

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QBrush, QColor, QFont
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFileDialog, QFrame, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QMessageBox, QPushButton,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QSizePolicy,
)

from nmlinux.core.cli_bar import get_cli_bar
from nmlinux.core.host_actions import HostActionMenu
from nmlinux.core.i18n import tr
from nmlinux.core.theme import color_ok, color_err

_CMD_MTR = shutil.which('mtr')

_YELLOW = QColor('#f9e2af')
_ORANGE = QColor('#fab387')


def _rtt_color(rtt: float) -> QColor:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QPalette as _P
    if rtt < 0:
        return QApplication.palette().color(_P.ColorRole.PlaceholderText)
    if rtt < 20:   return QColor(color_ok())
    if rtt < 80:   return _YELLOW
    if rtt < 200:  return _ORANGE
    return QColor(color_err())


def _loss_color(pct: float) -> QColor:
    if pct < 1:    return QColor(color_ok())
    if pct < 10:   return _YELLOW
    if pct < 25:   return _ORANGE
    return QColor(color_err())


# ── Text report parser ────────────────────────────────────────────────────────

# "  1.|-- _gateway    0.0%   3   1.0   0.8   0.7   1.0   0.2"
_HOP_RE = re.compile(
    r'^\s*(\d+)\.\|--\s+(\S+)\s+([\d.]+)%\s+(\d+)'
    r'\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)'
)


def _parse_mtr_report(text: str) -> list[dict]:
    hubs = []
    for line in text.splitlines():
        m = _HOP_RE.match(line)
        if not m:
            continue
        hubs.append({
            'count': int(m.group(1)),
            'host':  m.group(2),
            'Loss%': float(m.group(3)),
            'Snt':   int(m.group(4)),
            'Last':  float(m.group(5)),
            'Avg':   float(m.group(6)),
            'Best':  float(m.group(7)),
            'Wrst':  float(m.group(8)),
            'StDev': float(m.group(9)),
        })
    return hubs


# ── Worker ────────────────────────────────────────────────────────────────────

class MtrWorker(QThread):
    batch_done    = Signal(int, list)   # (batch_num, hubs)
    batch_started = Signal(int)         # batch_num
    error         = Signal(str)
    finished      = Signal()

    def __init__(self, target: str, cycles: int, no_dns: bool, continuous: bool) -> None:
        super().__init__()
        self._target     = target
        self._cycles     = cycles
        self._no_dns     = no_dns
        self._continuous = continuous
        self._stop       = False
        self._proc: subprocess.Popen | None = None

    def run(self) -> None:
        batch = 0
        while not self._stop:
            batch += 1
            self.batch_started.emit(batch)
            args = [_CMD_MTR, '--report', '--report-cycles', str(self._cycles)]
            if self._no_dns:
                args.append('--no-dns')
            args.append(self._target)

            try:
                self._proc = subprocess.Popen(
                    args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                )
                stdout, stderr = self._proc.communicate()
                if self._stop:
                    break
                if self._proc.returncode != 0:
                    self.error.emit(stderr.strip() or stdout.strip())
                    break
                hubs = _parse_mtr_report(stdout)
                if not hubs:
                    self.error.emit(tr("mtr_err_no_output"))
                    break
                self.batch_done.emit(batch, hubs)
            except Exception as exc:
                self.error.emit(str(exc))
                break

            if not self._continuous:
                break

        self.finished.emit()

    def stop(self) -> None:
        self._stop = True
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()
        self.wait(5000)


# ── Page ──────────────────────────────────────────────────────────────────────

class MtrPage(QWidget):
    action_requested = Signal(str, str, str)

    def __init__(self) -> None:
        super().__init__()
        self._worker: MtrWorker | None = None
        self._last_hubs: list[dict] = []
        self._build_ui()

    # ── Layout ───────────────────────────────────────────────────────────────

    def set_target(self, host: str) -> None:
        self._input.setText(host)
        self._on_start()

    def _on_right_click(self, pos) -> None:
        row = self._table.rowAt(pos.y())
        if row < 0:
            return
        host_item = self._table.item(row, 1)
        if not host_item:
            return
        host = host_item.text()
        if host in ('*', '???', ''):
            return
        menu = HostActionMenu(host, host, parent=self)
        menu.action_chosen.connect(self.action_requested)
        menu.exec(self._table.viewport().mapToGlobal(pos))

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # ── Toolbar row 1: target + start/stop ───────────────────────────────
        row1 = QHBoxLayout()
        row1.addWidget(QLabel(tr("mtr_target_lbl")))
        self._input = QLineEdit()
        self._input.setPlaceholderText(tr("mtr_target_ph"))
        self._input.returnPressed.connect(self._on_start)
        self._input.textChanged.connect(self._update_cli_bar)
        row1.addWidget(self._input, 1)

        self._btn_go = QPushButton(tr("mtr_start_btn"))
        self._btn_go.setFixedWidth(120)
        self._btn_go.setDefault(True)
        self._btn_go.clicked.connect(self._on_start)
        row1.addWidget(self._btn_go)

        self._btn_stop = QPushButton(tr("mtr_stop_btn"))
        self._btn_stop.setFixedWidth(100)
        self._btn_stop.clicked.connect(self._on_stop)
        self._btn_stop.setEnabled(False)
        row1.addWidget(self._btn_stop)

        layout.addLayout(row1)

        # ── Toolbar row 2: options ────────────────────────────────────────────
        row2 = QHBoxLayout()
        row2.addWidget(QLabel(tr("mtr_cycles_lbl")))
        self._cycles_box = QComboBox()
        for c in ('5', '10', '20', '50'):
            self._cycles_box.addItem(c)
        self._cycles_box.setCurrentText('10')
        self._cycles_box.setFixedWidth(60)
        self._cycles_box.currentTextChanged.connect(self._update_cli_bar)
        row2.addWidget(self._cycles_box)

        self._chk_continuous = QCheckBox(tr("mtr_continuous_lbl"))
        self._chk_continuous.setChecked(False)
        row2.addWidget(self._chk_continuous)

        self._chk_nodns = QCheckBox(tr("mtr_nodns_lbl"))
        self._chk_nodns.stateChanged.connect(self._update_cli_bar)
        row2.addWidget(self._chk_nodns)

        row2.addStretch()
        layout.addLayout(row2)

        # Status + export
        status_bar = QHBoxLayout()
        self._lbl_status = QLabel("")
        self._lbl_status.setStyleSheet("color: palette(mid);")
        status_bar.addWidget(self._lbl_status, 1)

        self._btn_csv = QPushButton(tr("common_export_csv"))
        self._btn_csv.setVisible(False)
        self._btn_csv.clicked.connect(self._export_csv)
        status_bar.addWidget(self._btn_csv)

        self._btn_txt = QPushButton(tr("common_export_txt"))
        self._btn_txt.setVisible(False)
        self._btn_txt.clicked.connect(self._export_txt)
        status_bar.addWidget(self._btn_txt)

        layout.addLayout(status_bar)

        # Legend
        legend = QHBoxLayout()
        legend.addStretch()
        for color_str, label in [
            (color_ok(),     "< 1 %"),
            (_YELLOW.name(), "1–10 %"),
            (_ORANGE.name(), "10–25 %"),
            (color_err(),    "> 25 %"),
        ]:
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {color_str}; font-size: 10px;")
            legend.addWidget(dot)
            legend.addWidget(QLabel(label))
            legend.addSpacing(12)
        lbl_leg = QLabel(tr("mtr_legend_loss"))
        lbl_leg.setStyleSheet("color: palette(mid); font-size: 10px;")
        legend.addWidget(lbl_leg)
        layout.addLayout(legend)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(sep)

        # Table
        cols = [
            tr("mtr_col_hop"), tr("mtr_col_host"),
            tr("mtr_col_loss"), tr("mtr_col_sent"),
            tr("mtr_col_last"), tr("mtr_col_avg"),
            tr("mtr_col_best"), tr("mtr_col_worst"),
            tr("mtr_col_jitter"),
        ]
        self._table = QTableWidget(0, len(cols))
        self._table.setHorizontalHeaderLabels(cols)
        hh = self._table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        for fixed_col in (0, 2, 3, 4, 5, 6, 7, 8):
            hh.setSectionResizeMode(fixed_col, QHeaderView.ResizeMode.ResizeToContents)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)
        self._table.setFont(QFont('Menlo' if _IS_MACOS else 'Monospace', 9))
        layout.addWidget(self._table, 1)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._on_right_click)

        if not _CMD_MTR:
            self._btn_go.setEnabled(False)
            self._input.setEnabled(False)
            banner = QLabel(tr("mtr_err_no_cmd"))
            banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
            banner.setStyleSheet(
                "color: palette(mid); font-size: 13px; padding: 24px;"
            )
            banner.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            layout.addWidget(banner)
        else:
            self._update_cli_bar()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _update_cli_bar(self, *_) -> None:
        t = self._input.text().strip()
        if t and _CMD_MTR:
            no_dns = '--no-dns ' if self._chk_nodns.isChecked() else ''
            get_cli_bar() and get_cli_bar().set_cmd(
                f'mtr --report-cycles {self._cycles_box.currentText()} {no_dns}{t}'
            )
        elif _CMD_MTR:
            get_cli_bar() and get_cli_bar().set_cmd('')

    # ── Control ──────────────────────────────────────────────────────────────

    def _on_start(self) -> None:
        if not _CMD_MTR:
            return
        target = self._input.text().strip()
        if not target:
            return
        self._stop_worker()
        self._table.setRowCount(0)
        self._last_hubs = []
        self._btn_csv.setVisible(False)
        self._btn_txt.setVisible(False)

        cycles     = int(self._cycles_box.currentText())
        no_dns     = self._chk_nodns.isChecked()
        continuous = self._chk_continuous.isChecked()

        self._worker = MtrWorker(target, cycles, no_dns, continuous)
        self._worker.batch_started.connect(self._on_batch_started)
        self._worker.batch_done.connect(self._on_batch_done)
        self._worker.error.connect(self._on_error)
        self._worker.finished.connect(self._on_finished)
        self._btn_go.setEnabled(False)
        self._btn_stop.setEnabled(True)
        self._worker.start()

    def _on_stop(self) -> None:
        self._stop_worker()
        self._lbl_status.setText(tr("mtr_status_stop"))

    def _stop_worker(self) -> None:
        if self._worker:
            try:
                self._worker.batch_started.disconnect()
                self._worker.batch_done.disconnect()
                self._worker.error.disconnect()
                self._worker.finished.disconnect()
            except Exception:
                pass
            self._worker.stop()
            self._worker = None
        self._btn_go.setEnabled(True)
        self._btn_stop.setEnabled(False)

    # ── Signals ──────────────────────────────────────────────────────────────

    def _on_batch_started(self, batch: int) -> None:
        cycles = self._cycles_box.currentText()
        self._lbl_status.setText(tr("mtr_status_run", batch=batch, cycles=cycles))

    def _on_batch_done(self, batch: int, hubs: list[dict]) -> None:
        self._last_hubs = hubs
        self._populate_table(hubs)
        n = len(hubs)
        self._lbl_status.setText(tr("mtr_status_done", batch=batch, n=n))
        self._btn_csv.setVisible(True)
        self._btn_txt.setVisible(True)

    def _on_error(self, msg: str) -> None:
        self._lbl_status.setText(tr("common_error_prefix", msg=msg))

    def _on_finished(self) -> None:
        self._btn_go.setEnabled(True)
        self._btn_stop.setEnabled(False)
        self._worker = None

    # ── Table ────────────────────────────────────────────────────────────────

    def _populate_table(self, hubs: list[dict]) -> None:
        self._table.setRowCount(0)
        for hub in hubs:
            row = self._table.rowCount()
            self._table.insertRow(row)

            hop_num  = hub.get('count', row + 1)
            host     = hub.get('host', '???')
            loss     = hub.get('Loss%', 0.0)
            sent     = hub.get('Snt', 0)
            last     = hub.get('Last', 0.0)
            avg      = hub.get('Avg',  0.0)
            best     = hub.get('Best', 0.0)
            worst    = hub.get('Wrst', 0.0)
            jitter   = hub.get('StDev', 0.0)

            values = [
                str(hop_num),
                host,
                f"{loss:.1f} %",
                str(sent),
                f"{last:.1f}",
                f"{avg:.1f}",
                f"{best:.1f}",
                f"{worst:.1f}",
                f"{jitter:.1f}",
            ]

            for col, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    if col not in (0, 1) else
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
                )
                # Color Loss%
                if col == 2:
                    item.setForeground(QBrush(_loss_color(loss)))
                # Color Avg RTT
                elif col == 5:
                    item.setForeground(QBrush(_rtt_color(avg)))
                self._table.setItem(row, col, item)

    # ── Export ───────────────────────────────────────────────────────────────

    def _table_rows(self) -> list[tuple[str, ...]]:
        rows = []
        for r in range(self._table.rowCount()):
            rows.append(tuple(
                self._table.item(r, c).text() if self._table.item(r, c) else ''
                for c in range(self._table.columnCount())
            ))
        return rows

    def _headers(self) -> list[str]:
        return [
            tr("mtr_col_hop"), tr("mtr_col_host"),
            tr("mtr_col_loss"), tr("mtr_col_sent"),
            tr("mtr_col_last"), tr("mtr_col_avg"),
            tr("mtr_col_best"), tr("mtr_col_worst"),
            tr("mtr_col_jitter"),
        ]

    def _export_csv(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, tr("common_export_csv"), "mtr_result.csv",
            "CSV (*.csv);;All (*)",
        )
        if not path:
            return
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(','.join(self._headers()) + '\n')
                for row in self._table_rows():
                    safe = [v.replace('"', '""') for v in row]
                    f.write(','.join(f'"{v}"' if ',' in v else v for v in safe) + '\n')
        except OSError as exc:
            QMessageBox.critical(self, "Error", str(exc))

    def _export_txt(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, tr("common_export_txt"), "mtr_result.txt",
            "Text (*.txt);;All (*)",
        )
        if not path:
            return
        try:
            rows    = self._table_rows()
            headers = self._headers()
            widths  = [
                max(len(h), max((len(r[i]) for r in rows), default=0))
                for i, h in enumerate(headers)
            ]
            sep  = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
            hrow = "| " + " | ".join(f"{h:<{w}}" for h, w in zip(headers, widths)) + " |"
            target = self._input.text().strip()
            with open(path, 'w', encoding='utf-8') as f:
                if target:
                    f.write(f"MTR — {target}\n{self._lbl_status.text()}\n\n")
                f.write(sep + "\n" + hrow + "\n" + sep + "\n")
                for row in rows:
                    f.write("| " + " | ".join(f"{v:<{w}}" for v, w in zip(row, widths)) + " |\n")
                f.write(sep + "\n")
        except OSError as exc:
            QMessageBox.critical(self, "Error", str(exc))
