"""Firewall Viewer — lecture seule nftables / iptables / pf."""

from __future__ import annotations

import platform
import re
import shutil
import subprocess
from pathlib import Path

_IS_MACOS = platform.system() == 'Darwin'

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QBrush, QColor, QFont
from PySide6.QtWidgets import (
    QComboBox, QFrame, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

from nmlinux.core.i18n import tr
from nmlinux.core.theme import color_ok, color_err

_CMD_PKEXEC = shutil.which('pkexec')
_CMD_NFT    = shutil.which('nft')

_NFT_CONF    = Path('/etc/nftables.conf')
_IP4_RULES   = Path('/etc/iptables/iptables.rules')
_IP6_RULES   = Path('/etc/iptables/ip6tables.rules')
_PF_CONF     = Path('/etc/pf.conf')

_ORANGE = QColor('#fab387')
_BLUE   = QColor('#89b4fa')

_VERDICTS_NFT = ('accept', 'drop', 'reject', 'return',
                 'jump', 'goto', 'masquerade', 'snat', 'dnat', 'log')


# ── Parsers ───────────────────────────────────────────────────────────────────

def _action_nft(rule: str) -> str:
    words = rule.lower().split()
    for v in _VERDICTS_NFT:
        if v in words:
            if v in ('jump', 'goto'):
                idx = words.index(v)
                target = words[idx + 1] if idx + 1 < len(words) else ''
                return f"{v} {target}" if target else v
            return v
    return ''


def _action_iptables(rule: str) -> str:
    parts = rule.split()
    for i, p in enumerate(parts):
        if p == '-j' and i + 1 < len(parts):
            return parts[i + 1]
    return ''


def _comment_nft(rule: str) -> tuple[str, str]:
    """Return (rule_without_comment, comment)."""
    m = re.search(r'\bcomment\s+"([^"]*)"', rule)
    if m:
        return rule[:m.start()].strip(), m.group(1)
    return rule, ''


def _comment_iptables(rule: str) -> str:
    m = re.search(r'--comment\s+"?([^"]+)"?', rule)
    return m.group(1) if m else ''


def _ports_nft(rule: str) -> str:
    """Extract port info from an nft rule text."""
    # Match: dport/sport followed by a value or set: { 80, 443 } or ssh or 22
    matches = re.findall(
        r'\b[ds]port\s+(?:\{[^}]+\}|\S+)',
        rule, re.IGNORECASE,
    )
    return ', '.join(m.strip() for m in matches)


def _ports_iptables(rule: str) -> str:
    """Extract port info from an iptables rule text."""
    parts = []
    for flag in ('--dport', '--sport', '--destination-port', '--source-port',
                 '--dports', '--sports'):
        m = re.search(re.escape(flag) + r'\s+(\S+)', rule)
        if m:
            parts.append(m.group(1))
    return ', '.join(parts)


def parse_nft(text: str, source_label: str) -> list[dict]:
    rows: list[dict] = []
    table = ''
    chain = ''
    depth = 0

    for raw_line in text.splitlines():
        line = raw_line.strip()

        # Skip comments and shebangs
        if not line or line.startswith('#') or line.startswith('//'):
            continue
        # destroy / flush / include directives — skip
        if line.startswith(('destroy ', 'flush ', 'include ')):
            continue

        if line.startswith('table '):
            # "table inet filter {" or "table inet filter"
            parts = line.rstrip('{').split()
            table = ' '.join(parts[1:3]) if len(parts) >= 3 else line
            depth = 1
        elif line.startswith('chain '):
            parts = line.rstrip('{').split()
            chain = parts[1] if len(parts) >= 2 else ''
            depth = 2
        elif line == '}':
            depth = max(0, depth - 1)
            if depth < 2:
                chain = ''
            if depth < 1:
                table = ''
        elif depth == 2:
            # Chain-level metadata
            if line.startswith('type '):
                # "type filter hook input priority filter; policy drop;"
                m = re.search(r'policy\s+(\w+)', line)
                if m:
                    pol = m.group(1).rstrip(';')
                    rows.append({
                        'source':  source_label,
                        'table':   table,
                        'chain':   chain,
                        'rule':    f'(policy {pol})',
                        'action':  pol,
                        'comment': '',
                        'is_meta': True,
                    })
                continue
            if line.startswith('policy '):
                pol = line.rstrip(';').split()[-1]
                rows.append({
                    'source':  source_label,
                    'table':   table,
                    'chain':   chain,
                    'rule':    f'(policy {pol})',
                    'port':    '',
                    'action':  pol,
                    'comment': '',
                    'is_meta': True,
                })
                continue

            rule_text, comment = _comment_nft(line)
            # Strip nft handle annotations "# handle N"
            rule_text = re.sub(r'\s*#\s*handle\s+\d+', '', rule_text).strip()
            if not rule_text:
                continue
            action = _action_nft(rule_text)
            rows.append({
                'source':  source_label,
                'table':   table,
                'chain':   chain,
                'rule':    rule_text,
                'port':    _ports_nft(rule_text),
                'action':  action,
                'comment': comment,
                'is_meta': False,
            })
    return rows


def parse_iptables(text: str, source_label: str) -> list[dict]:
    rows: list[dict] = []
    table = 'filter'

    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if line.startswith('*'):
            table = line[1:].strip()
            continue
        if line.startswith(':'):
            # ":CHAIN POLICY [pkts:bytes]" — default policy
            parts = line[1:].split()
            if len(parts) >= 2 and parts[1] not in ('-', ''):
                rows.append({
                    'source':  source_label,
                    'table':   table,
                    'chain':   parts[0],
                    'rule':    f'(policy {parts[1]})',
                    'action':  parts[1],
                    'comment': '',
                    'is_meta': True,
                })
            continue
        if line in ('COMMIT', 'RETURN'):
            continue
        if not line.startswith(('-A ', '-I ', '-P ', '-N ')):
            continue

        parts = line.split()
        chain = parts[1] if len(parts) >= 2 else ''
        action = _action_iptables(line)
        comment = _comment_iptables(line)

        rows.append({
            'source':  source_label,
            'table':   table,
            'chain':   chain,
            'rule':    line,
            'port':    _ports_iptables(line),
            'action':  action,
            'comment': comment,
            'is_meta': False,
        })
    return rows


# ── pf parser (macOS) ────────────────────────────────────────────────────────

_PF_ACTIONS = ('pass', 'block', 'anchor', 'nat', 'rdr', 'scrub', 'dummynet', 'load')


def parse_pf(text: str, source_label: str) -> list[dict]:
    rows: list[dict] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        action = next((kw for kw in _PF_ACTIONS if line.startswith(kw)), '')
        if not action:
            continue

        direction = next(
            (d for d in ('in', 'out') if re.search(r'\b' + d + r'\b', line)),
            'all',
        )

        m_if = re.search(r'\bon\s+(\S+)', line)
        iface = m_if.group(1) if m_if else 'any'

        port_matches = re.findall(r'\bport\s+(\S+)', line)
        port = ', '.join(port_matches)

        rows.append({
            'source':  source_label,
            'table':   direction,
            'chain':   iface,
            'rule':    line,
            'port':    port,
            'action':  action,
            'comment': '',
            'is_meta': False,
        })
    return rows


# ── Worker for live ruleset (pkexec) ─────────────────────────────────────────

class LiveRulesetWorker(QThread):
    done  = Signal(str)   # raw nft output
    error = Signal(str)

    def run(self) -> None:
        if not _CMD_PKEXEC or not _CMD_NFT:
            self.error.emit(tr("fw_err_no_pkexec"))
            return
        try:
            proc = subprocess.run(
                [_CMD_PKEXEC, _CMD_NFT, 'list', 'ruleset'],
                capture_output=True, text=True, timeout=30,
            )
            if proc.returncode != 0:
                self.error.emit(proc.stderr.strip() or tr("fw_err_pkexec_fail"))
            else:
                self.done.emit(proc.stdout)
        except subprocess.TimeoutExpired:
            self.error.emit(tr("fw_err_timeout"))
        except Exception as exc:
            self.error.emit(str(exc))


class LiveRulesetWorkerMacos(QThread):
    done  = Signal(str)
    error = Signal(str)

    def run(self) -> None:
        try:
            proc = subprocess.run(
                ['osascript', '-e',
                 'do shell script "pfctl -sr" with administrator privileges'],
                capture_output=True, text=True, timeout=60,
            )
            if proc.returncode != 0:
                self.error.emit(proc.stderr.strip() or tr("fw_err_pkexec_fail"))
            else:
                self.done.emit(proc.stdout)
        except subprocess.TimeoutExpired:
            self.error.emit(tr("fw_err_timeout"))
        except Exception as exc:
            self.error.emit(str(exc))


# ── Action color ──────────────────────────────────────────────────────────────

def _action_color(action: str) -> QColor | None:
    a = action.lower()
    if a in ('accept', 'pass'):
        return QColor(color_ok())
    if a in ('drop', 'block'):
        return QColor(color_err())
    if a in ('reject', 'nat', 'rdr'):
        return _ORANGE
    if a in ('log', 'anchor', 'scrub', 'dummynet') or a.startswith(('jump', 'goto')):
        return _BLUE
    return None


# ── Page ──────────────────────────────────────────────────────────────────────

_SOURCE_NFT4     = 'nftables.conf'
_SOURCE_IP4      = 'iptables IPv4'
_SOURCE_IP6      = 'iptables IPv6'
_SOURCE_LIVE     = 'live (pkexec)'
_SOURCE_PF_FILE  = 'pf.conf'
_SOURCE_PF_LIVE  = 'live (pfctl)'

if _IS_MACOS:
    _ALL_SOURCES    = [_SOURCE_PF_FILE, _SOURCE_PF_LIVE]
    _DEFAULT_SOURCE = _SOURCE_PF_FILE
else:
    _ALL_SOURCES    = [_SOURCE_NFT4, _SOURCE_IP4, _SOURCE_IP6, _SOURCE_LIVE]
    _DEFAULT_SOURCE = _SOURCE_NFT4


class FirewallPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._rows: list[dict] = []
        self._worker: LiveRulesetWorker | None = None
        self._build_ui()
        self._load_source(_DEFAULT_SOURCE)

    # ── Layout ───────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Toolbar
        bar = QHBoxLayout()

        bar.addWidget(QLabel(tr("fw_source_lbl")))
        self._src_box = QComboBox()
        for s in _ALL_SOURCES:
            self._src_box.addItem(s)
        self._src_box.currentTextChanged.connect(self._on_source_changed)
        bar.addWidget(self._src_box)

        bar.addSpacing(16)
        bar.addWidget(QLabel(tr("fw_filter_lbl")))
        self._filter_edit = QLineEdit()
        self._filter_edit.setPlaceholderText(tr("fw_filter_ph"))
        self._filter_edit.setClearButtonEnabled(True)
        self._filter_edit.textChanged.connect(self._apply_filter)
        bar.addWidget(self._filter_edit, 1)

        self._btn_refresh = QPushButton(tr("common_refresh"))
        self._btn_refresh.clicked.connect(self._on_refresh)
        bar.addWidget(self._btn_refresh)

        self._btn_export = QPushButton("Export")
        self._btn_export.setFixedWidth(80)
        self._btn_export.clicked.connect(self._export)
        bar.addWidget(self._btn_export)

        layout.addLayout(bar)

        # Status
        self._lbl_status = QLabel("")
        self._lbl_status.setStyleSheet("color: palette(mid);")
        layout.addWidget(self._lbl_status)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(sep)

        # Legend
        legend = QHBoxLayout()
        legend.addStretch()
        for color_str, label in [
            (color_ok(),    "accept"),
            (color_err(),   "drop"),
            (_ORANGE.name(), "reject"),
            (_BLUE.name(),  "jump / log"),
        ]:
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {color_str}; font-size: 10px;")
            legend.addWidget(dot)
            legend.addWidget(QLabel(label))
            legend.addSpacing(12)
        layout.addLayout(legend)

        # Table
        cols = [
            tr("fw_col_table"), tr("fw_col_chain"),
            tr("fw_col_rule"), tr("fw_col_port"),
            tr("fw_col_action"), tr("fw_col_comment"),
        ]
        self._table = QTableWidget(0, len(cols))
        self._table.setHorizontalHeaderLabels(cols)
        hh = self._table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)
        self._table.setFont(QFont('Menlo' if _IS_MACOS else 'Monospace', 9))
        self._table.setWordWrap(False)
        layout.addWidget(self._table, 1)

    # ── Source logic ─────────────────────────────────────────────────────────

    def _on_source_changed(self, source: str) -> None:
        self._load_source(source)

    def _on_refresh(self) -> None:
        self._load_source(self._src_box.currentText())

    def _load_source(self, source: str) -> None:
        self._stop_worker()
        self._rows = []
        self._filter_edit.clear()

        if _IS_MACOS:
            if source == _SOURCE_PF_FILE:
                self._load_file(_PF_CONF, source, 'pf')
            elif source == _SOURCE_PF_LIVE:
                self._load_live()
        else:
            if source == _SOURCE_NFT4:
                self._load_file(_NFT_CONF, source, 'nft')
            elif source == _SOURCE_IP4:
                self._load_file(_IP4_RULES, source, 'ipt')
            elif source == _SOURCE_IP6:
                self._load_file(_IP6_RULES, source, 'ipt')
            elif source == _SOURCE_LIVE:
                self._load_live()

    def _load_file(self, path: Path, label: str, fmt: str) -> None:
        if not path.exists():
            self._lbl_status.setText(tr("fw_err_not_found", path=str(path)))
            self._populate([])
            return
        try:
            text = path.read_text(encoding='utf-8', errors='replace')
        except OSError as exc:
            self._lbl_status.setText(tr("common_error_prefix", msg=str(exc)))
            self._populate([])
            return

        if fmt == 'nft':
            rows = parse_nft(text, label)
        elif fmt == 'pf':
            rows = parse_pf(text, label)
        else:
            rows = parse_iptables(text, label)

        self._rows = rows
        self._populate(rows)
        n_rules = sum(1 for r in rows if not r.get('is_meta'))
        self._lbl_status.setText(tr("fw_status_loaded", path=str(path), n=n_rules))

    def _load_live(self) -> None:
        self._lbl_status.setText(tr("fw_status_pkexec"))
        self._btn_refresh.setEnabled(False)
        self._src_box.setEnabled(False)
        if _IS_MACOS:
            self._worker = LiveRulesetWorkerMacos()
        else:
            if not _CMD_PKEXEC or not _CMD_NFT:
                self._lbl_status.setText(tr("fw_err_no_pkexec"))
                self._populate([])
                self._btn_refresh.setEnabled(True)
                self._src_box.setEnabled(True)
                return
            self._worker = LiveRulesetWorker()
        self._worker.done.connect(self._on_live_done)
        self._worker.error.connect(self._on_live_error)
        self._worker.finished.connect(self._on_live_finished)
        self._worker.start()

    def _on_live_done(self, text: str) -> None:
        source = _SOURCE_PF_LIVE if _IS_MACOS else _SOURCE_LIVE
        rows = parse_pf(text, source) if _IS_MACOS else parse_nft(text, source)
        self._rows = rows
        self._populate(rows)
        n_rules = sum(1 for r in rows if not r.get('is_meta'))
        self._lbl_status.setText(tr("fw_status_live", n=n_rules))

    def _on_live_error(self, msg: str) -> None:
        self._lbl_status.setText(tr("common_error_prefix", msg=msg))
        self._populate([])

    def _on_live_finished(self) -> None:
        self._btn_refresh.setEnabled(True)
        self._src_box.setEnabled(True)
        self._worker = None

    def _stop_worker(self) -> None:
        if self._worker:
            try:
                self._worker.done.disconnect()
                self._worker.error.disconnect()
                self._worker.finished.disconnect()
            except Exception:
                pass
            self._worker.quit()
            self._worker.wait(3000)
            self._worker = None
        self._btn_refresh.setEnabled(True)
        self._src_box.setEnabled(True)

    # ── Table population ─────────────────────────────────────────────────────

    def _populate(self, rows: list[dict]) -> None:
        self._table.setRowCount(0)
        for row in rows:
            self._insert_row(row)

    def _insert_row(self, row: dict) -> None:
        r = self._table.rowCount()
        self._table.insertRow(r)

        is_meta = row.get('is_meta', False)
        values = [
            row.get('table', ''),
            row.get('chain', ''),
            row.get('rule', ''),
            row.get('port', ''),
            row.get('action', ''),
            row.get('comment', ''),
        ]

        for col, val in enumerate(values):
            item = QTableWidgetItem(val)
            item.setToolTip(val)

            if is_meta:
                from PySide6.QtGui import QPalette
                from PySide6.QtWidgets import QApplication
                dim = QApplication.palette().color(QPalette.ColorRole.PlaceholderText)
                item.setForeground(QBrush(dim))
                font = QFont('Menlo' if _IS_MACOS else 'Monospace', 9)
                font.setItalic(True)
                item.setFont(font)

            if col == 4 and not is_meta:
                c = _action_color(val)
                if c:
                    item.setForeground(QBrush(c))

            self._table.setItem(r, col, item)

    # ── Filter ───────────────────────────────────────────────────────────────

    def _export(self) -> None:
        from PySide6.QtWidgets import QMessageBox
        from datetime import datetime
        from nmlinux.export_manager import save_export
        from nmlinux.core.export_dialog import open_export_dialog

        filepath, fmt = open_export_dialog(self, "Export Firewall Rules", "firewall-rules")
        if not filepath:
            return

        data = {
            "timestamp": datetime.now().isoformat(),
            "module": "Firewall",
            "source": self._src_box.currentText(),
            "rules": self._rows,
        }
        error = save_export(data, fmt, filepath)
        if error:
            QMessageBox.warning(self, "Export Error", error)
        else:
            QMessageBox.information(self, "Export", f"Saved to:\n{filepath}")

    def _apply_filter(self, text: str) -> None:
        needle = text.lower()
        for row in range(self._table.rowCount()):
            if not needle:
                self._table.setRowHidden(row, False)
                continue
            visible = False
            for col in range(self._table.columnCount()):
                item = self._table.item(row, col)
                if item and needle in item.text().lower():
                    visible = True
                    break
            self._table.setRowHidden(row, not visible)

        # Update status count
        visible_count = sum(
            1 for r in range(self._table.rowCount())
            if not self._table.isRowHidden(r)
        )
        total = self._table.rowCount()
        if needle:
            self._lbl_status.setText(tr("fw_filter_result", shown=visible_count, total=total))
        else:
            n_rules = sum(1 for row in self._rows if not row.get('is_meta'))
            src = self._src_box.currentText()
            if src == _SOURCE_LIVE:
                self._lbl_status.setText(tr("fw_status_live", n=n_rules))
            else:
                path = {
                    _SOURCE_NFT4:    _NFT_CONF,
                    _SOURCE_IP4:     _IP4_RULES,
                    _SOURCE_IP6:     _IP6_RULES,
                    _SOURCE_PF_FILE: _PF_CONF,
                }.get(src, Path(src))
                self._lbl_status.setText(tr("fw_status_loaded", path=str(path), n=n_rules))
