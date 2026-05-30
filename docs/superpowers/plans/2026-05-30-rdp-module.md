# RDP Module Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Remote Desktop Protocol module to NMLinux that manages Windows RDP connection profiles and launches `xfreerdp` as an external process.

**Architecture:** Mirror the SSH module exactly — `core/rdp.py` for pure logic (models, persistence, arg builder) and `pages/rdp.py` for the Qt UI (splitter with tree + stacked EMPTY/DETAIL/FORM panel). No window embedding; xfreerdp opens in its own OS window. Password is prompted at connect time via `QInputDialog` and never persisted.

**Tech Stack:** Python 3, PySide6 (Qt 6), `xfreerdp` CLI, `QProcess` (detached launch), `shutil.which` (binary detection)

---

## File Map

| Action | Path |
|--------|------|
| Create | `nmlinux/core/rdp.py` |
| Create | `nmlinux/pages/rdp.py` |
| Create | `tests/test_rdp_core.py` |
| Modify | `nmlinux/core/i18n.py` — add `nav_rdp` + `rdp_*` keys in fr/en/es/de |
| Modify | `nmlinux/window.py` — import RdpPage, add sidebar entry |

---

## Task 1: `core/rdp.py` — data model, persistence, arg builder

**Files:**
- Create: `nmlinux/core/rdp.py`
- Create: `tests/__init__.py`
- Create: `tests/test_rdp_core.py`

- [ ] **Step 1: Create `tests/__init__.py`**

```python
```
(empty file)

- [ ] **Step 2: Write failing tests**

Create `tests/test_rdp_core.py`:

```python
from __future__ import annotations
import json
from pathlib import Path
import pytest
from nmlinux.core.rdp import (
    RdpGroup, RdpConnection, RdpStore, build_rdp_args
)


# ── build_rdp_args ─────────────────────────────────────────────────────────

def test_args_basic():
    conn = RdpConnection(host="192.168.1.10", username="admin", port=3389)
    args = build_rdp_args(conn, "secret")
    assert "/v:192.168.1.10:3389" in args
    assert "/u:admin" in args
    assert "/p:secret" in args
    assert "/cert:ignore" in args
    assert "/dynamic-resolution" in args

def test_args_no_domain():
    conn = RdpConnection(host="srv", username="user", domain="")
    args = build_rdp_args(conn, "pw")
    assert not any(a.startswith("/d:") for a in args)

def test_args_with_domain():
    conn = RdpConnection(host="srv", username="user", domain="CORP")
    args = build_rdp_args(conn, "pw")
    assert "/d:CORP" in args

def test_args_resolution():
    conn = RdpConnection(host="srv", resolution="1920x1080", fullscreen=False)
    args = build_rdp_args(conn, "pw")
    assert "/size:1920x1080" in args
    assert "/f" not in args

def test_args_fullscreen():
    conn = RdpConnection(host="srv", fullscreen=True)
    args = build_rdp_args(conn, "pw")
    assert "/f" in args
    assert not any(a.startswith("/size:") for a in args)

def test_args_first_element_is_xfreerdp():
    conn = RdpConnection(host="srv")
    args = build_rdp_args(conn, "pw")
    assert args[0] == "xfreerdp"


# ── RdpConnection defaults ─────────────────────────────────────────────────

def test_connection_defaults():
    conn = RdpConnection()
    assert conn.port == 3389
    assert conn.resolution == "1920x1080"
    assert conn.fullscreen is False
    assert conn.domain == ""
    assert conn.group_id == ""

def test_display_name_uses_name():
    conn = RdpConnection(name="Mon PC", host="192.168.1.5")
    assert conn.display_name == "Mon PC"

def test_display_name_falls_back_to_host():
    conn = RdpConnection(name="", host="192.168.1.5")
    assert conn.display_name == "192.168.1.5"

def test_subtitle_includes_user_and_host():
    conn = RdpConnection(host="srv", username="admin", port=3389)
    assert "admin" in conn.subtitle
    assert "srv" in conn.subtitle


# ── RdpStore ───────────────────────────────────────────────────────────────

def test_store_roundtrip(tmp_path):
    path = tmp_path / "rdp.json"
    store = RdpStore(path)
    groups = [RdpGroup(name="Boulot"), RdpGroup(name="Perso")]
    conns  = [
        RdpConnection(name="AD", host="10.0.0.1", username="admin", domain="CORP"),
        RdpConnection(name="NAS", host="10.0.0.2"),
    ]
    store.save(groups, conns)
    loaded_groups, loaded_conns = store.load()
    assert len(loaded_groups) == 2
    assert len(loaded_conns) == 2
    assert loaded_conns[0].host == "10.0.0.1"
    assert loaded_conns[0].domain == "CORP"

def test_store_load_missing_file(tmp_path):
    store = RdpStore(tmp_path / "missing.json")
    groups, conns = store.load()
    assert groups == []
    assert conns == []

def test_store_load_corrupt_file(tmp_path):
    path = tmp_path / "rdp.json"
    path.write_text("not json")
    store = RdpStore(path)
    groups, conns = store.load()
    assert groups == []
    assert conns == []

def test_store_json_format(tmp_path):
    path = tmp_path / "rdp.json"
    store = RdpStore(path)
    store.save([RdpGroup(name="G")], [RdpConnection(name="C", host="h")])
    raw = json.loads(path.read_text())
    assert raw["version"] == 2
    assert "groups" in raw
    assert "connections" in raw
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
cd /home/luust/claude-projects/nmlinux && python -m pytest tests/test_rdp_core.py -v 2>&1 | head -30
```
Expected: `ModuleNotFoundError: No module named 'nmlinux.core.rdp'`

- [ ] **Step 4: Create `nmlinux/core/rdp.py`**

```python
"""RDP connection profiles — pure logic, no Qt dependency."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path


# ── Model ──────────────────────────────────────────────────────────────────


@dataclass
class RdpGroup:
    id:        str = field(default_factory=lambda: str(uuid.uuid4()))
    name:      str = ""
    parent_id: str = ""


@dataclass
class RdpConnection:
    id:         str  = field(default_factory=lambda: str(uuid.uuid4()))
    name:       str  = ""
    host:       str  = ""
    port:       int  = 3389
    username:   str  = ""
    domain:     str  = ""
    resolution: str  = "1920x1080"
    fullscreen: bool = False
    notes:      str  = ""
    group_id:   str  = ""

    @property
    def display_name(self) -> str:
        return self.name if self.name else self.host

    @property
    def subtitle(self) -> str:
        target = f"{self.username}@{self.host}" if self.username else self.host
        return f"{target}:{self.port}" if self.port != 3389 else target


# ── Persistence ────────────────────────────────────────────────────────────


class RdpStore:
    def __init__(self, path: Path | None = None) -> None:
        if path is None:
            data_dir = Path.home() / ".local" / "share" / "nmlinux"
            data_dir.mkdir(parents=True, exist_ok=True)
            path = data_dir / "rdp_connections.json"
        self._path = path

    def load(self) -> tuple[list[RdpGroup], list[RdpConnection]]:
        if not self._path.exists():
            return [], []
        try:
            raw = json.loads(self._path.read_text())
            conn_fields  = RdpConnection.__dataclass_fields__
            group_fields = RdpGroup.__dataclass_fields__
            groups = [
                RdpGroup(**{k: v for k, v in g.items() if k in group_fields})
                for g in raw.get("groups", [])
            ]
            conns = [
                RdpConnection(**{k: v for k, v in c.items() if k in conn_fields})
                for c in raw.get("connections", [])
            ]
            return groups, conns
        except Exception:
            return [], []

    def save(self, groups: list[RdpGroup], connections: list[RdpConnection]) -> None:
        data = {
            "version": 2,
            "groups": [asdict(g) for g in groups],
            "connections": [asdict(c) for c in connections],
        }
        self._path.write_text(json.dumps(data, indent=2, ensure_ascii=False))


# ── Args builder ───────────────────────────────────────────────────────────


def build_rdp_args(conn: RdpConnection, password: str) -> list[str]:
    args = [
        "xfreerdp",
        f"/v:{conn.host}:{conn.port}",
    ]
    if conn.username:
        args.append(f"/u:{conn.username}")
    args.append(f"/p:{password}")
    if conn.domain:
        args.append(f"/d:{conn.domain}")
    if conn.fullscreen:
        args.append("/f")
    else:
        args.append(f"/size:{conn.resolution}")
    args += ["/dynamic-resolution", "/cert:ignore"]
    return args
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd /home/luust/claude-projects/nmlinux && python -m pytest tests/test_rdp_core.py -v
```
Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
cd /home/luust/claude-projects/nmlinux
git add nmlinux/core/rdp.py tests/__init__.py tests/test_rdp_core.py
git commit -m "feat(rdp): add core/rdp.py — models, store, build_rdp_args"
```

---

## Task 2: i18n — add RDP keys in fr / en / es / de

**Files:**
- Modify: `nmlinux/core/i18n.py`

- [ ] **Step 1: Add `nav_rdp` in all 4 language blocks**

In `i18n.py`, find the 4 occurrences of `"nav_ssh":` (lines 21, 559, 1080, 1603) and add `nav_rdp` immediately after each one:

French (after line 21):
```python
        "nav_ssh":          "SSH",
        "nav_rdp":          "Remote Desktop",
```

English (after line 559):
```python
        "nav_ssh":          "SSH",
        "nav_rdp":          "Remote Desktop",
```

Spanish (after line 1080):
```python
        "nav_ssh":          "SSH",
        "nav_rdp":          "Remote Desktop",
```

German (after line 1603):
```python
        "nav_ssh":          "SSH",
        "nav_rdp":          "Remote Desktop",
```

- [ ] **Step 2: Add `rdp_*` keys in French block** (after `ssh_session_ended` at line 345)

```python
        "ssh_session_ended":      "\n\n── Session terminée (code {code}) ──\n",

        # ── Remote Desktop ───────────────────────────────────────────────────
        "rdp_new_conn_btn":        "Nouvelle connexion",
        "rdp_new_grp_btn":         "Nouveau groupe",
        "rdp_empty_state":         "Sélectionnez une connexion\nou créez-en une nouvelle.",
        "rdp_det_lbl_host":        "Hôte",
        "rdp_det_lbl_port":        "Port",
        "rdp_det_lbl_user":        "Utilisateur",
        "rdp_det_lbl_domain":      "Domaine",
        "rdp_det_lbl_resolution":  "Résolution",
        "rdp_det_lbl_fullscreen":  "Plein écran",
        "rdp_det_lbl_notes":       "Notes",
        "rdp_connect_btn":         "Se connecter",
        "rdp_edit_btn":            "Modifier",
        "rdp_delete_btn":          "Supprimer",
        "rdp_form_lbl_name":       "Nom :",
        "rdp_form_lbl_group":      "Groupe :",
        "rdp_form_lbl_host":       "Hôte * :",
        "rdp_form_lbl_port":       "Port :",
        "rdp_form_lbl_user":       "Utilisateur :",
        "rdp_form_lbl_domain":     "Domaine :",
        "rdp_form_lbl_resolution": "Résolution :",
        "rdp_form_lbl_fullscreen": "Plein écran :",
        "rdp_form_lbl_notes":      "Notes :",
        "rdp_form_name_ph":        "Mon PC Windows",
        "rdp_form_user_ph":        "Administrateur",
        "rdp_form_domain_ph":      "CORP  (laisser vide si absent)",
        "rdp_save_btn":            "Enregistrer",
        "rdp_cancel_btn":          "Annuler",
        "rdp_form_title_new":      "Nouvelle connexion RDP",
        "rdp_form_title_edit":     "Modifier la connexion RDP",
        "rdp_ctx_connect":         "Se connecter",
        "rdp_ctx_edit":            "Modifier",
        "rdp_ctx_delete":          "Supprimer",
        "rdp_ctx_rename_grp":      "Renommer",
        "rdp_ctx_add_sub":         "Ajouter un sous-groupe",
        "rdp_ctx_delete_grp":      "Supprimer le groupe",
        "rdp_no_group":            "— Aucun groupe —",
        "rdp_root_level":          "— Niveau racine —",
        "rdp_dlg_new_grp_title":   "Nouveau groupe",
        "rdp_dlg_new_grp_prompt":  "Nom du groupe :",
        "rdp_dlg_parent_title":    "Groupe parent",
        "rdp_dlg_parent_prompt":   "Placer dans :",
        "rdp_dlg_new_sub_title":   "Nouveau sous-groupe",
        "rdp_dlg_new_sub_prompt":  "Sous-groupe de «{parent}» :",
        "rdp_dlg_rename_title":    "Renommer",
        "rdp_dlg_rename_prompt":   "Nouveau nom :",
        "rdp_dlg_req_title":       "Champ requis",
        "rdp_dlg_req_msg":         "L'hôte est requis.",
        "rdp_dlg_del_title":       "Supprimer",
        "rdp_dlg_del_msg":         "Supprimer «{name}» ?",
        "rdp_dlg_del_grp_title":   "Supprimer le groupe",
        "rdp_dlg_del_grp_msg":     "Supprimer «{name}» ?\nLes connexions seront déplacées à la racine.",
        "rdp_password_prompt":     "Mot de passe Windows :",
        "rdp_missing_title":       "xfreerdp introuvable",
        "rdp_missing_msg":         "xfreerdp n'est pas installé.\n\nArch : sudo pacman -S freerdp\nDebian/Ubuntu : sudo apt install freerdp2-x11\nFedora : sudo dnf install freerdp",
```

- [ ] **Step 3: Add `rdp_*` keys in English block** (after `ssh_session_ended` at line 868 — offset +1 due to nav_rdp insertion)

```python
        "ssh_session_ended":      "\n\n── Session ended (code {code}) ──\n",

        # ── Remote Desktop ───────────────────────────────────────────────────
        "rdp_new_conn_btn":        "New connection",
        "rdp_new_grp_btn":         "New group",
        "rdp_empty_state":         "Select a connection\nor create a new one.",
        "rdp_det_lbl_host":        "Host",
        "rdp_det_lbl_port":        "Port",
        "rdp_det_lbl_user":        "Username",
        "rdp_det_lbl_domain":      "Domain",
        "rdp_det_lbl_resolution":  "Resolution",
        "rdp_det_lbl_fullscreen":  "Fullscreen",
        "rdp_det_lbl_notes":       "Notes",
        "rdp_connect_btn":         "Connect",
        "rdp_edit_btn":            "Edit",
        "rdp_delete_btn":          "Delete",
        "rdp_form_lbl_name":       "Name:",
        "rdp_form_lbl_group":      "Group:",
        "rdp_form_lbl_host":       "Host *:",
        "rdp_form_lbl_port":       "Port:",
        "rdp_form_lbl_user":       "Username:",
        "rdp_form_lbl_domain":     "Domain:",
        "rdp_form_lbl_resolution": "Resolution:",
        "rdp_form_lbl_fullscreen": "Fullscreen:",
        "rdp_form_lbl_notes":      "Notes:",
        "rdp_form_name_ph":        "My Windows PC",
        "rdp_form_user_ph":        "Administrator",
        "rdp_form_domain_ph":      "CORP  (leave empty if none)",
        "rdp_save_btn":            "Save",
        "rdp_cancel_btn":          "Cancel",
        "rdp_form_title_new":      "New RDP connection",
        "rdp_form_title_edit":     "Edit RDP connection",
        "rdp_ctx_connect":         "Connect",
        "rdp_ctx_edit":            "Edit",
        "rdp_ctx_delete":          "Delete",
        "rdp_ctx_rename_grp":      "Rename",
        "rdp_ctx_add_sub":         "Add subgroup",
        "rdp_ctx_delete_grp":      "Delete group",
        "rdp_no_group":            "— No group —",
        "rdp_root_level":          "— Root level —",
        "rdp_dlg_new_grp_title":   "New group",
        "rdp_dlg_new_grp_prompt":  "Group name:",
        "rdp_dlg_parent_title":    "Parent group",
        "rdp_dlg_parent_prompt":   "Place in:",
        "rdp_dlg_new_sub_title":   "New subgroup",
        "rdp_dlg_new_sub_prompt":  "Subgroup of «{parent}»:",
        "rdp_dlg_rename_title":    "Rename",
        "rdp_dlg_rename_prompt":   "New name:",
        "rdp_dlg_req_title":       "Required field",
        "rdp_dlg_req_msg":         "Host is required.",
        "rdp_dlg_del_title":       "Delete",
        "rdp_dlg_del_msg":         "Delete «{name}»?",
        "rdp_dlg_del_grp_title":   "Delete group",
        "rdp_dlg_del_grp_msg":     "Delete «{name}»?\nConnections will be moved to root.",
        "rdp_password_prompt":     "Windows password:",
        "rdp_missing_title":       "xfreerdp not found",
        "rdp_missing_msg":         "xfreerdp is not installed.\n\nArch: sudo pacman -S freerdp\nDebian/Ubuntu: sudo apt install freerdp2-x11\nFedora: sudo dnf install freerdp",
```

- [ ] **Step 4: Add `rdp_*` keys in Spanish block** (after `ssh_session_ended` at line 1372)

```python
        "ssh_session_ended":      "\n\n── Sesión terminada (código {code}) ──\n",

        # ── Remote Desktop ───────────────────────────────────────────────────
        "rdp_new_conn_btn":        "Nueva conexión",
        "rdp_new_grp_btn":         "Nuevo grupo",
        "rdp_empty_state":         "Seleccione una conexión\no cree una nueva.",
        "rdp_det_lbl_host":        "Host",
        "rdp_det_lbl_port":        "Puerto",
        "rdp_det_lbl_user":        "Usuario",
        "rdp_det_lbl_domain":      "Dominio",
        "rdp_det_lbl_resolution":  "Resolución",
        "rdp_det_lbl_fullscreen":  "Pantalla completa",
        "rdp_det_lbl_notes":       "Notas",
        "rdp_connect_btn":         "Conectar",
        "rdp_edit_btn":            "Editar",
        "rdp_delete_btn":          "Eliminar",
        "rdp_form_lbl_name":       "Nombre:",
        "rdp_form_lbl_group":      "Grupo:",
        "rdp_form_lbl_host":       "Host *:",
        "rdp_form_lbl_port":       "Puerto:",
        "rdp_form_lbl_user":       "Usuario:",
        "rdp_form_lbl_domain":     "Dominio:",
        "rdp_form_lbl_resolution": "Resolución:",
        "rdp_form_lbl_fullscreen": "Pantalla completa:",
        "rdp_form_lbl_notes":      "Notas:",
        "rdp_form_name_ph":        "Mi PC Windows",
        "rdp_form_user_ph":        "Administrador",
        "rdp_form_domain_ph":      "CORP  (dejar vacío si no aplica)",
        "rdp_save_btn":            "Guardar",
        "rdp_cancel_btn":          "Cancelar",
        "rdp_form_title_new":      "Nueva conexión RDP",
        "rdp_form_title_edit":     "Editar conexión RDP",
        "rdp_ctx_connect":         "Conectar",
        "rdp_ctx_edit":            "Editar",
        "rdp_ctx_delete":          "Eliminar",
        "rdp_ctx_rename_grp":      "Renombrar",
        "rdp_ctx_add_sub":         "Agregar subgrupo",
        "rdp_ctx_delete_grp":      "Eliminar grupo",
        "rdp_no_group":            "— Sin grupo —",
        "rdp_root_level":          "— Nivel raíz —",
        "rdp_dlg_new_grp_title":   "Nuevo grupo",
        "rdp_dlg_new_grp_prompt":  "Nombre del grupo:",
        "rdp_dlg_parent_title":    "Grupo padre",
        "rdp_dlg_parent_prompt":   "Colocar en:",
        "rdp_dlg_new_sub_title":   "Nuevo subgrupo",
        "rdp_dlg_new_sub_prompt":  "Subgrupo de «{parent}»:",
        "rdp_dlg_rename_title":    "Renombrar",
        "rdp_dlg_rename_prompt":   "Nuevo nombre:",
        "rdp_dlg_req_title":       "Campo requerido",
        "rdp_dlg_req_msg":         "El host es obligatorio.",
        "rdp_dlg_del_title":       "Eliminar",
        "rdp_dlg_del_msg":         "¿Eliminar «{name}»?",
        "rdp_dlg_del_grp_title":   "Eliminar grupo",
        "rdp_dlg_del_grp_msg":     "¿Eliminar «{name}»?\nLas conexiones se moverán a la raíz.",
        "rdp_password_prompt":     "Contraseña de Windows:",
        "rdp_missing_title":       "xfreerdp no encontrado",
        "rdp_missing_msg":         "xfreerdp no está instalado.\n\nArch: sudo pacman -S freerdp\nDebian/Ubuntu: sudo apt install freerdp2-x11\nFedora: sudo dnf install freerdp",
```

- [ ] **Step 5: Add `rdp_*` keys in German block** (after `ssh_session_ended` at line 1895)

```python
        "ssh_session_ended":      "\n\n── Sitzung beendet (Code {code}) ──\n",

        # ── Remote Desktop ───────────────────────────────────────────────────
        "rdp_new_conn_btn":        "Neue Verbindung",
        "rdp_new_grp_btn":         "Neue Gruppe",
        "rdp_empty_state":         "Verbindung auswählen\noder neue erstellen.",
        "rdp_det_lbl_host":        "Host",
        "rdp_det_lbl_port":        "Port",
        "rdp_det_lbl_user":        "Benutzer",
        "rdp_det_lbl_domain":      "Domäne",
        "rdp_det_lbl_resolution":  "Auflösung",
        "rdp_det_lbl_fullscreen":  "Vollbild",
        "rdp_det_lbl_notes":       "Notizen",
        "rdp_connect_btn":         "Verbinden",
        "rdp_edit_btn":            "Bearbeiten",
        "rdp_delete_btn":          "Löschen",
        "rdp_form_lbl_name":       "Name:",
        "rdp_form_lbl_group":      "Gruppe:",
        "rdp_form_lbl_host":       "Host *:",
        "rdp_form_lbl_port":       "Port:",
        "rdp_form_lbl_user":       "Benutzer:",
        "rdp_form_lbl_domain":     "Domäne:",
        "rdp_form_lbl_resolution": "Auflösung:",
        "rdp_form_lbl_fullscreen": "Vollbild:",
        "rdp_form_lbl_notes":      "Notizen:",
        "rdp_form_name_ph":        "Mein Windows-PC",
        "rdp_form_user_ph":        "Administrator",
        "rdp_form_domain_ph":      "CORP  (leer lassen wenn nicht vorhanden)",
        "rdp_save_btn":            "Speichern",
        "rdp_cancel_btn":          "Abbrechen",
        "rdp_form_title_new":      "Neue RDP-Verbindung",
        "rdp_form_title_edit":     "RDP-Verbindung bearbeiten",
        "rdp_ctx_connect":         "Verbinden",
        "rdp_ctx_edit":            "Bearbeiten",
        "rdp_ctx_delete":          "Löschen",
        "rdp_ctx_rename_grp":      "Umbenennen",
        "rdp_ctx_add_sub":         "Untergruppe hinzufügen",
        "rdp_ctx_delete_grp":      "Gruppe löschen",
        "rdp_no_group":            "— Keine Gruppe —",
        "rdp_root_level":          "— Stammebene —",
        "rdp_dlg_new_grp_title":   "Neue Gruppe",
        "rdp_dlg_new_grp_prompt":  "Gruppenname:",
        "rdp_dlg_parent_title":    "Übergeordnete Gruppe",
        "rdp_dlg_parent_prompt":   "Platzieren in:",
        "rdp_dlg_new_sub_title":   "Neue Untergruppe",
        "rdp_dlg_new_sub_prompt":  "Untergruppe von «{parent}»:",
        "rdp_dlg_rename_title":    "Umbenennen",
        "rdp_dlg_rename_prompt":   "Neuer Name:",
        "rdp_dlg_req_title":       "Pflichtfeld",
        "rdp_dlg_req_msg":         "Host ist erforderlich.",
        "rdp_dlg_del_title":       "Löschen",
        "rdp_dlg_del_msg":         "«{name}» löschen?",
        "rdp_dlg_del_grp_title":   "Gruppe löschen",
        "rdp_dlg_del_grp_msg":     "«{name}» löschen?\nVerbindungen werden in die Stammebene verschoben.",
        "rdp_password_prompt":     "Windows-Passwort:",
        "rdp_missing_title":       "xfreerdp nicht gefunden",
        "rdp_missing_msg":         "xfreerdp ist nicht installiert.\n\nArch: sudo pacman -S freerdp\nDebian/Ubuntu: sudo apt install freerdp2-x11\nFedora: sudo dnf install freerdp",
```

- [ ] **Step 6: Verify i18n loads without error**

```bash
cd /home/luust/claude-projects/nmlinux && python -c "from nmlinux.core.i18n import tr; print(tr('nav_rdp')); print(tr('rdp_connect_btn'))"
```
Expected output:
```
Remote Desktop
Se connecter
```

- [ ] **Step 7: Commit**

```bash
cd /home/luust/claude-projects/nmlinux
git add nmlinux/core/i18n.py
git commit -m "feat(rdp): add i18n keys for RDP module (fr/en/es/de)"
```

---

## Task 3: `pages/rdp.py` — Qt UI page

**Files:**
- Create: `nmlinux/pages/rdp.py`

- [ ] **Step 1: Create `nmlinux/pages/rdp.py`**

```python
from __future__ import annotations

import shutil
import uuid

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QFormLayout,
    QTreeWidget, QTreeWidgetItem,
    QStackedWidget,
    QLabel, QLineEdit, QSpinBox, QPushButton, QTextEdit,
    QFrame, QGroupBox, QSplitter, QCheckBox,
    QMessageBox, QApplication, QComboBox, QInputDialog, QMenu,
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QProcess

from nmlinux.core.rdp import RdpConnection, RdpGroup, RdpStore, build_rdp_args
from nmlinux.core.i18n import tr

_EMPTY  = 0
_DETAIL = 1
_FORM   = 2


# ── RDP page ───────────────────────────────────────────────────────────────

class RdpPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._store = RdpStore()
        self._groups, self._connections = self._store.load()
        self._editing_id: str | None = None

        self._build_ui()
        self._refresh_list()

    # ── Build ──────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self._build_left())
        splitter.addWidget(self._build_right())
        splitter.setSizes([220, 700])
        root.addWidget(splitter)

    # ── Left panel ─────────────────────────────────────────────────────────

    def _build_left(self) -> QWidget:
        panel = QFrame()
        panel.setFrameShape(QFrame.Shape.NoFrame)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 4, 8)
        layout.setSpacing(4)

        btn_new_conn = QPushButton(QIcon.fromTheme("list-add"), " " + tr("rdp_new_conn_btn"))
        btn_new_conn.clicked.connect(self._on_new)
        btn_new_grp  = QPushButton(QIcon.fromTheme("folder-new"), " " + tr("rdp_new_grp_btn"))
        btn_new_grp.clicked.connect(self._on_new_group)
        layout.addWidget(btn_new_conn)
        layout.addWidget(btn_new_grp)

        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setFrameShape(QFrame.Shape.NoFrame)
        self._tree.setIndentation(16)
        self._tree.setAnimated(True)
        self._tree.currentItemChanged.connect(self._on_selection_changed)
        self._tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        self._tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._on_context_menu)
        layout.addWidget(self._tree, 1)
        return panel

    # ── Right panel ────────────────────────────────────────────────────────

    def _build_right(self) -> QStackedWidget:
        self._right = QStackedWidget()
        self._right.addWidget(self._build_empty())
        self._right.addWidget(self._build_detail())
        self._right.addWidget(self._build_form())
        return self._right

    def _build_empty(self) -> QWidget:
        w = QWidget()
        lbl = QLabel(tr("rdp_empty_state"))
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("color: palette(mid); font-size: 14px;")
        QVBoxLayout(w).addWidget(lbl)
        return w

    def _build_detail(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        self._det_name     = QLabel()
        self._det_name.setStyleSheet("font-size: 18px; font-weight: bold;")
        self._det_subtitle = QLabel()
        self._det_subtitle.setStyleSheet("color: palette(mid);")
        self._det_group_path = QLabel()
        self._det_group_path.setStyleSheet("color: palette(mid); font-style: italic;")
        layout.addWidget(self._det_name)
        layout.addWidget(self._det_subtitle)
        layout.addWidget(self._det_group_path)

        card = QGroupBox()
        form = QFormLayout(card)
        form.setHorizontalSpacing(20)
        self._det: dict[str, QLabel] = {}
        for key, lbl_key in [
            ("host",       "rdp_det_lbl_host"),
            ("port",       "rdp_det_lbl_port"),
            ("username",   "rdp_det_lbl_user"),
            ("domain",     "rdp_det_lbl_domain"),
            ("resolution", "rdp_det_lbl_resolution"),
            ("fullscreen", "rdp_det_lbl_fullscreen"),
            ("notes",      "rdp_det_lbl_notes"),
        ]:
            val = QLabel()
            val.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            val.setWordWrap(True)
            self._det[key] = val
            form.addRow(tr(lbl_key) + " :", val)
        layout.addWidget(card)
        layout.addStretch(1)

        row = QHBoxLayout()
        self._btn_connect = QPushButton(QIcon.fromTheme("network-connect"), " " + tr("rdp_connect_btn"))
        self._btn_connect.setDefault(True)
        self._btn_connect.clicked.connect(self._on_connect)
        btn_edit = QPushButton(QIcon.fromTheme("document-edit"), " " + tr("rdp_edit_btn"))
        btn_edit.clicked.connect(self._on_edit)
        btn_del  = QPushButton(QIcon.fromTheme("edit-delete"), " " + tr("rdp_delete_btn"))
        btn_del.clicked.connect(self._on_delete)
        row.addWidget(self._btn_connect)
        row.addWidget(btn_edit)
        row.addStretch(1)
        row.addWidget(btn_del)
        layout.addLayout(row)
        return w

    def _build_form(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        self._form_title = QLabel()
        self._form_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self._form_title)

        card = QGroupBox()
        form = QFormLayout(card)
        form.setHorizontalSpacing(20)

        self._f_name       = QLineEdit(); self._f_name.setPlaceholderText(tr("rdp_form_name_ph"))
        self._f_group      = QComboBox()
        self._f_host       = QLineEdit(); self._f_host.setPlaceholderText("192.168.1.100")
        self._f_port       = QSpinBox();  self._f_port.setRange(1, 65535); self._f_port.setValue(3389)
        self._f_user       = QLineEdit(); self._f_user.setPlaceholderText(tr("rdp_form_user_ph"))
        self._f_domain     = QLineEdit(); self._f_domain.setPlaceholderText(tr("rdp_form_domain_ph"))
        self._f_resolution = QComboBox()
        for res in ["1920x1080", "1280x720", "1600x900", "2560x1440", "3840x2160"]:
            self._f_resolution.addItem(res)
        self._f_resolution.setEditable(True)
        self._f_fullscreen = QCheckBox()
        self._f_notes      = QTextEdit(); self._f_notes.setMaximumHeight(80)

        form.addRow(tr("rdp_form_lbl_name"),       self._f_name)
        form.addRow(tr("rdp_form_lbl_group"),       self._f_group)
        form.addRow(tr("rdp_form_lbl_host"),        self._f_host)
        form.addRow(tr("rdp_form_lbl_port"),        self._f_port)
        form.addRow(tr("rdp_form_lbl_user"),        self._f_user)
        form.addRow(tr("rdp_form_lbl_domain"),      self._f_domain)
        form.addRow(tr("rdp_form_lbl_resolution"),  self._f_resolution)
        form.addRow(tr("rdp_form_lbl_fullscreen"),  self._f_fullscreen)
        form.addRow(tr("rdp_form_lbl_notes"),       self._f_notes)
        layout.addWidget(card)
        layout.addStretch(1)

        row = QHBoxLayout()
        btn_save   = QPushButton(QIcon.fromTheme("document-save"), " " + tr("rdp_save_btn"))
        btn_save.setDefault(True); btn_save.clicked.connect(self._on_save)
        btn_cancel = QPushButton(QIcon.fromTheme("dialog-cancel"), " " + tr("rdp_cancel_btn"))
        btn_cancel.clicked.connect(self._on_cancel)
        row.addWidget(btn_save); row.addWidget(btn_cancel); row.addStretch(1)
        layout.addLayout(row)
        return w

    # ── Tree helpers ───────────────────────────────────────────────────────

    def _group_path(self, group_id: str) -> str:
        parts: list[str] = []
        gid = group_id
        while gid:
            grp = next((g for g in self._groups if g.id == gid), None)
            if grp is None:
                break
            parts.insert(0, grp.name)
            gid = grp.parent_id
        return " > ".join(parts)

    def _build_tree_children(
        self,
        parent_item: QTreeWidgetItem,
        parent_group_id: str,
        icon_conn: QIcon,
        icon_grp: QIcon,
    ) -> None:
        for group in self._groups:
            if group.parent_id == parent_group_id:
                g_item = QTreeWidgetItem(parent_item, [group.name])
                g_item.setIcon(0, icon_grp)
                g_item.setData(0, Qt.ItemDataRole.UserRole, ('group', group.id))
                g_item.setExpanded(True)
                f = g_item.font(0); f.setBold(True); g_item.setFont(0, f)
                self._build_tree_children(g_item, group.id, icon_conn, icon_grp)
        for conn in self._connections:
            if conn.group_id == parent_group_id:
                c_item = QTreeWidgetItem(parent_item, [conn.display_name])
                c_item.setIcon(0, icon_conn)
                c_item.setToolTip(0, conn.subtitle)
                c_item.setData(0, Qt.ItemDataRole.UserRole, ('conn', conn.id))

    def _refresh_list(self, select_conn_id: str | None = None) -> None:
        self._tree.blockSignals(True)
        self._tree.clear()
        icon_conn = QIcon.fromTheme("computer")
        icon_grp  = QIcon.fromTheme("folder")
        self._build_tree_children(self._tree.invisibleRootItem(), "", icon_conn, icon_grp)
        self._tree.blockSignals(False)
        if select_conn_id:
            self._select_conn(select_conn_id)
        else:
            self._select_first_conn()

    def _select_conn(self, conn_id: str) -> bool:
        def walk(parent: QTreeWidgetItem) -> bool:
            for i in range(parent.childCount()):
                child = parent.child(i)
                data = child.data(0, Qt.ItemDataRole.UserRole)
                if data and data[0] == 'conn' and data[1] == conn_id:
                    self._tree.setCurrentItem(child)
                    return True
                if walk(child):
                    return True
            return False
        return walk(self._tree.invisibleRootItem())

    def _select_first_conn(self) -> None:
        def walk(parent: QTreeWidgetItem) -> bool:
            for i in range(parent.childCount()):
                child = parent.child(i)
                data = child.data(0, Qt.ItemDataRole.UserRole)
                if data and data[0] == 'conn':
                    self._tree.setCurrentItem(child)
                    return True
                if walk(child):
                    return True
            return False
        if not walk(self._tree.invisibleRootItem()):
            self._right.setCurrentIndex(_EMPTY)

    def _current_conn(self) -> RdpConnection | None:
        item = self._tree.currentItem()
        if item is None:
            return None
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data is None or data[0] != 'conn':
            return None
        return next((c for c in self._connections if c.id == data[1]), None)

    def _populate_group_combo(self, current_group_id: str = "") -> None:
        self._f_group.blockSignals(True)
        self._f_group.clear()
        self._f_group.addItem(tr("rdp_no_group"), "")

        def add_group(grp: RdpGroup, indent: int) -> None:
            prefix = "    " * indent
            self._f_group.addItem(f"{prefix}{grp.name}", grp.id)
            for sub in self._groups:
                if sub.parent_id == grp.id:
                    add_group(sub, indent + 1)

        for grp in self._groups:
            if not grp.parent_id:
                add_group(grp, 0)

        idx = self._f_group.findData(current_group_id)
        self._f_group.setCurrentIndex(idx if idx >= 0 else 0)
        self._f_group.blockSignals(False)

    # ── Slots — selection ──────────────────────────────────────────────────

    def _on_selection_changed(self, current: QTreeWidgetItem | None, _prev) -> None:
        if current is None:
            self._right.setCurrentIndex(_EMPTY)
            return
        data = current.data(0, Qt.ItemDataRole.UserRole)
        if data is None or data[0] != 'conn':
            self._right.setCurrentIndex(_EMPTY)
            return
        conn = next((c for c in self._connections if c.id == data[1]), None)
        if conn:
            self._show_detail(conn)

    def _on_item_double_clicked(self, item: QTreeWidgetItem, _col: int) -> None:
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data and data[0] == 'conn':
            conn = next((c for c in self._connections if c.id == data[1]), None)
            if conn:
                self._launch_rdp(conn)

    def _on_context_menu(self, pos) -> None:
        item = self._tree.itemAt(pos)
        if item is None:
            return
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data is None:
            return
        kind, item_id = data
        menu = QMenu(self)

        if kind == 'conn':
            conn = next((c for c in self._connections if c.id == item_id), None)
            if conn is None:
                return
            act_connect = menu.addAction(QIcon.fromTheme("network-connect"), tr("rdp_ctx_connect"))
            menu.addSeparator()
            act_edit = menu.addAction(QIcon.fromTheme("document-edit"), tr("rdp_ctx_edit"))
            act_del  = menu.addAction(QIcon.fromTheme("edit-delete"),   tr("rdp_ctx_delete"))
            act = menu.exec(self._tree.viewport().mapToGlobal(pos))
            if act == act_connect:
                self._launch_rdp(conn)
            elif act == act_edit:
                self._tree.setCurrentItem(item); self._on_edit()
            elif act == act_del:
                self._tree.setCurrentItem(item); self._on_delete()

        elif kind == 'group':
            grp = next((g for g in self._groups if g.id == item_id), None)
            if grp is None:
                return
            act_rename  = menu.addAction(QIcon.fromTheme("document-edit"), tr("rdp_ctx_rename_grp"))
            act_add_sub = menu.addAction(QIcon.fromTheme("folder-new"),    tr("rdp_ctx_add_sub"))
            menu.addSeparator()
            act_del = menu.addAction(QIcon.fromTheme("edit-delete"), tr("rdp_ctx_delete_grp"))
            act = menu.exec(self._tree.viewport().mapToGlobal(pos))
            if act == act_rename:
                self._rename_group(item_id)
            elif act == act_add_sub:
                self._new_subgroup(item_id)
            elif act == act_del:
                self._delete_group(item_id)

    # ── Slots — detail ─────────────────────────────────────────────────────

    def _show_detail(self, conn: RdpConnection) -> None:
        self._det_name.setText(conn.display_name)
        self._det_subtitle.setText(conn.subtitle)
        path = self._group_path(conn.group_id)
        self._det_group_path.setText(path)
        self._det_group_path.setVisible(bool(path))
        self._det["host"].setText(conn.host)
        self._det["port"].setText(str(conn.port))
        self._det["username"].setText(conn.username or "—")
        self._det["domain"].setText(conn.domain or "—")
        self._det["resolution"].setText(conn.resolution)
        self._det["fullscreen"].setText("✓" if conn.fullscreen else "—")
        self._det["notes"].setText(conn.notes or "")
        self._right.setCurrentIndex(_DETAIL)

    def _on_connect(self) -> None:
        conn = self._current_conn()
        if conn:
            self._launch_rdp(conn)

    def _on_edit(self) -> None:
        conn = self._current_conn()
        if conn is None:
            return
        self._editing_id = conn.id
        self._form_title.setText(tr("rdp_form_title_edit"))
        self._populate_group_combo(conn.group_id)
        self._f_name.setText(conn.name)
        self._f_host.setText(conn.host)
        self._f_port.setValue(conn.port)
        self._f_user.setText(conn.username)
        self._f_domain.setText(conn.domain)
        idx = self._f_resolution.findText(conn.resolution)
        if idx >= 0:
            self._f_resolution.setCurrentIndex(idx)
        else:
            self._f_resolution.setCurrentText(conn.resolution)
        self._f_fullscreen.setChecked(conn.fullscreen)
        self._f_notes.setPlainText(conn.notes)
        self._right.setCurrentIndex(_FORM)
        self._f_host.setFocus()

    def _on_delete(self) -> None:
        conn = self._current_conn()
        if conn is None:
            return
        ans = QMessageBox.question(
            self, tr("rdp_dlg_del_title"),
            tr("rdp_dlg_del_msg", name=conn.display_name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if ans != QMessageBox.StandardButton.Yes:
            return
        self._connections = [c for c in self._connections if c.id != conn.id]
        self._store.save(self._groups, self._connections)
        self._refresh_list()

    # ── Slots — form ───────────────────────────────────────────────────────

    def _on_new(self) -> None:
        preselect = ""
        item = self._tree.currentItem()
        if item:
            data = item.data(0, Qt.ItemDataRole.UserRole)
            if data and data[0] == 'group':
                preselect = data[1]
        self._editing_id = None
        self._form_title.setText(tr("rdp_form_title_new"))
        self._populate_group_combo(preselect)
        self._f_name.clear()
        self._f_host.clear()
        self._f_port.setValue(3389)
        self._f_user.clear()
        self._f_domain.clear()
        self._f_resolution.setCurrentIndex(0)
        self._f_fullscreen.setChecked(False)
        self._f_notes.clear()
        self._right.setCurrentIndex(_FORM)
        self._f_host.setFocus()

    def _on_save(self) -> None:
        host = self._f_host.text().strip()
        if not host:
            QMessageBox.warning(self, tr("rdp_dlg_req_title"), tr("rdp_dlg_req_msg"))
            self._f_host.setFocus()
            return
        updated = RdpConnection(
            id         = self._editing_id or str(uuid.uuid4()),
            name       = self._f_name.text().strip() or host,
            host       = host,
            port       = self._f_port.value(),
            username   = self._f_user.text().strip(),
            domain     = self._f_domain.text().strip(),
            resolution = self._f_resolution.currentText().strip(),
            fullscreen = self._f_fullscreen.isChecked(),
            notes      = self._f_notes.toPlainText().strip(),
            group_id   = self._f_group.currentData() or "",
        )
        if self._editing_id:
            self._connections = [
                updated if c.id == self._editing_id else c
                for c in self._connections
            ]
        else:
            self._connections.append(updated)
        self._store.save(self._groups, self._connections)
        self._refresh_list(select_conn_id=updated.id)

    def _on_cancel(self) -> None:
        conn = self._current_conn()
        if conn:
            self._show_detail(conn)
        else:
            self._right.setCurrentIndex(_EMPTY)

    # ── Slots — group management ───────────────────────────────────────────

    def _on_new_group(self) -> None:
        name, ok = QInputDialog.getText(self, tr("rdp_dlg_new_grp_title"), tr("rdp_dlg_new_grp_prompt"))
        if not ok or not name.strip():
            return
        top_groups = [g for g in self._groups if not g.parent_id]
        parent_id = ""
        if top_groups:
            choices = [tr("rdp_root_level")] + [g.name for g in top_groups]
            choice, ok2 = QInputDialog.getItem(
                self, tr("rdp_dlg_parent_title"), tr("rdp_dlg_parent_prompt"), choices, 0, False
            )
            if not ok2:
                return
            if choice != choices[0]:
                parent_id = top_groups[choices.index(choice) - 1].id
        self._groups.append(RdpGroup(name=name.strip(), parent_id=parent_id))
        self._store.save(self._groups, self._connections)
        self._refresh_list()

    def _new_subgroup(self, parent_group_id: str) -> None:
        parent = next((g for g in self._groups if g.id == parent_group_id), None)
        if parent is None:
            return
        name, ok = QInputDialog.getText(
            self, tr("rdp_dlg_new_sub_title"),
            tr("rdp_dlg_new_sub_prompt", parent=parent.name)
        )
        if not ok or not name.strip():
            return
        self._groups.append(RdpGroup(name=name.strip(), parent_id=parent_group_id))
        self._store.save(self._groups, self._connections)
        self._refresh_list()

    def _rename_group(self, group_id: str) -> None:
        grp = next((g for g in self._groups if g.id == group_id), None)
        if grp is None:
            return
        name, ok = QInputDialog.getText(
            self, tr("rdp_dlg_rename_title"), tr("rdp_dlg_rename_prompt"), text=grp.name
        )
        if ok and name.strip():
            grp.name = name.strip()
            self._store.save(self._groups, self._connections)
            self._refresh_list()

    def _delete_group(self, group_id: str) -> None:
        grp = next((g for g in self._groups if g.id == group_id), None)
        if grp is None:
            return
        ans = QMessageBox.question(
            self, tr("rdp_dlg_del_grp_title"),
            tr("rdp_dlg_del_grp_msg", name=grp.name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if ans != QMessageBox.StandardButton.Yes:
            return
        ids_to_remove: set[str] = set()
        def collect(gid: str) -> None:
            ids_to_remove.add(gid)
            for sub in self._groups:
                if sub.parent_id == gid:
                    collect(sub.id)
        collect(group_id)
        for conn in self._connections:
            if conn.group_id in ids_to_remove:
                conn.group_id = ""
        self._groups = [g for g in self._groups if g.id not in ids_to_remove]
        self._store.save(self._groups, self._connections)
        self._refresh_list()

    # ── RDP launch ─────────────────────────────────────────────────────────

    def _launch_rdp(self, conn: RdpConnection) -> None:
        if not shutil.which("xfreerdp"):
            QMessageBox.warning(self, tr("rdp_missing_title"), tr("rdp_missing_msg"))
            return
        password, ok = QInputDialog.getText(
            self,
            conn.display_name,
            tr("rdp_password_prompt"),
            QLineEdit.EchoMode.Password,
        )
        if not ok:
            return
        args = build_rdp_args(conn, password)
        proc = QProcess(self)
        proc.startDetached(args[0], args[1:])
```

- [ ] **Step 2: Verify syntax**

```bash
cd /home/luust/claude-projects/nmlinux && python -c "from nmlinux.pages.rdp import RdpPage; print('OK')"
```
Expected: `OK`

- [ ] **Step 3: Run existing tests to confirm no regression**

```bash
cd /home/luust/claude-projects/nmlinux && python -m pytest tests/ -v
```
Expected: all tests PASS.

- [ ] **Step 4: Commit**

```bash
cd /home/luust/claude-projects/nmlinux
git add nmlinux/pages/rdp.py
git commit -m "feat(rdp): add pages/rdp.py — RDP connection manager UI"
```

---

## Task 4: `window.py` — sidebar integration

**Files:**
- Modify: `nmlinux/window.py`

- [ ] **Step 1: Add import**

In `nmlinux/window.py`, add after the `from nmlinux.pages.ssh import SshPage` line (line 25):

```python
from nmlinux.pages.rdp import RdpPage
```

- [ ] **Step 2: Add `_TOOLS` entry**

In `nmlinux/window.py`, add after the SSH entry (after line 109):

```python
    (
        ("computer", "network-workgroup", "preferences-desktop-remote-desktop"),
        "Remote Desktop", RdpPage,
        "Gère les profils de connexion Bureau à distance (RDP)\net lance xfreerdp vers des machines Windows.",
    ),
```

- [ ] **Step 3: Verify import and app startup**

```bash
cd /home/luust/claude-projects/nmlinux && python -c "from nmlinux.window import MainWindow; print('OK')"
```
Expected: `OK`

- [ ] **Step 4: Manual smoke test**

Launch the app:
```bash
cd /home/luust/claude-projects/nmlinux && python -m nmlinux
```

Check:
- "Remote Desktop" entry visible in sidebar after SSH
- Clicking it shows the RDP page (empty state with invite message)
- `[+ Connexion]` opens the form with all fields (host, port, user, domain, resolution, fullscreen checkbox, notes)
- Save a profile → appears in tree
- Edit → form pre-filled correctly
- Delete → removed from tree
- Group creation / rename / delete works
- `[Se connecter]` prompts for password then (if xfreerdp absent) shows install message

- [ ] **Step 5: Commit**

```bash
cd /home/luust/claude-projects/nmlinux
git add nmlinux/window.py
git commit -m "feat(rdp): wire RDP module into sidebar"
```

---

## Task 5: version bump + push

**Files:**
- Modify: `nmlinux/main.py` or wherever version is declared (check `grep -r "1\.2\.7" nmlinux/`)
- Modify: `README.md` changelog section

- [ ] **Step 1: Find version string**

```bash
grep -r "1\.2\.7\|__version__\|version" /home/luust/claude-projects/nmlinux/nmlinux/main.py | head -5
grep -r "__version__" /home/luust/claude-projects/nmlinux/nmlinux/ | head -5
```

- [ ] **Step 2: Bump to v1.2.8**

Update version string from `1.2.7` to `1.2.8` wherever it appears (main.py, pyproject.toml, README.md title).

- [ ] **Step 3: Add changelog entry in README.md**

Add above the `### v1.2.7` section:

```markdown
### v1.2.8 — 2026-05-30

- **Remote Desktop (RDP)** — new module for managing Windows RDP connection profiles; groups/subgroups like SSH; launches `xfreerdp` as an external process; password prompted at connect time, never stored; resolution, fullscreen, domain fields; detects missing `xfreerdp` with distro-specific install instructions
```

- [ ] **Step 4: Final test run**

```bash
cd /home/luust/claude-projects/nmlinux && python -m pytest tests/ -v
```
Expected: all tests PASS.

- [ ] **Step 5: Commit and push**

```bash
cd /home/luust/claude-projects/nmlinux
git add -p   # stage only version + README changes
git commit -m "chore: bump to v1.2.8 — add RDP module"
git push origin main
```
