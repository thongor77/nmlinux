# SSH Key Manager Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a SSH Key Manager page to NMLinux that lists `~/.ssh/` key pairs, generates new Ed25519/RSA keys, copies the public key to clipboard, deploys via `ssh-copy-id` in an inline terminal, and deletes key pairs.

**Architecture:** Single file `nmlinux/pages/ssh_keys.py` following the `hosts.py` pattern (QTableWidget + toolbar + status bar). A `_DeployBar` widget (hidden by default) appears below the table when the user clicks Deploy, running `ssh-copy-id` via `QProcess`. Key generation runs in a `QThread`.

**Tech Stack:** PySide6, Python stdlib (`subprocess`, `os`, `re`, `shutil`, `pathlib`), `ssh-keygen`, `ssh-copy-id`.

---

## Files

| Action | Path |
|---|---|
| Create | `nmlinux/pages/ssh_keys.py` |
| Create | `tests/test_ssh_keys.py` |
| Modify | `nmlinux/core/i18n.py` |
| Modify | `nmlinux/window.py` |

---

## Task 1 — Pure functions + tests

**Files:**
- Create: `tests/test_ssh_keys.py`
- Create: `nmlinux/pages/ssh_keys.py` (pure functions only)

- [ ] **Step 1: Write failing tests**

Create `tests/test_ssh_keys.py`:

```python
from __future__ import annotations
import os
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from nmlinux.pages.ssh_keys import _parse_keygen_line, _scan_keys, _keygen_args


# ── _parse_keygen_line ─────────────────────────────────────────────────────

def test_parse_ed25519():
    line = "256 SHA256:AbCdEfGhIjKlMnOpQrStUvWxYz user@host (ED25519)"
    result = _parse_keygen_line(line)
    assert result is not None
    assert result["bits"] == 256
    assert result["fingerprint"] == "SHA256:AbCdEfGhIjKlMnOpQrStUvWxYz"
    assert result["comment"] == "user@host"
    assert result["type"] == "ED25519"

def test_parse_rsa():
    line = "4096 SHA256:XxXxXxXxXxXxXxXxXxXxXxXxXx admin@server (RSA)"
    result = _parse_keygen_line(line)
    assert result is not None
    assert result["bits"] == 4096
    assert result["type"] == "RSA"

def test_parse_comment_with_spaces():
    line = "256 SHA256:AAAAbbbbCCCCdddd my laptop key (ED25519)"
    result = _parse_keygen_line(line)
    assert result is not None
    assert result["comment"] == "my laptop key"

def test_parse_invalid_returns_none():
    assert _parse_keygen_line("not a valid line") is None
    assert _parse_keygen_line("") is None


# ── _scan_keys ─────────────────────────────────────────────────────────────

def test_scan_keys_returns_only_complete_pairs(tmp_path):
    # Create a complete pair
    (tmp_path / "id_ed25519").write_text("PRIVATE")
    (tmp_path / "id_ed25519.pub").write_text("PUBLIC")
    # Create an orphan .pub (no private key)
    (tmp_path / "id_rsa.pub").write_text("PUBLIC_ONLY")

    fake_output = "256 SHA256:AbCdEfGh user@host (ED25519)\n"

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0, stdout=fake_output
        )
        results = _scan_keys(tmp_path)

    assert len(results) == 1
    assert results[0]["file"] == "id_ed25519"
    assert results[0]["type"] == "ED25519"
    assert results[0]["pub_path"] == tmp_path / "id_ed25519.pub"
    assert results[0]["priv_path"] == tmp_path / "id_ed25519"

def test_scan_keys_empty_dir(tmp_path):
    results = _scan_keys(tmp_path)
    assert results == []

def test_scan_keys_keygen_fails_skips_key(tmp_path):
    (tmp_path / "id_ed25519").write_text("PRIVATE")
    (tmp_path / "id_ed25519.pub").write_text("PUBLIC")

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        results = _scan_keys(tmp_path)

    assert results == []


# ── _keygen_args ───────────────────────────────────────────────────────────

def test_keygen_args_ed25519():
    args = _keygen_args("ED25519", Path("/home/user/.ssh/id_ed25519"), "user@host", "")
    assert args[0] == "ssh-keygen"
    assert "-t" in args
    assert "ed25519" in args
    assert "-f" in args
    assert "/home/user/.ssh/id_ed25519" in args
    assert "-C" in args
    assert "user@host" in args
    assert "-N" in args
    assert "" in args

def test_keygen_args_rsa():
    args = _keygen_args("RSA", Path("/home/user/.ssh/id_rsa"), "comment", "mypass")
    assert "rsa" in args
    assert "-b" in args
    assert "4096" in args
    assert "mypass" in args

def test_keygen_args_no_xfreerdp_as_first():
    args = _keygen_args("ED25519", Path("/tmp/key"), "c", "")
    assert args[0] == "ssh-keygen"
```

- [ ] **Step 2: Run to verify failure**

```bash
cd /home/luust/claude-projects/nmlinux
python -m pytest tests/test_ssh_keys.py -v 2>&1 | head -30
```

Expected: `ModuleNotFoundError: No module named 'nmlinux.pages.ssh_keys'`

- [ ] **Step 3: Create `nmlinux/pages/ssh_keys.py` with pure functions**

```python
from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path


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
    """Return list of complete key pairs found in ssh_dir.

    Each dict: {file, type, bits, fingerprint, comment, pub_path, priv_path}
    Pairs without a matching private key are silently skipped.
    """
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
            "file":     pub.stem,
            "pub_path": pub,
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
```

- [ ] **Step 4: Run tests — all must pass**

```bash
cd /home/luust/claude-projects/nmlinux
python -m pytest tests/test_ssh_keys.py -v
```

Expected: `9 passed`

- [ ] **Step 5: Commit**

```bash
cd /home/luust/claude-projects/nmlinux
git add tests/test_ssh_keys.py nmlinux/pages/ssh_keys.py
git commit -m "feat(ssh-keys): pure functions + tests (_parse_keygen_line, _scan_keys, _keygen_args)"
```

---

## Task 2 — i18n (4 langues)

**Files:**
- Modify: `nmlinux/core/i18n.py`

- [ ] **Step 1: Ajouter les clés françaises (ligne ~41, après `nav_hint_ssh`)**

Ouvrir `nmlinux/core/i18n.py`. Repérer la ligne contenant `"nav_hint_ssh"` dans le bloc `"fr"` (ligne ~41). Insérer **après** cette ligne :

```python
        "nav_ssh_keys":              "Clés SSH",
        "nav_hint_ssh_keys":         "Gère les clés SSH locales : lister, générer,\ncopier et déployer via ssh-copy-id.",

        # ── SSH Keys page ────────────────────────────────────────────────
        "ssh_keys_btn_generate":     "Générer",
        "ssh_keys_btn_copy_pub":     "Copier clé pub.",
        "ssh_keys_btn_deploy":       "Déployer",
        "ssh_keys_btn_delete":       "Supprimer",
        "ssh_keys_btn_refresh":      "Actualiser",
        "ssh_keys_col_file":         "Fichier",
        "ssh_keys_col_type":         "Type",
        "ssh_keys_col_bits":         "Bits",
        "ssh_keys_col_comment":      "Commentaire",
        "ssh_keys_col_fingerprint":  "Empreinte",
        "ssh_keys_dlg_gen_title":    "Générer une clé SSH",
        "ssh_keys_dlg_gen_type":     "Type",
        "ssh_keys_dlg_gen_file":     "Nom du fichier",
        "ssh_keys_dlg_gen_comment":  "Commentaire",
        "ssh_keys_dlg_gen_passphrase": "Passphrase",
        "ssh_keys_dlg_gen_confirm":  "Confirmer",
        "ssh_keys_dlg_overwrite_title": "Fichier existant",
        "ssh_keys_dlg_overwrite_msg": "La clé {name} existe déjà. Écraser ?",
        "ssh_keys_dlg_del_title":    "Supprimer la clé",
        "ssh_keys_dlg_del_msg":      "Supprimer la paire {name} ? Cette action est irréversible.",
        "ssh_keys_deploy_user_host": "utilisateur@hôte",
        "ssh_keys_deploy_port":      "Port",
        "ssh_keys_deploy_btn_run":   "Lancer",
        "ssh_keys_deploy_btn_close": "Fermer",
        "ssh_keys_deploy_no_tool":   "ssh-copy-id introuvable. Installez openssh-client.",
        "ssh_keys_generated":        "Clé {name} générée.",
        "ssh_keys_copied":           "Clé publique copiée dans le presse-papiers.",
        "ssh_keys_deleted":          "Paire {name} supprimée.",
        "ssh_keys_err_passphrase_mismatch": "Les passphrases ne correspondent pas.",
        "ssh_keys_err_keygen":       "Erreur : {msg}",
        "ssh_keys_no_keys":          "Aucune clé SSH trouvée dans ~/.ssh/",
```

- [ ] **Step 2: Ajouter les clés anglaises (ligne ~800, après `nav_hint_ssh` bloc `"en"`)**

```python
        "nav_ssh_keys":              "SSH Keys",
        "nav_hint_ssh_keys":         "Manage local SSH keys: list, generate,\ncopy and deploy via ssh-copy-id.",

        # ── SSH Keys page ────────────────────────────────────────────────
        "ssh_keys_btn_generate":     "Generate",
        "ssh_keys_btn_copy_pub":     "Copy Public Key",
        "ssh_keys_btn_deploy":       "Deploy",
        "ssh_keys_btn_delete":       "Delete",
        "ssh_keys_btn_refresh":      "Refresh",
        "ssh_keys_col_file":         "File",
        "ssh_keys_col_type":         "Type",
        "ssh_keys_col_bits":         "Bits",
        "ssh_keys_col_comment":      "Comment",
        "ssh_keys_col_fingerprint":  "Fingerprint",
        "ssh_keys_dlg_gen_title":    "Generate SSH Key",
        "ssh_keys_dlg_gen_type":     "Type",
        "ssh_keys_dlg_gen_file":     "Filename",
        "ssh_keys_dlg_gen_comment":  "Comment",
        "ssh_keys_dlg_gen_passphrase": "Passphrase",
        "ssh_keys_dlg_gen_confirm":  "Confirm",
        "ssh_keys_dlg_overwrite_title": "File Exists",
        "ssh_keys_dlg_overwrite_msg": "Key {name} already exists. Overwrite?",
        "ssh_keys_dlg_del_title":    "Delete Key",
        "ssh_keys_dlg_del_msg":      "Delete key pair {name}? This cannot be undone.",
        "ssh_keys_deploy_user_host": "user@host",
        "ssh_keys_deploy_port":      "Port",
        "ssh_keys_deploy_btn_run":   "Run",
        "ssh_keys_deploy_btn_close": "Close",
        "ssh_keys_deploy_no_tool":   "ssh-copy-id not found. Install openssh-client.",
        "ssh_keys_generated":        "Key {name} generated.",
        "ssh_keys_copied":           "Public key copied to clipboard.",
        "ssh_keys_deleted":          "Key pair {name} deleted.",
        "ssh_keys_err_passphrase_mismatch": "Passphrases do not match.",
        "ssh_keys_err_keygen":       "Error: {msg}",
        "ssh_keys_no_keys":          "No SSH keys found in ~/.ssh/",
```

- [ ] **Step 3: Ajouter les clés espagnoles (ligne ~1539, après `nav_hint_ssh` bloc `"es"`)**

```python
        "nav_ssh_keys":              "Claves SSH",
        "nav_hint_ssh_keys":         "Gestiona las claves SSH locales: listar, generar,\ncopiar y desplegar via ssh-copy-id.",

        # ── SSH Keys page ────────────────────────────────────────────────
        "ssh_keys_btn_generate":     "Generar",
        "ssh_keys_btn_copy_pub":     "Copiar clave pub.",
        "ssh_keys_btn_deploy":       "Desplegar",
        "ssh_keys_btn_delete":       "Eliminar",
        "ssh_keys_btn_refresh":      "Actualizar",
        "ssh_keys_col_file":         "Archivo",
        "ssh_keys_col_type":         "Tipo",
        "ssh_keys_col_bits":         "Bits",
        "ssh_keys_col_comment":      "Comentario",
        "ssh_keys_col_fingerprint":  "Huella",
        "ssh_keys_dlg_gen_title":    "Generar clave SSH",
        "ssh_keys_dlg_gen_type":     "Tipo",
        "ssh_keys_dlg_gen_file":     "Nombre de archivo",
        "ssh_keys_dlg_gen_comment":  "Comentario",
        "ssh_keys_dlg_gen_passphrase": "Frase de contraseña",
        "ssh_keys_dlg_gen_confirm":  "Confirmar",
        "ssh_keys_dlg_overwrite_title": "Archivo existente",
        "ssh_keys_dlg_overwrite_msg": "La clave {name} ya existe. ¿Sobrescribir?",
        "ssh_keys_dlg_del_title":    "Eliminar clave",
        "ssh_keys_dlg_del_msg":      "¿Eliminar el par {name}? Esta acción no se puede deshacer.",
        "ssh_keys_deploy_user_host": "usuario@host",
        "ssh_keys_deploy_port":      "Puerto",
        "ssh_keys_deploy_btn_run":   "Ejecutar",
        "ssh_keys_deploy_btn_close": "Cerrar",
        "ssh_keys_deploy_no_tool":   "ssh-copy-id no encontrado. Instale openssh-client.",
        "ssh_keys_generated":        "Clave {name} generada.",
        "ssh_keys_copied":           "Clave pública copiada al portapapeles.",
        "ssh_keys_deleted":          "Par {name} eliminado.",
        "ssh_keys_err_passphrase_mismatch": "Las frases de contraseña no coinciden.",
        "ssh_keys_err_keygen":       "Error: {msg}",
        "ssh_keys_no_keys":          "No se encontraron claves SSH en ~/.ssh/",
```

- [ ] **Step 4: Ajouter les clés allemandes (ligne ~2281, après `nav_hint_ssh` bloc `"de"`)**

```python
        "nav_ssh_keys":              "SSH-Schlüssel",
        "nav_hint_ssh_keys":         "Verwaltet lokale SSH-Schlüssel: auflisten, generieren,\nkopieren und bereitstellen via ssh-copy-id.",

        # ── SSH Keys page ────────────────────────────────────────────────
        "ssh_keys_btn_generate":     "Generieren",
        "ssh_keys_btn_copy_pub":     "Pub.-Schlüssel kopieren",
        "ssh_keys_btn_deploy":       "Bereitstellen",
        "ssh_keys_btn_delete":       "Löschen",
        "ssh_keys_btn_refresh":      "Aktualisieren",
        "ssh_keys_col_file":         "Datei",
        "ssh_keys_col_type":         "Typ",
        "ssh_keys_col_bits":         "Bits",
        "ssh_keys_col_comment":      "Kommentar",
        "ssh_keys_col_fingerprint":  "Fingerabdruck",
        "ssh_keys_dlg_gen_title":    "SSH-Schlüssel generieren",
        "ssh_keys_dlg_gen_type":     "Typ",
        "ssh_keys_dlg_gen_file":     "Dateiname",
        "ssh_keys_dlg_gen_comment":  "Kommentar",
        "ssh_keys_dlg_gen_passphrase": "Passphrase",
        "ssh_keys_dlg_gen_confirm":  "Bestätigen",
        "ssh_keys_dlg_overwrite_title": "Datei vorhanden",
        "ssh_keys_dlg_overwrite_msg": "Schlüssel {name} existiert bereits. Überschreiben?",
        "ssh_keys_dlg_del_title":    "Schlüssel löschen",
        "ssh_keys_dlg_del_msg":      "Schlüsselpaar {name} löschen? Dies kann nicht rückgängig gemacht werden.",
        "ssh_keys_deploy_user_host": "benutzer@host",
        "ssh_keys_deploy_port":      "Port",
        "ssh_keys_deploy_btn_run":   "Starten",
        "ssh_keys_deploy_btn_close": "Schließen",
        "ssh_keys_deploy_no_tool":   "ssh-copy-id nicht gefunden. Installieren Sie openssh-client.",
        "ssh_keys_generated":        "Schlüssel {name} generiert.",
        "ssh_keys_copied":           "Öffentlicher Schlüssel in die Zwischenablage kopiert.",
        "ssh_keys_deleted":          "Schlüsselpaar {name} gelöscht.",
        "ssh_keys_err_passphrase_mismatch": "Passphrasen stimmen nicht überein.",
        "ssh_keys_err_keygen":       "Fehler: {msg}",
        "ssh_keys_no_keys":          "Keine SSH-Schlüssel in ~/.ssh/ gefunden",
```

- [ ] **Step 5: Vérifier que `tr()` fonctionne**

```bash
cd /home/luust/claude-projects/nmlinux
python -c "
from nmlinux.core.settings import set as _set
_set('language', 'fr')
from nmlinux.core.i18n import tr
print(tr('nav_ssh_keys'))
print(tr('ssh_keys_btn_generate'))
print(tr('ssh_keys_dlg_overwrite_msg', name='id_ed25519'))
"
```

Expected:
```
Clés SSH
Générer
La clé id_ed25519 existe déjà. Écraser ?
```

- [ ] **Step 6: Commit**

```bash
cd /home/luust/claude-projects/nmlinux
git add nmlinux/core/i18n.py
git commit -m "feat(ssh-keys): add i18n keys — fr, en, es, de"
```

---

## Task 3 — `_KeyGenDialog` et `_KeyGenWorker`

**Files:**
- Modify: `nmlinux/pages/ssh_keys.py`

- [ ] **Step 1: Ajouter les imports UI en tête de fichier**

Remplacer le contenu actuel de `nmlinux/pages/ssh_keys.py` par :

```python
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
```

- [ ] **Step 2: Vérifier l'import**

```bash
cd /home/luust/claude-projects/nmlinux
python -c "from nmlinux.pages.ssh_keys import _KeyGenDialog, _KeyGenWorker; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Relancer les tests**

```bash
cd /home/luust/claude-projects/nmlinux
python -m pytest tests/test_ssh_keys.py -v
```

Expected: `9 passed`

- [ ] **Step 4: Commit**

```bash
cd /home/luust/claude-projects/nmlinux
git add nmlinux/pages/ssh_keys.py
git commit -m "feat(ssh-keys): add _KeyGenWorker and _KeyGenDialog"
```

---

## Task 4 — `_DeployBar`

**Files:**
- Modify: `nmlinux/pages/ssh_keys.py`

- [ ] **Step 1: Ajouter `_DeployBar` à la fin de `ssh_keys.py` (avant la classe principale)**

```python
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
```

- [ ] **Step 2: Vérifier l'import**

```bash
cd /home/luust/claude-projects/nmlinux
python -c "from nmlinux.pages.ssh_keys import _DeployBar; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
cd /home/luust/claude-projects/nmlinux
git add nmlinux/pages/ssh_keys.py
git commit -m "feat(ssh-keys): add _DeployBar with QProcess terminal"
```

---

## Task 5 — `SshKeysPage` (page principale)

**Files:**
- Modify: `nmlinux/pages/ssh_keys.py`

- [ ] **Step 1: Ajouter `SshKeysPage` à la fin de `ssh_keys.py`**

```python
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
```

- [ ] **Step 2: Vérifier l'import complet**

```bash
cd /home/luust/claude-projects/nmlinux
python -c "from nmlinux.pages.ssh_keys import SshKeysPage; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Relancer tous les tests**

```bash
cd /home/luust/claude-projects/nmlinux
python -m pytest tests/test_ssh_keys.py -v
```

Expected: `9 passed`

- [ ] **Step 4: Commit**

```bash
cd /home/luust/claude-projects/nmlinux
git add nmlinux/pages/ssh_keys.py
git commit -m "feat(ssh-keys): add SshKeysPage with table, toolbar, and deploy bar"
```

---

## Task 6 — Enregistrement dans `window.py`

**Files:**
- Modify: `nmlinux/window.py`

- [ ] **Step 1: Ajouter l'import (ligne ~28, après `from nmlinux.pages.ssh import SshPage`)**

```python
from nmlinux.pages.ssh_keys import SshKeysPage
```

- [ ] **Step 2: Ajouter l'entrée dans la liste des pages (après le bloc SSH, lignes ~125-129)**

Après le bloc :
```python
    (
        ("utilities-terminal", "terminal", "gnome-terminal"),
        "SSH", SshPage,
        tr("nav_hint_ssh"),
    ),
```

Ajouter :
```python
    (
        ("dialog-password", "security-high", "changes-prevent"),
        "SSH Keys", SshKeysPage,
        tr("nav_hint_ssh_keys"),
    ),
```

- [ ] **Step 3: Vérifier l'import de l'application**

```bash
cd /home/luust/claude-projects/nmlinux
python -c "from nmlinux.window import MainWindow; print('OK')"
```

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
cd /home/luust/claude-projects/nmlinux
git add nmlinux/window.py
git commit -m "feat(ssh-keys): register SshKeysPage in sidebar"
```

---

## Task 7 — Test manuel + release

**Files:** aucun

- [ ] **Step 1: Lancer l'application**

```bash
cd /home/luust/claude-projects/nmlinux
python -m nmlinux.main
```

Naviguer vers **SSH Keys** dans la sidebar et vérifier :
- La liste des clés `~/.ssh/` s'affiche (fichier, type, bits, commentaire, empreinte)
- Clic **Générer** → dialog avec type/fichier/commentaire/passphrase
- Champ passphrase vide = clé sans protection, OK activé
- Passphrase ≠ confirmation = message rouge, OK désactivé
- Après génération : nouvelle clé apparaît dans la table, status vert
- Sélectionner une clé → **Copier clé pub.** → coller quelque part pour vérifier
- Clic **Déployer** → `_DeployBar` apparaît en bas avec champ user@host
- Clic **Supprimer** → dialog de confirmation → clé disparaît de la table

- [ ] **Step 2: Bump version et release**

```bash
cd /home/luust/claude-projects/nmlinux
# Modifier nmlinux/__init__.py et pyproject.toml : 1.3.0 → 1.4.0
# Puis :
git add nmlinux/__init__.py pyproject.toml
git commit -m "chore: bump version to 1.4.0"
git tag v1.4.0
python -m build
gh release create v1.4.0 dist/nmlinux-1.4.0-py3-none-any.whl --title "NMLinux v1.4.0" --notes "- SSH Key Manager : liste, génération Ed25519/RSA, copie clé publique, déploiement ssh-copy-id, suppression"
```

- [ ] **Step 3: Mettre à jour l'AUR**

```bash
cd /home/luust/claude-projects/nmlinux/aur
# Mettre à jour pkgver=1.4.0 dans PKGBUILD
# Recalculer sha256 :
sha256sum ../dist/nmlinux-1.4.0-py3-none-any.whl
# Mettre à jour sha256sums dans PKGBUILD
makepkg --printsrcinfo > .SRCINFO
git add PKGBUILD .SRCINFO
git commit -m "upgpkg: nmlinux 1.4.0"
git push
```
