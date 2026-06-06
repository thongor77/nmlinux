from __future__ import annotations

import platform
import re
import subprocess
import tempfile
import os

_IS_MACOS = platform.system() == 'Darwin'

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QDialog, QDialogButtonBox,
    QFrame, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QMessageBox, QPushButton,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from nmlinux.core.i18n import tr

_HOSTS_FILE = "/etc/hosts"


# ── Parsing ───────────────────────────────────────────────────────────────────

def _parse_hosts(text: str) -> list[dict]:
    """Return list of dicts: {enabled, ip, hostnames, comment, raw}."""
    entries = []
    for line in text.splitlines():
        raw = line
        enabled = not line.strip().startswith("#")
        # Strip leading # for disabled entries
        clean = line.lstrip("#").strip() if not enabled else line.strip()
        if not clean:
            entries.append({"enabled": True, "ip": "", "hostnames": "",
                            "comment": "", "raw": raw, "blank": True})
            continue
        # Inline comment
        comment = ""
        if "#" in clean:
            parts = clean.split("#", 1)
            clean, comment = parts[0].strip(), parts[1].strip()
        tokens = clean.split()
        if not tokens:
            entries.append({"enabled": enabled, "ip": "", "hostnames": "",
                            "comment": comment, "raw": raw, "blank": False})
            continue
        ip = tokens[0]
        hostnames = " ".join(tokens[1:])
        entries.append({"enabled": enabled, "ip": ip, "hostnames": hostnames,
                        "comment": comment, "raw": raw, "blank": False})
    return entries


def _entry_to_line(e: dict) -> str:
    if e.get("blank"):
        return ""
    ip, hostnames, comment = e["ip"], e["hostnames"], e["comment"]
    if not ip and not hostnames:
        line = f"# {comment}" if comment else ""
    else:
        line = f"{ip}\t{hostnames}"
        if comment:
            line += f"\t# {comment}"
    return line if e["enabled"] else f"# {line}"


# ── Add/Edit dialog ───────────────────────────────────────────────────────────

class _EntryDialog(QDialog):
    def __init__(self, parent=None, ip="", hostnames="", comment="") -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("hosts_dlg_title"))
        self.setMinimumWidth(400)

        form = QVBoxLayout(self)

        def _row(lbl, widget):
            h = QHBoxLayout()
            l = QLabel(lbl)
            l.setFixedWidth(100)
            h.addWidget(l)
            h.addWidget(widget, 1)
            form.addLayout(h)

        self._ip = QLineEdit(ip)
        self._ip.setPlaceholderText("192.168.1.100")
        _row(tr("hosts_lbl_ip"), self._ip)

        self._hostnames = QLineEdit(hostnames)
        self._hostnames.setPlaceholderText("server.local server")
        _row(tr("hosts_lbl_hostnames"), self._hostnames)

        self._comment = QLineEdit(comment)
        self._comment.setPlaceholderText(tr("hosts_lbl_comment_hint"))
        _row(tr("hosts_lbl_comment"), self._comment)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        form.addWidget(btns)

    def values(self) -> tuple[str, str, str]:
        return (self._ip.text().strip(),
                self._hostnames.text().strip(),
                self._comment.text().strip())


# ── Page ──────────────────────────────────────────────────────────────────────

class HostsPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._entries: list[dict] = []
        self._build_ui()
        self._load()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 8)
        root.setSpacing(8)

        # ── Toolbar ───────────────────────────────────────────────────────
        bar = QHBoxLayout()

        self._btn_add = QPushButton(tr("hosts_btn_add"))
        self._btn_add.clicked.connect(self._add_entry)

        self._btn_edit = QPushButton(tr("hosts_btn_edit"))
        self._btn_edit.clicked.connect(self._edit_entry)
        self._btn_edit.setEnabled(False)

        self._btn_del = QPushButton(tr("hosts_btn_delete"))
        self._btn_del.clicked.connect(self._delete_entry)
        self._btn_del.setEnabled(False)

        self._btn_toggle = QPushButton(tr("hosts_btn_toggle"))
        self._btn_toggle.clicked.connect(self._toggle_entry)
        self._btn_toggle.setEnabled(False)

        self._btn_reload = QPushButton(tr("hosts_btn_reload"))
        self._btn_reload.clicked.connect(self._load)

        self._btn_save = QPushButton(tr("hosts_btn_save"))
        self._btn_save.setStyleSheet("font-weight: bold;")
        self._btn_save.clicked.connect(self._save)

        self._filter = QLineEdit()
        self._filter.setPlaceholderText(tr("hosts_filter_placeholder"))
        self._filter.textChanged.connect(self._apply_filter)
        self._filter.setFixedWidth(180)

        for w in (self._btn_add, self._btn_edit, self._btn_del,
                  self._btn_toggle, self._btn_reload):
            bar.addWidget(w)
        bar.addStretch(1)
        bar.addWidget(self._filter)
        bar.addWidget(self._btn_save)
        root.addLayout(bar)

        # ── Table ─────────────────────────────────────────────────────────
        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels([
            tr("hosts_col_enabled"),
            tr("hosts_col_ip"),
            tr("hosts_col_hostnames"),
            tr("hosts_col_comment"),
        ])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setFrameShape(QFrame.Shape.NoFrame)
        self._table.itemSelectionChanged.connect(self._on_selection)
        root.addWidget(self._table, 1)

        # ── Status ────────────────────────────────────────────────────────
        self._status = QLabel("")
        self._status.setStyleSheet("font-size: 12px; color: gray;")
        root.addWidget(self._status)

    # ── Data ──────────────────────────────────────────────────────────────────

    def _load(self) -> None:
        try:
            with open(_HOSTS_FILE, encoding="utf-8") as f:
                text = f.read()
        except OSError as exc:
            self._status.setText(str(exc))
            return
        self._entries = _parse_hosts(text)
        self._populate(self._entries)
        self._status.setText(tr("hosts_loaded", path=_HOSTS_FILE))

    def _populate(self, entries: list[dict]) -> None:
        self._table.setRowCount(0)
        for e in entries:
            if e.get("blank") or (not e["ip"] and not e["hostnames"]):
                continue
            row = self._table.rowCount()
            self._table.insertRow(row)

            enabled_item = QTableWidgetItem("✓" if e["enabled"] else "")
            enabled_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if not e["enabled"]:
                enabled_item.setForeground(Qt.GlobalColor.gray)
            self._table.setItem(row, 0, enabled_item)

            for col, key in enumerate(("ip", "hostnames", "comment"), start=1):
                item = QTableWidgetItem(e[key])
                if not e["enabled"]:
                    item.setForeground(Qt.GlobalColor.gray)
                self._table.setItem(row, col, item)

            # Store entry index in user role
            self._table.item(row, 0).setData(Qt.ItemDataRole.UserRole,
                                             self._entries.index(e))

    def _apply_filter(self, text: str) -> None:
        text = text.lower()
        filtered = [e for e in self._entries
                    if not e.get("blank") and (e["ip"] or e["hostnames"])
                    and (not text or text in e["ip"].lower()
                         or text in e["hostnames"].lower())]
        self._populate(filtered)

    def _selected_entry_idx(self) -> int | None:
        rows = self._table.selectedItems()
        if not rows:
            return None
        return self._table.item(self._table.currentRow(), 0).data(
            Qt.ItemDataRole.UserRole
        )

    def _on_selection(self) -> None:
        has = bool(self._table.selectedItems())
        self._btn_edit.setEnabled(has)
        self._btn_del.setEnabled(has)
        self._btn_toggle.setEnabled(has)

    # ── Actions ───────────────────────────────────────────────────────────────

    def _add_entry(self) -> None:
        dlg = _EntryDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        ip, hostnames, comment = dlg.values()
        if not ip or not hostnames:
            return
        self._entries.append({"enabled": True, "ip": ip,
                              "hostnames": hostnames, "comment": comment,
                              "raw": "", "blank": False})
        self._populate(self._entries)
        self._status.setText(tr("hosts_modified"))

    def _edit_entry(self) -> None:
        idx = self._selected_entry_idx()
        if idx is None:
            return
        e = self._entries[idx]
        dlg = _EntryDialog(self, e["ip"], e["hostnames"], e["comment"])
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        ip, hostnames, comment = dlg.values()
        e["ip"], e["hostnames"], e["comment"] = ip, hostnames, comment
        self._populate(self._entries)
        self._status.setText(tr("hosts_modified"))

    def _delete_entry(self) -> None:
        idx = self._selected_entry_idx()
        if idx is None:
            return
        e = self._entries[idx]
        reply = QMessageBox.question(
            self, tr("hosts_dlg_del_title"),
            tr("hosts_dlg_del_msg", host=e["hostnames"] or e["ip"]),
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self._entries.pop(idx)
        self._populate(self._entries)
        self._status.setText(tr("hosts_modified"))

    def _toggle_entry(self) -> None:
        idx = self._selected_entry_idx()
        if idx is None:
            return
        self._entries[idx]["enabled"] = not self._entries[idx]["enabled"]
        self._populate(self._entries)
        self._status.setText(tr("hosts_modified"))

    def _save(self) -> None:
        lines = [_entry_to_line(e) for e in self._entries]
        content = "\n".join(lines) + "\n"

        try:
            fd, tmppath = tempfile.mkstemp(suffix=".hosts")
            with os.fdopen(fd, "w") as f:
                f.write(content)

            if _IS_MACOS:
                proc = subprocess.run(
                    ['osascript', '-e',
                     f'do shell script "cp {tmppath} /etc/hosts"'
                     f' with administrator privileges'],
                    capture_output=True, timeout=60,
                )
            else:
                proc = subprocess.run(
                    ["pkexec", "cp", tmppath, _HOSTS_FILE],
                    capture_output=True, timeout=30,
                )
            os.unlink(tmppath)

            if proc.returncode != 0:
                self._status.setText(tr("hosts_save_err",
                                        msg=proc.stderr.decode()[:80]))
                self._status.setStyleSheet("font-size: 12px; color: #f38ba8;")
            else:
                self._status.setText(tr("hosts_saved"))
                self._status.setStyleSheet("font-size: 12px; color: #a6e3a1;")
        except Exception as exc:
            self._status.setText(str(exc))
            self._status.setStyleSheet("font-size: 12px; color: #f38ba8;")
