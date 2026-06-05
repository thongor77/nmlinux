from __future__ import annotations

import os
import re
import shutil
import socket
import subprocess
from pathlib import Path

from PySide6.QtCore import Qt, QProcess, QThread, Signal
from PySide6.QtWidgets import (
    QAbstractItemView, QApplication, QDialog, QDialogButtonBox,
    QFrame, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QMessageBox, QPushButton, QTableWidget, QTableWidgetItem,
    QTextEdit, QVBoxLayout, QWidget, QComboBox,
)
from PySide6.QtGui import QFont

from nmlinux.core.cli_bar import get_cli_bar
from nmlinux.core.i18n import tr


_SSH_DIR = Path.home() / ".ssh"


# ── Pure functions ─────────────────────────────────────────────────────────

def _parse_keygen_line(line: str) -> dict | None:
    """Parse one line of `ssh-keygen -l -f` output.

    Format: '256 SHA256:xxx comment (ED25519)'
    """
    m = re.match(r"(\d+)\s+(SHA256:\S+)\s+(.*)\s+\((\w+)\)", line.strip())
    if not m:
        return None
    return {
        "bits":        int(m.group(1)),
        "fingerprint": m.group(2),
        "comment":     m.group(3).strip(),
        "type":        m.group(4),
    }


def _scan_keys(ssh_dir: Path) -> list[dict]:
    """Return list of complete key pairs found in ssh_dir."""
    results = []
    for pub in sorted(ssh_dir.glob("*.pub")):
        priv = pub.with_suffix("")
        if not priv.exists():
            continue
        try:
            proc = subprocess.run(
                ["ssh-keygen", "-l", "-f", str(pub)],
                capture_output=True, text=True, timeout=5,
            )
        except Exception:
            continue
        if proc.returncode != 0:
            continue
        info = _parse_keygen_line(proc.stdout.strip())
        if not info:
            continue
        results.append({
            **info,
            "file":      pub.stem,
            "pub_path":  pub,
            "priv_path": priv,
        })
    return results


def _keygen_args(key_type: str, path: Path, comment: str, passphrase: str) -> list[str]:
    """Build the ssh-keygen argument list."""
    args = ["ssh-keygen"]
    if key_type == "ED25519":
        args += ["-t", "ed25519"]
    else:
        args += ["-t", "rsa", "-b", "4096"]
    args += ["-f", str(path), "-C", comment, "-N", passphrase]
    return args


# ── Worker ─────────────────────────────────────────────────────────────────

class _KeyGenWorker(QThread):
    success = Signal(str)   # key stem name
    error   = Signal(str)

    def __init__(self, args: list[str], name: str) -> None:
        super().__init__()
        self._args = args
        self._name = name

    def run(self) -> None:
        try:
            proc = subprocess.run(
                self._args, capture_output=True, text=True, timeout=30,
            )
            if proc.returncode == 0:
                self.success.emit(self._name)
            else:
                msg = proc.stderr.strip() or proc.stdout.strip()
                self.error.emit(msg)
        except Exception as exc:
            self.error.emit(str(exc))


# ── Generation dialog ──────────────────────────────────────────────────────

class _KeyGenDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("ssh_keys_dlg_gen_title"))
        self.setMinimumWidth(420)
        self._user_edited_file = False
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        def _row(label: str, widget) -> None:
            h = QHBoxLayout()
            lbl = QLabel(label + ":")
            lbl.setFixedWidth(120)
            h.addWidget(lbl)
            h.addWidget(widget, 1)
            layout.addLayout(h)

        # Type
        self._type_combo = QComboBox()
        self._type_combo.addItems(["ED25519", "RSA 4096"])
        self._type_combo.currentTextChanged.connect(self._on_type_changed)
        _row(tr("ssh_keys_dlg_gen_type"), self._type_combo)

        # Filename
        self._file_edit = QLineEdit("id_ed25519")
        self._file_edit.textEdited.connect(self._on_file_edited)
        _row(tr("ssh_keys_dlg_gen_file"), self._file_edit)

        # Comment
        try:
            default_comment = f"{os.environ.get('USER', 'user')}@{socket.gethostname()}"
        except Exception:
            default_comment = "user@host"
        self._comment_edit = QLineEdit(default_comment)
        _row(tr("ssh_keys_dlg_gen_comment"), self._comment_edit)

        # Passphrase
        self._pass_edit = QLineEdit()
        self._pass_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._pass_edit.setPlaceholderText("(vide = sans protection)")
        self._pass_edit.textChanged.connect(self._validate)
        _row(tr("ssh_keys_dlg_gen_passphrase"), self._pass_edit)

        # Confirm
        self._confirm_edit = QLineEdit()
        self._confirm_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._confirm_edit.textChanged.connect(self._validate)
        _row(tr("ssh_keys_dlg_gen_confirm"), self._confirm_edit)

        # Mismatch label
        self._mismatch_lbl = QLabel(tr("ssh_keys_err_passphrase_mismatch"))
        self._mismatch_lbl.setStyleSheet("color: #f38ba8; font-size: 11px;")
        self._mismatch_lbl.setVisible(False)
        layout.addWidget(self._mismatch_lbl)

        # Buttons
        self._btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._btns.accepted.connect(self.accept)
        self._btns.rejected.connect(self.reject)
        layout.addWidget(self._btns)

    def _on_type_changed(self, text: str) -> None:
        if not self._user_edited_file:
            self._file_edit.setText("id_ed25519" if "ED25519" in text else "id_rsa")

    def _on_file_edited(self) -> None:
        self._user_edited_file = True

    def _validate(self) -> None:
        p = self._pass_edit.text()
        c = self._confirm_edit.text()
        mismatch = bool(p) and p != c
        self._mismatch_lbl.setVisible(mismatch)
        self._btns.button(QDialogButtonBox.StandardButton.Ok).setEnabled(not mismatch)

    def values(self) -> tuple[str, str, str, str]:
        """Return (key_type, filename_stem, comment, passphrase)."""
        key_type = "ED25519" if "ED25519" in self._type_combo.currentText() else "RSA"
        return (
            key_type,
            self._file_edit.text().strip() or "id_ed25519",
            self._comment_edit.text().strip(),
            self._pass_edit.text(),
        )


# ── Deploy bar ─────────────────────────────────────────────────────────────

class _DeployBar(QWidget):
    """Inline terminal for ssh-copy-id, shown/hidden on demand."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._process = None
        self._pub_path: str = ""
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 4, 0, 0)
        root.setSpacing(4)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        root.addWidget(sep)

        # Toolbar
        bar = QHBoxLayout()
        bar.setSpacing(6)

        self._user_host = QLineEdit()
        self._user_host.setPlaceholderText(tr("ssh_keys_deploy_user_host"))

        port_lbl = QLabel(tr("ssh_keys_deploy_port") + ":")
        port_lbl.setStyleSheet("font-size: 12px;")
        self._port = QLineEdit("22")
        self._port.setFixedWidth(50)

        self._btn_run = QPushButton(tr("ssh_keys_deploy_btn_run"))
        self._btn_run.clicked.connect(self._run)

        self._btn_close = QPushButton(tr("ssh_keys_deploy_btn_close"))
        self._btn_close.clicked.connect(self._close_bar)

        bar.addWidget(self._user_host, 1)
        bar.addWidget(port_lbl)
        bar.addWidget(self._port)
        bar.addWidget(self._btn_run)
        bar.addWidget(self._btn_close)
        root.addLayout(bar)

        # Output area
        self._output = QTextEdit()
        self._output.setReadOnly(True)
        self._output.setMaximumHeight(160)
        mono = QFont("Monospace")
        mono.setStyleHint(QFont.StyleHint.Monospace)
        self._output.setFont(mono)
        self._output.setStyleSheet("background: #1e1e2e; color: #cdd6f4;")
        root.addWidget(self._output)

        # Stdin row (for password prompts)
        stdin_row = QHBoxLayout()
        self._stdin = QLineEdit()
        self._stdin.setEchoMode(QLineEdit.EchoMode.Password)
        self._stdin.setPlaceholderText("Mot de passe / passphrase (si demandé)")
        self._stdin.returnPressed.connect(self._send_stdin)
        btn_send = QPushButton("↵")
        btn_send.setFixedWidth(32)
        btn_send.clicked.connect(self._send_stdin)
        stdin_row.addWidget(self._stdin, 1)
        stdin_row.addWidget(btn_send)
        root.addLayout(stdin_row)

    def set_key(self, pub_path: str) -> None:
        self._pub_path = pub_path
        self._output.clear()

    def _run(self) -> None:
        if not shutil.which("ssh-copy-id"):
            self._output.setPlainText(tr("ssh_keys_deploy_no_tool"))
            return

        user_host = self._user_host.text().strip()
        if not user_host:
            return

        port = self._port.text().strip() or "22"
        self._output.clear()
        self._terminate_process()

        self._process = QProcess(self)
        self._process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self._process.readyRead.connect(self._on_output)
        self._process.finished.connect(self._on_finished)

        args = ["-i", self._pub_path, "-p", port, user_host]
        self._process.start("ssh-copy-id", args)

        cli = get_cli_bar()
        if cli:
            cli.set_cmd(f"ssh-copy-id -i {self._pub_path} -p {port} {user_host}")

    def _on_output(self) -> None:
        if self._process:
            data = bytes(self._process.readAll()).decode("utf-8", errors="replace")
            self._output.append(data.rstrip("\n"))

    def _on_finished(self, code: int) -> None:
        self._output.append(f"\n── Terminé (code {code}) ──")
        self._process = None

    def _send_stdin(self) -> None:
        if self._process and self._process.state() != self._process.ProcessState.NotRunning:
            text = self._stdin.text() + "\n"
            self._process.write(text.encode())
            self._stdin.clear()

    def _terminate_process(self) -> None:
        if self._process:
            self._process.terminate()
            self._process.waitForFinished(2000)
            self._process = None

    def _close_bar(self) -> None:
        self._terminate_process()
        self.hide()


# ── Main page ──────────────────────────────────────────────────────────────

class SshKeysPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._worker: _KeyGenWorker | None = None
        self._keys: list[dict] = []
        self._build_ui()
        self._load()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 8)
        root.setSpacing(8)

        # ── Toolbar ───────────────────────────────────────────────────────
        bar = QHBoxLayout()
        bar.setSpacing(6)

        self._btn_generate = QPushButton(tr("ssh_keys_btn_generate"))
        self._btn_generate.clicked.connect(self._generate)

        self._btn_copy = QPushButton(tr("ssh_keys_btn_copy_pub"))
        self._btn_copy.setEnabled(False)
        self._btn_copy.clicked.connect(self._copy_pub)

        self._btn_deploy = QPushButton(tr("ssh_keys_btn_deploy"))
        self._btn_deploy.setEnabled(False)
        self._btn_deploy.clicked.connect(self._deploy)

        self._btn_delete = QPushButton(tr("ssh_keys_btn_delete"))
        self._btn_delete.setEnabled(False)
        self._btn_delete.clicked.connect(self._delete)

        self._btn_refresh = QPushButton(tr("ssh_keys_btn_refresh"))
        self._btn_refresh.clicked.connect(self._load)

        for btn in (self._btn_generate, self._btn_copy,
                    self._btn_deploy, self._btn_delete, self._btn_refresh):
            bar.addWidget(btn)
        bar.addStretch(1)
        root.addLayout(bar)

        # ── Table ─────────────────────────────────────────────────────────
        self._table = QTableWidget(0, 5)
        self._table.setHorizontalHeaderLabels([
            tr("ssh_keys_col_file"),
            tr("ssh_keys_col_type"),
            tr("ssh_keys_col_bits"),
            tr("ssh_keys_col_comment"),
            tr("ssh_keys_col_fingerprint"),
        ])
        hdr = self._table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setFrameShape(QFrame.Shape.NoFrame)
        self._table.itemSelectionChanged.connect(self._on_selection)
        root.addWidget(self._table, 1)

        # ── Deploy bar (hidden by default) ─────────────────────────────────
        self._deploy_bar = _DeployBar()
        self._deploy_bar.hide()
        root.addWidget(self._deploy_bar)

        # ── Status ────────────────────────────────────────────────────────
        self._status = QLabel("")
        self._status.setStyleSheet("font-size: 12px; color: gray;")
        root.addWidget(self._status)

    # ── Data ──────────────────────────────────────────────────────────────────

    def _load(self) -> None:
        _SSH_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
        self._keys = _scan_keys(_SSH_DIR)
        self._populate()
        cli = get_cli_bar()
        if cli:
            cli.set_cmd("ls -la ~/.ssh/")

    def _populate(self) -> None:
        self._table.setRowCount(0)
        for k in self._keys:
            row = self._table.rowCount()
            self._table.insertRow(row)
            for col, val in enumerate([
                k["file"],
                k["type"],
                str(k["bits"]),
                k["comment"],
                k["fingerprint"],
            ]):
                item = QTableWidgetItem(val)
                self._table.setItem(row, col, item)
        self._on_selection()
        if not self._keys:
            self._set_status(tr("ssh_keys_no_keys"), "gray")

    def _on_selection(self) -> None:
        has = bool(self._table.selectedItems())
        self._btn_copy.setEnabled(has)
        self._btn_deploy.setEnabled(has)
        self._btn_delete.setEnabled(has)

    def _selected_key(self) -> dict | None:
        row = self._table.currentRow()
        if row < 0 or row >= len(self._keys):
            return None
        return self._keys[row]

    def _set_status(self, msg: str, color: str = "gray") -> None:
        self._status.setText(msg)
        self._status.setStyleSheet(f"font-size: 12px; color: {color};")

    # ── Actions ───────────────────────────────────────────────────────────────

    def showEvent(self, event) -> None:
        super().showEvent(event)
        cli = get_cli_bar()
        if cli:
            cli.set_cmd("ls -la ~/.ssh/")

    def _generate(self) -> None:
        dlg = _KeyGenDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        key_type, stem, comment, passphrase = dlg.values()
        path = _SSH_DIR / stem

        if path.exists():
            ans = QMessageBox.question(
                self,
                tr("ssh_keys_dlg_overwrite_title"),
                tr("ssh_keys_dlg_overwrite_msg", name=stem),
            )
            if ans != QMessageBox.StandardButton.Yes:
                return
            path.unlink(missing_ok=True)
            Path(str(path) + ".pub").unlink(missing_ok=True)

        args = _keygen_args(key_type, path, comment, passphrase)
        cli = get_cli_bar()
        if cli:
            t = "ed25519" if key_type == "ED25519" else "rsa -b 4096"
            cli.set_cmd(f"ssh-keygen -t {t} -f ~/.ssh/{stem} -C \"{comment}\"")

        self._btn_generate.setEnabled(False)
        self._worker = _KeyGenWorker(args, stem)
        self._worker.success.connect(self._on_gen_success)
        self._worker.error.connect(self._on_gen_error)
        self._worker.finished.connect(lambda: self._btn_generate.setEnabled(True))
        self._worker.start()

    def _on_gen_success(self, name: str) -> None:
        self._set_status(tr("ssh_keys_generated", name=name), "#a6e3a1")
        self._load()

    def _on_gen_error(self, msg: str) -> None:
        self._set_status(tr("ssh_keys_err_keygen", msg=msg), "#f38ba8")

    def _copy_pub(self) -> None:
        key = self._selected_key()
        if key is None:
            return
        try:
            content = key["pub_path"].read_text(encoding="utf-8").strip()
            QApplication.clipboard().setText(content)
            self._set_status(tr("ssh_keys_copied"), "#a6e3a1")
        except OSError as exc:
            self._set_status(str(exc), "#f38ba8")

    def _deploy(self) -> None:
        key = self._selected_key()
        if key is None:
            return
        self._deploy_bar.set_key(str(key["pub_path"]))
        self._deploy_bar.show()

    def _delete(self) -> None:
        key = self._selected_key()
        if key is None:
            return
        ans = QMessageBox.question(
            self,
            tr("ssh_keys_dlg_del_title"),
            tr("ssh_keys_dlg_del_msg", name=key["file"]),
        )
        if ans != QMessageBox.StandardButton.Yes:
            return
        try:
            key["pub_path"].unlink(missing_ok=True)
            key["priv_path"].unlink(missing_ok=True)
            self._set_status(tr("ssh_keys_deleted", name=key["file"]), "#a6e3a1")
        except OSError as exc:
            self._set_status(str(exc), "#f38ba8")
        self._load()
