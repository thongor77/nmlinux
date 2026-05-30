# VNC Module Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a VNC module to NMLinux that manages connection profiles and launches `vncviewer` (TigerVNC) with password passed via stdin.

**Architecture:** Mirror `core/rdp.py` + `pages/rdp.py` exactly — same splitter/tree/EMPTY-DETAIL-FORM pattern. Key difference: no domain/resolution/fullscreen fields, and launch uses `subprocess.Popen(stdin=PIPE, start_new_session=True)` to write the password to vncviewer's stdin via `-autopass`.

**Tech Stack:** Python 3, PySide6 (Qt 6), `vncviewer` (TigerVNC), `subprocess.Popen`, `QInputDialog`

---

## File Map

| Action | Path |
|--------|------|
| Create | `nmlinux/core/vnc.py` |
| Create | `nmlinux/pages/vnc.py` |
| Create | `tests/test_vnc_core.py` |
| Modify | `nmlinux/core/i18n.py` — add `nav_vnc` + `vnc_*` keys in fr/en/es/de |
| Modify | `nmlinux/window.py` — import VncPage, add sidebar entry |
| Modify | `pyproject.toml` — bump version to 1.2.9 |
| Modify | `README.md` — add v1.2.9 changelog entry |

---

## Task 1: `core/vnc.py` — data model, persistence, arg builder

**Files:**
- Create: `nmlinux/core/vnc.py`
- Create: `tests/test_vnc_core.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_vnc_core.py`:

```python
from __future__ import annotations
import json
from pathlib import Path
from nmlinux.core.vnc import (
    VncGroup, VncConnection, VncStore, build_vnc_args
)


# ── build_vnc_args ─────────────────────────────────────────────────────────

def test_args_basic():
    conn = VncConnection(host="192.168.1.20", port=5900)
    args = build_vnc_args(conn, "vncviewer")
    assert args[0] == "vncviewer"
    assert "-autopass" in args
    assert "192.168.1.20::5900" in args

def test_args_with_username():
    conn = VncConnection(host="192.168.1.20", port=5900, username="luust")
    args = build_vnc_args(conn, "vncviewer")
    assert "-username" in args
    assert "luust" in args

def test_args_no_username():
    conn = VncConnection(host="192.168.1.20", port=5900, username="")
    args = build_vnc_args(conn, "vncviewer")
    assert "-username" not in args

def test_args_custom_binary():
    conn = VncConnection(host="srv", port=5901)
    args = build_vnc_args(conn, "tigervnc")
    assert args[0] == "tigervnc"

def test_args_port_format():
    conn = VncConnection(host="myhost", port=5902)
    args = build_vnc_args(conn, "vncviewer")
    assert "myhost::5902" in args


# ── VncConnection defaults ─────────────────────────────────────────────────

def test_connection_defaults():
    conn = VncConnection()
    assert conn.port == 5900
    assert conn.username == ""
    assert conn.group_id == ""

def test_display_name_uses_name():
    conn = VncConnection(name="MacBook", host="192.168.1.20")
    assert conn.display_name == "MacBook"

def test_display_name_falls_back_to_host():
    conn = VncConnection(name="", host="192.168.1.20")
    assert conn.display_name == "192.168.1.20"

def test_subtitle_with_username():
    conn = VncConnection(host="srv", username="luust", port=5900)
    assert "luust" in conn.subtitle
    assert "srv" in conn.subtitle

def test_subtitle_default_port_omitted():
    conn = VncConnection(host="srv", port=5900)
    sub = conn.subtitle
    assert "5900" not in sub

def test_subtitle_nondefault_port_shown():
    conn = VncConnection(host="srv", port=5901)
    assert "5901" in conn.subtitle


# ── VncStore ───────────────────────────────────────────────────────────────

def test_store_roundtrip(tmp_path):
    path = tmp_path / "vnc.json"
    store = VncStore(path)
    groups = [VncGroup(name="macOS"), VncGroup(name="Linux")]
    conns = [
        VncConnection(name="MacBook", host="192.168.1.20", username="luust"),
        VncConnection(name="Plex", host="192.168.1.30"),
    ]
    store.save(groups, conns)
    lg, lc = store.load()
    assert len(lg) == 2
    assert len(lc) == 2
    assert lc[0].username == "luust"

def test_store_load_missing_file(tmp_path):
    store = VncStore(tmp_path / "missing.json")
    groups, conns = store.load()
    assert groups == []
    assert conns == []

def test_store_load_corrupt_file(tmp_path):
    path = tmp_path / "vnc.json"
    path.write_text("not json")
    store = VncStore(path)
    groups, conns = store.load()
    assert groups == []
    assert conns == []

def test_store_json_format(tmp_path):
    path = tmp_path / "vnc.json"
    store = VncStore(path)
    store.save([VncGroup(name="G")], [VncConnection(name="C", host="h")])
    raw = json.loads(path.read_text())
    assert raw["version"] == 2
    assert "groups" in raw
    assert "connections" in raw
```

- [ ] **Step 2: Verify tests fail**

```bash
cd /home/luust/claude-projects/nmlinux && python3 -c "from nmlinux.core.vnc import VncConnection" 2>&1 | head -5
```
Expected: `ModuleNotFoundError: No module named 'nmlinux.core.vnc'`

- [ ] **Step 3: Create `nmlinux/core/vnc.py`**

```python
"""VNC connection profiles — pure logic, no Qt dependency."""

from __future__ import annotations

import json
import shutil
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path

# TigerVNC binary names vary by distro
_VNCVIEWER_CANDIDATES = ["vncviewer", "tigervnc"]


def find_vncviewer() -> str | None:
    for name in _VNCVIEWER_CANDIDATES:
        if shutil.which(name):
            return name
    return None


# ── Model ──────────────────────────────────────────────────────────────────


@dataclass
class VncGroup:
    id:        str = field(default_factory=lambda: str(uuid.uuid4()))
    name:      str = ""
    parent_id: str = ""


@dataclass
class VncConnection:
    id:       str = field(default_factory=lambda: str(uuid.uuid4()))
    name:     str = ""
    host:     str = ""
    port:     int = 5900
    username: str = ""
    notes:    str = ""
    group_id: str = ""

    @property
    def display_name(self) -> str:
        return self.name if self.name else self.host

    @property
    def subtitle(self) -> str:
        target = f"{self.username}@{self.host}" if self.username else self.host
        return f"{target}:{self.port}" if self.port != 5900 else target


# ── Persistence ────────────────────────────────────────────────────────────


class VncStore:
    def __init__(self, path: Path | None = None) -> None:
        if path is None:
            data_dir = Path.home() / ".local" / "share" / "nmlinux"
            data_dir.mkdir(parents=True, exist_ok=True)
            path = data_dir / "vnc_connections.json"
        self._path = path

    def load(self) -> tuple[list[VncGroup], list[VncConnection]]:
        if not self._path.exists():
            return [], []
        try:
            raw = json.loads(self._path.read_text())
            conn_fields  = VncConnection.__dataclass_fields__
            group_fields = VncGroup.__dataclass_fields__
            groups = [
                VncGroup(**{k: v for k, v in g.items() if k in group_fields})
                for g in raw.get("groups", [])
            ]
            conns = [
                VncConnection(**{k: v for k, v in c.items() if k in conn_fields})
                for c in raw.get("connections", [])
            ]
            return groups, conns
        except Exception:
            return [], []

    def save(self, groups: list[VncGroup], connections: list[VncConnection]) -> None:
        data = {
            "version": 2,
            "groups": [asdict(g) for g in groups],
            "connections": [asdict(c) for c in connections],
        }
        self._path.write_text(json.dumps(data, indent=2, ensure_ascii=False))


# ── Args builder ───────────────────────────────────────────────────────────


def build_vnc_args(conn: VncConnection, binary: str) -> list[str]:
    args = [binary, "-autopass"]
    if conn.username:
        args += ["-username", conn.username]
    args.append(f"{conn.host}::{conn.port}")
    return args
```

- [ ] **Step 4: Verify tests pass**

```bash
cd /home/luust/claude-projects/nmlinux && python3 -c "
import json, tempfile
from pathlib import Path
from nmlinux.core.vnc import VncGroup, VncConnection, VncStore, build_vnc_args

# build_vnc_args
conn = VncConnection(host='192.168.1.20', port=5900, username='luust')
args = build_vnc_args(conn, 'vncviewer')
assert args[0] == 'vncviewer'
assert '-autopass' in args
assert '-username' in args and 'luust' in args
assert '192.168.1.20::5900' in args

conn2 = VncConnection(host='srv', port=5900, username='')
args2 = build_vnc_args(conn2, 'vncviewer')
assert '-username' not in args2

# defaults
c = VncConnection()
assert c.port == 5900 and c.username == ''

# display_name
assert VncConnection(name='Mac', host='1.2.3.4').display_name == 'Mac'
assert VncConnection(name='', host='1.2.3.4').display_name == '1.2.3.4'

# store roundtrip
with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / 'vnc.json'
    store = VncStore(path)
    store.save([VncGroup(name='macOS')], [VncConnection(name='Mac', host='h', username='u')])
    lg, lc = store.load()
    assert len(lg) == 1 and lc[0].username == 'u'
    g2, c2 = VncStore(Path(tmp) / 'missing.json').load()
    assert g2 == [] and c2 == []

print('All vnc core tests PASSED')
"
```
Expected: `All vnc core tests PASSED`

- [ ] **Step 5: Commit**

```bash
cd /home/luust/claude-projects/nmlinux
git add nmlinux/core/vnc.py tests/test_vnc_core.py
git commit -m "feat(vnc): add core/vnc.py — models, store, build_vnc_args"
```

---

## Task 2: i18n — add VNC keys in fr / en / es / de

**Files:**
- Modify: `nmlinux/core/i18n.py`

- [ ] **Step 1: Add `nav_vnc` in all 4 language blocks**

Find each `"nav_rdp": "Remote Desktop"` line (at lines 22, 617, 1195, 1775) and add `nav_vnc` immediately after. Do this for all 4 blocks:

```python
        "nav_rdp":          "Remote Desktop",
        "nav_vnc":          "VNC",
```

(Same value "VNC" in all 4 languages — it's a proper name.)

- [ ] **Step 2: Add `vnc_*` keys in French block**

Find the French `rdp_missing_msg` line (line ~402) and insert after it, before `# ── Settings ──`:

```python
        "rdp_missing_msg":         "xfreerdp n'est pas installé.\n\nArch : sudo pacman -S freerdp\nDebian/Ubuntu : sudo apt install freerdp2-x11\nFedora : sudo dnf install freerdp",

        # ── VNC ─────────────────────────────────────────────────────────────
        "vnc_new_conn_btn":        "Nouvelle connexion",
        "vnc_new_grp_btn":         "Nouveau groupe",
        "vnc_empty_state":         "Sélectionnez une connexion\nou créez-en une nouvelle.",
        "vnc_det_lbl_host":        "Hôte",
        "vnc_det_lbl_port":        "Port",
        "vnc_det_lbl_user":        "Utilisateur",
        "vnc_det_lbl_notes":       "Notes",
        "vnc_connect_btn":         "Se connecter",
        "vnc_edit_btn":            "Modifier",
        "vnc_delete_btn":          "Supprimer",
        "vnc_form_lbl_name":       "Nom :",
        "vnc_form_lbl_group":      "Groupe :",
        "vnc_form_lbl_host":       "Hôte * :",
        "vnc_form_lbl_port":       "Port :",
        "vnc_form_lbl_user":       "Utilisateur :",
        "vnc_form_lbl_notes":      "Notes :",
        "vnc_form_name_ph":        "Mon Mac",
        "vnc_form_user_ph":        "luust",
        "vnc_save_btn":            "Enregistrer",
        "vnc_cancel_btn":          "Annuler",
        "vnc_form_title_new":      "Nouvelle connexion VNC",
        "vnc_form_title_edit":     "Modifier la connexion VNC",
        "vnc_ctx_connect":         "Se connecter",
        "vnc_ctx_edit":            "Modifier",
        "vnc_ctx_delete":          "Supprimer",
        "vnc_ctx_rename_grp":      "Renommer",
        "vnc_ctx_add_sub":         "Ajouter un sous-groupe",
        "vnc_ctx_delete_grp":      "Supprimer le groupe",
        "vnc_no_group":            "— Aucun groupe —",
        "vnc_root_level":          "— Niveau racine —",
        "vnc_dlg_new_grp_title":   "Nouveau groupe",
        "vnc_dlg_new_grp_prompt":  "Nom du groupe :",
        "vnc_dlg_parent_title":    "Groupe parent",
        "vnc_dlg_parent_prompt":   "Placer dans :",
        "vnc_dlg_new_sub_title":   "Nouveau sous-groupe",
        "vnc_dlg_new_sub_prompt":  "Sous-groupe de «{parent}» :",
        "vnc_dlg_rename_title":    "Renommer",
        "vnc_dlg_rename_prompt":   "Nouveau nom :",
        "vnc_dlg_req_title":       "Champ requis",
        "vnc_dlg_req_msg":         "L'hôte est requis.",
        "vnc_dlg_del_title":       "Supprimer",
        "vnc_dlg_del_msg":         "Supprimer «{name}» ?",
        "vnc_dlg_del_grp_title":   "Supprimer le groupe",
        "vnc_dlg_del_grp_msg":     "Supprimer «{name}» ?\nLes connexions seront déplacées à la racine.",
        "vnc_password_prompt":     "Mot de passe VNC :",
        "vnc_missing_title":       "vncviewer introuvable",
        "vnc_missing_msg":         "TigerVNC n'est pas installé.\n\nArch : sudo pacman -S tigervnc\nDebian/Ubuntu : sudo apt install tigervnc-viewer\nFedora : sudo dnf install tigervnc",
```

- [ ] **Step 3: Add `vnc_*` keys in English block**

Find English `rdp_missing_msg` (line ~982) and insert after it, before `"settings_title"`:

```python
        "rdp_missing_msg":         "xfreerdp is not installed.\n\nArch: sudo pacman -S freerdp\nDebian/Ubuntu: sudo apt install freerdp2-x11\nFedora: sudo dnf install freerdp",

        # ── VNC ─────────────────────────────────────────────────────────────
        "vnc_new_conn_btn":        "New connection",
        "vnc_new_grp_btn":         "New group",
        "vnc_empty_state":         "Select a connection\nor create a new one.",
        "vnc_det_lbl_host":        "Host",
        "vnc_det_lbl_port":        "Port",
        "vnc_det_lbl_user":        "Username",
        "vnc_det_lbl_notes":       "Notes",
        "vnc_connect_btn":         "Connect",
        "vnc_edit_btn":            "Edit",
        "vnc_delete_btn":          "Delete",
        "vnc_form_lbl_name":       "Name:",
        "vnc_form_lbl_group":      "Group:",
        "vnc_form_lbl_host":       "Host *:",
        "vnc_form_lbl_port":       "Port:",
        "vnc_form_lbl_user":       "Username:",
        "vnc_form_lbl_notes":      "Notes:",
        "vnc_form_name_ph":        "My Mac",
        "vnc_form_user_ph":        "luust",
        "vnc_save_btn":            "Save",
        "vnc_cancel_btn":          "Cancel",
        "vnc_form_title_new":      "New VNC connection",
        "vnc_form_title_edit":     "Edit VNC connection",
        "vnc_ctx_connect":         "Connect",
        "vnc_ctx_edit":            "Edit",
        "vnc_ctx_delete":          "Delete",
        "vnc_ctx_rename_grp":      "Rename",
        "vnc_ctx_add_sub":         "Add subgroup",
        "vnc_ctx_delete_grp":      "Delete group",
        "vnc_no_group":            "— No group —",
        "vnc_root_level":          "— Root level —",
        "vnc_dlg_new_grp_title":   "New group",
        "vnc_dlg_new_grp_prompt":  "Group name:",
        "vnc_dlg_parent_title":    "Parent group",
        "vnc_dlg_parent_prompt":   "Place in:",
        "vnc_dlg_new_sub_title":   "New subgroup",
        "vnc_dlg_new_sub_prompt":  "Subgroup of «{parent}»:",
        "vnc_dlg_rename_title":    "Rename",
        "vnc_dlg_rename_prompt":   "New name:",
        "vnc_dlg_req_title":       "Required field",
        "vnc_dlg_req_msg":         "Host is required.",
        "vnc_dlg_del_title":       "Delete",
        "vnc_dlg_del_msg":         "Delete «{name}»?",
        "vnc_dlg_del_grp_title":   "Delete group",
        "vnc_dlg_del_grp_msg":     "Delete «{name}»?\nConnections will be moved to root.",
        "vnc_password_prompt":     "VNC password:",
        "vnc_missing_title":       "vncviewer not found",
        "vnc_missing_msg":         "TigerVNC is not installed.\n\nArch: sudo pacman -S tigervnc\nDebian/Ubuntu: sudo apt install tigervnc-viewer\nFedora: sudo dnf install tigervnc",
```

- [ ] **Step 4: Add `vnc_*` keys in Spanish block**

Find Spanish `rdp_missing_msg` (line ~1543) and insert after it, before `"nav_about": "Acerca de"`:

```python
        "rdp_missing_msg":         "xfreerdp no está instalado.\n\nArch: sudo pacman -S freerdp\nDebian/Ubuntu: sudo apt install freerdp2-x11\nFedora: sudo dnf install freerdp",

        # ── VNC ─────────────────────────────────────────────────────────────
        "vnc_new_conn_btn":        "Nueva conexión",
        "vnc_new_grp_btn":         "Nuevo grupo",
        "vnc_empty_state":         "Seleccione una conexión\no cree una nueva.",
        "vnc_det_lbl_host":        "Host",
        "vnc_det_lbl_port":        "Puerto",
        "vnc_det_lbl_user":        "Usuario",
        "vnc_det_lbl_notes":       "Notas",
        "vnc_connect_btn":         "Conectar",
        "vnc_edit_btn":            "Editar",
        "vnc_delete_btn":          "Eliminar",
        "vnc_form_lbl_name":       "Nombre:",
        "vnc_form_lbl_group":      "Grupo:",
        "vnc_form_lbl_host":       "Host *:",
        "vnc_form_lbl_port":       "Puerto:",
        "vnc_form_lbl_user":       "Usuario:",
        "vnc_form_lbl_notes":      "Notas:",
        "vnc_form_name_ph":        "Mi Mac",
        "vnc_form_user_ph":        "luust",
        "vnc_save_btn":            "Guardar",
        "vnc_cancel_btn":          "Cancelar",
        "vnc_form_title_new":      "Nueva conexión VNC",
        "vnc_form_title_edit":     "Editar conexión VNC",
        "vnc_ctx_connect":         "Conectar",
        "vnc_ctx_edit":            "Editar",
        "vnc_ctx_delete":          "Eliminar",
        "vnc_ctx_rename_grp":      "Renombrar",
        "vnc_ctx_add_sub":         "Agregar subgrupo",
        "vnc_ctx_delete_grp":      "Eliminar grupo",
        "vnc_no_group":            "— Sin grupo —",
        "vnc_root_level":          "— Nivel raíz —",
        "vnc_dlg_new_grp_title":   "Nuevo grupo",
        "vnc_dlg_new_grp_prompt":  "Nombre del grupo:",
        "vnc_dlg_parent_title":    "Grupo padre",
        "vnc_dlg_parent_prompt":   "Colocar en:",
        "vnc_dlg_new_sub_title":   "Nuevo subgrupo",
        "vnc_dlg_new_sub_prompt":  "Subgrupo de «{parent}»:",
        "vnc_dlg_rename_title":    "Renombrar",
        "vnc_dlg_rename_prompt":   "Nuevo nombre:",
        "vnc_dlg_req_title":       "Campo requerido",
        "vnc_dlg_req_msg":         "El host es obligatorio.",
        "vnc_dlg_del_title":       "Eliminar",
        "vnc_dlg_del_msg":         "¿Eliminar «{name}»?",
        "vnc_dlg_del_grp_title":   "Eliminar grupo",
        "vnc_dlg_del_grp_msg":     "¿Eliminar «{name}»?\nLas conexiones se moverán a la raíz.",
        "vnc_password_prompt":     "Contraseña VNC:",
        "vnc_missing_title":       "vncviewer no encontrado",
        "vnc_missing_msg":         "TigerVNC no está instalado.\n\nArch: sudo pacman -S tigervnc\nDebian/Ubuntu: sudo apt install tigervnc-viewer\nFedora: sudo dnf install tigervnc",
```

- [ ] **Step 5: Add `vnc_*` keys in German block**

Find German `rdp_missing_msg` (line ~2123) and insert after it, before `"nav_about": "Über"`:

```python
        "rdp_missing_msg":         "xfreerdp ist nicht installiert.\n\nArch: sudo pacman -S freerdp\nDebian/Ubuntu: sudo apt install freerdp2-x11\nFedora: sudo dnf install freerdp",

        # ── VNC ─────────────────────────────────────────────────────────────
        "vnc_new_conn_btn":        "Neue Verbindung",
        "vnc_new_grp_btn":         "Neue Gruppe",
        "vnc_empty_state":         "Verbindung auswählen\noder neue erstellen.",
        "vnc_det_lbl_host":        "Host",
        "vnc_det_lbl_port":        "Port",
        "vnc_det_lbl_user":        "Benutzer",
        "vnc_det_lbl_notes":       "Notizen",
        "vnc_connect_btn":         "Verbinden",
        "vnc_edit_btn":            "Bearbeiten",
        "vnc_delete_btn":          "Löschen",
        "vnc_form_lbl_name":       "Name:",
        "vnc_form_lbl_group":      "Gruppe:",
        "vnc_form_lbl_host":       "Host *:",
        "vnc_form_lbl_port":       "Port:",
        "vnc_form_lbl_user":       "Benutzer:",
        "vnc_form_lbl_notes":      "Notizen:",
        "vnc_form_name_ph":        "Mein Mac",
        "vnc_form_user_ph":        "luust",
        "vnc_save_btn":            "Speichern",
        "vnc_cancel_btn":          "Abbrechen",
        "vnc_form_title_new":      "Neue VNC-Verbindung",
        "vnc_form_title_edit":     "VNC-Verbindung bearbeiten",
        "vnc_ctx_connect":         "Verbinden",
        "vnc_ctx_edit":            "Bearbeiten",
        "vnc_ctx_delete":          "Löschen",
        "vnc_ctx_rename_grp":      "Umbenennen",
        "vnc_ctx_add_sub":         "Untergruppe hinzufügen",
        "vnc_ctx_delete_grp":      "Gruppe löschen",
        "vnc_no_group":            "— Keine Gruppe —",
        "vnc_root_level":          "— Stammebene —",
        "vnc_dlg_new_grp_title":   "Neue Gruppe",
        "vnc_dlg_new_grp_prompt":  "Gruppenname:",
        "vnc_dlg_parent_title":    "Übergeordnete Gruppe",
        "vnc_dlg_parent_prompt":   "Platzieren in:",
        "vnc_dlg_new_sub_title":   "Neue Untergruppe",
        "vnc_dlg_new_sub_prompt":  "Untergruppe von «{parent}»:",
        "vnc_dlg_rename_title":    "Umbenennen",
        "vnc_dlg_rename_prompt":   "Neuer Name:",
        "vnc_dlg_req_title":       "Pflichtfeld",
        "vnc_dlg_req_msg":         "Host ist erforderlich.",
        "vnc_dlg_del_title":       "Löschen",
        "vnc_dlg_del_msg":         "«{name}» löschen?",
        "vnc_dlg_del_grp_title":   "Gruppe löschen",
        "vnc_dlg_del_grp_msg":     "«{name}» löschen?\nVerbindungen werden in die Stammebene verschoben.",
        "vnc_password_prompt":     "VNC-Passwort:",
        "vnc_missing_title":       "vncviewer nicht gefunden",
        "vnc_missing_msg":         "TigerVNC ist nicht installiert.\n\nArch: sudo pacman -S tigervnc\nDebian/Ubuntu: sudo apt install tigervnc-viewer\nFedora: sudo dnf install tigervnc",
```

- [ ] **Step 6: Verify i18n**

```bash
cd /home/luust/claude-projects/nmlinux && python3 -c "
from nmlinux.core.i18n import tr
print(tr('nav_vnc'))
print(tr('vnc_connect_btn'))
print(tr('vnc_missing_title'))
"
```
Expected:
```
VNC
Connect
vncviewer not found
```

- [ ] **Step 7: Commit**

```bash
cd /home/luust/claude-projects/nmlinux
git add nmlinux/core/i18n.py
git commit -m "feat(vnc): add i18n keys for VNC module (fr/en/es/de)"
```

---

## Task 3: `pages/vnc.py` — Qt UI page

**Files:**
- Create: `nmlinux/pages/vnc.py`

- [ ] **Step 1: Create `nmlinux/pages/vnc.py`**

```python
from __future__ import annotations

import subprocess
import uuid

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QFormLayout,
    QTreeWidget, QTreeWidgetItem,
    QStackedWidget,
    QLabel, QLineEdit, QSpinBox, QPushButton, QTextEdit,
    QFrame, QGroupBox, QSplitter,
    QMessageBox, QComboBox, QInputDialog, QMenu,
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt

from nmlinux.core.vnc import VncConnection, VncGroup, VncStore, build_vnc_args, find_vncviewer
from nmlinux.core.i18n import tr

_EMPTY  = 0
_DETAIL = 1
_FORM   = 2


class VncPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._store = VncStore()
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

    def _build_left(self) -> QWidget:
        panel = QFrame()
        panel.setFrameShape(QFrame.Shape.NoFrame)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 4, 8)
        layout.setSpacing(4)

        btn_new_conn = QPushButton(QIcon.fromTheme("list-add"), " " + tr("vnc_new_conn_btn"))
        btn_new_conn.clicked.connect(self._on_new)
        btn_new_grp  = QPushButton(QIcon.fromTheme("folder-new"), " " + tr("vnc_new_grp_btn"))
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

    def _build_right(self) -> QStackedWidget:
        self._right = QStackedWidget()
        self._right.addWidget(self._build_empty())
        self._right.addWidget(self._build_detail())
        self._right.addWidget(self._build_form())
        return self._right

    def _build_empty(self) -> QWidget:
        w = QWidget()
        lbl = QLabel(tr("vnc_empty_state"))
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("color: palette(mid); font-size: 14px;")
        QVBoxLayout(w).addWidget(lbl)
        return w

    def _build_detail(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        self._det_name       = QLabel()
        self._det_name.setStyleSheet("font-size: 18px; font-weight: bold;")
        self._det_subtitle   = QLabel()
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
            ("host",     "vnc_det_lbl_host"),
            ("port",     "vnc_det_lbl_port"),
            ("username", "vnc_det_lbl_user"),
            ("notes",    "vnc_det_lbl_notes"),
        ]:
            val = QLabel()
            val.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            val.setWordWrap(True)
            self._det[key] = val
            form.addRow(tr(lbl_key) + " :", val)
        layout.addWidget(card)
        layout.addStretch(1)

        row = QHBoxLayout()
        self._btn_connect = QPushButton(QIcon.fromTheme("network-connect"), " " + tr("vnc_connect_btn"))
        self._btn_connect.setDefault(True)
        self._btn_connect.clicked.connect(self._on_connect)
        btn_edit = QPushButton(QIcon.fromTheme("document-edit"), " " + tr("vnc_edit_btn"))
        btn_edit.clicked.connect(self._on_edit)
        btn_del  = QPushButton(QIcon.fromTheme("edit-delete"), " " + tr("vnc_delete_btn"))
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

        self._f_name  = QLineEdit(); self._f_name.setPlaceholderText(tr("vnc_form_name_ph"))
        self._f_group = QComboBox()
        self._f_host  = QLineEdit(); self._f_host.setPlaceholderText("192.168.1.20")
        self._f_port  = QSpinBox();  self._f_port.setRange(1, 65535); self._f_port.setValue(5900)
        self._f_user  = QLineEdit(); self._f_user.setPlaceholderText(tr("vnc_form_user_ph"))
        self._f_notes = QTextEdit(); self._f_notes.setMaximumHeight(80)

        form.addRow(tr("vnc_form_lbl_name"),  self._f_name)
        form.addRow(tr("vnc_form_lbl_group"), self._f_group)
        form.addRow(tr("vnc_form_lbl_host"),  self._f_host)
        form.addRow(tr("vnc_form_lbl_port"),  self._f_port)
        form.addRow(tr("vnc_form_lbl_user"),  self._f_user)
        form.addRow(tr("vnc_form_lbl_notes"), self._f_notes)
        layout.addWidget(card)
        layout.addStretch(1)

        row = QHBoxLayout()
        btn_save   = QPushButton(QIcon.fromTheme("document-save"), " " + tr("vnc_save_btn"))
        btn_save.setDefault(True); btn_save.clicked.connect(self._on_save)
        btn_cancel = QPushButton(QIcon.fromTheme("dialog-cancel"), " " + tr("vnc_cancel_btn"))
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

    def _build_tree_children(self, parent_item, parent_group_id, icon_conn, icon_grp) -> None:
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
        def walk(parent) -> bool:
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
        def walk(parent) -> bool:
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

    def _current_conn(self) -> VncConnection | None:
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
        self._f_group.addItem(tr("vnc_no_group"), "")

        def add_group(grp: VncGroup, indent: int) -> None:
            self._f_group.addItem("    " * indent + grp.name, grp.id)
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

    def _on_selection_changed(self, current, _prev) -> None:
        if current is None:
            self._right.setCurrentIndex(_EMPTY); return
        data = current.data(0, Qt.ItemDataRole.UserRole)
        if data is None or data[0] != 'conn':
            self._right.setCurrentIndex(_EMPTY); return
        conn = next((c for c in self._connections if c.id == data[1]), None)
        if conn:
            self._show_detail(conn)

    def _on_item_double_clicked(self, item, _col: int) -> None:
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data and data[0] == 'conn':
            conn = next((c for c in self._connections if c.id == data[1]), None)
            if conn:
                self._launch_vnc(conn)

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
            act_connect = menu.addAction(QIcon.fromTheme("network-connect"), tr("vnc_ctx_connect"))
            menu.addSeparator()
            act_edit = menu.addAction(QIcon.fromTheme("document-edit"), tr("vnc_ctx_edit"))
            act_del  = menu.addAction(QIcon.fromTheme("edit-delete"),   tr("vnc_ctx_delete"))
            act = menu.exec(self._tree.viewport().mapToGlobal(pos))
            if act == act_connect:
                self._launch_vnc(conn)
            elif act == act_edit:
                self._tree.setCurrentItem(item); self._on_edit()
            elif act == act_del:
                self._tree.setCurrentItem(item); self._on_delete()

        elif kind == 'group':
            grp = next((g for g in self._groups if g.id == item_id), None)
            if grp is None:
                return
            act_rename  = menu.addAction(QIcon.fromTheme("document-edit"), tr("vnc_ctx_rename_grp"))
            act_add_sub = menu.addAction(QIcon.fromTheme("folder-new"),    tr("vnc_ctx_add_sub"))
            menu.addSeparator()
            act_del = menu.addAction(QIcon.fromTheme("edit-delete"), tr("vnc_ctx_delete_grp"))
            act = menu.exec(self._tree.viewport().mapToGlobal(pos))
            if act == act_rename:
                self._rename_group(item_id)
            elif act == act_add_sub:
                self._new_subgroup(item_id)
            elif act == act_del:
                self._delete_group(item_id)

    # ── Slots — detail ─────────────────────────────────────────────────────

    def _show_detail(self, conn: VncConnection) -> None:
        self._det_name.setText(conn.display_name)
        self._det_subtitle.setText(conn.subtitle)
        path = self._group_path(conn.group_id)
        self._det_group_path.setText(path)
        self._det_group_path.setVisible(bool(path))
        self._det["host"].setText(conn.host)
        self._det["port"].setText(str(conn.port))
        self._det["username"].setText(conn.username or "—")
        self._det["notes"].setText(conn.notes or "")
        self._right.setCurrentIndex(_DETAIL)

    def _on_connect(self) -> None:
        conn = self._current_conn()
        if conn:
            self._launch_vnc(conn)

    def _on_edit(self) -> None:
        conn = self._current_conn()
        if conn is None:
            return
        self._editing_id = conn.id
        self._form_title.setText(tr("vnc_form_title_edit"))
        self._populate_group_combo(conn.group_id)
        self._f_name.setText(conn.name)
        self._f_host.setText(conn.host)
        self._f_port.setValue(conn.port)
        self._f_user.setText(conn.username)
        self._f_notes.setPlainText(conn.notes)
        self._right.setCurrentIndex(_FORM)
        self._f_host.setFocus()

    def _on_delete(self) -> None:
        conn = self._current_conn()
        if conn is None:
            return
        ans = QMessageBox.question(
            self, tr("vnc_dlg_del_title"),
            tr("vnc_dlg_del_msg", name=conn.display_name),
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
        self._form_title.setText(tr("vnc_form_title_new"))
        self._populate_group_combo(preselect)
        self._f_name.clear(); self._f_host.clear()
        self._f_port.setValue(5900); self._f_user.clear(); self._f_notes.clear()
        self._right.setCurrentIndex(_FORM)
        self._f_host.setFocus()

    def _on_save(self) -> None:
        host = self._f_host.text().strip()
        if not host:
            QMessageBox.warning(self, tr("vnc_dlg_req_title"), tr("vnc_dlg_req_msg"))
            self._f_host.setFocus()
            return
        updated = VncConnection(
            id       = self._editing_id or str(uuid.uuid4()),
            name     = self._f_name.text().strip() or host,
            host     = host,
            port     = self._f_port.value(),
            username = self._f_user.text().strip(),
            notes    = self._f_notes.toPlainText().strip(),
            group_id = self._f_group.currentData() or "",
        )
        if self._editing_id:
            self._connections = [updated if c.id == self._editing_id else c for c in self._connections]
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
        name, ok = QInputDialog.getText(self, tr("vnc_dlg_new_grp_title"), tr("vnc_dlg_new_grp_prompt"))
        if not ok or not name.strip():
            return
        top_groups = [g for g in self._groups if not g.parent_id]
        parent_id = ""
        if top_groups:
            choices = [tr("vnc_root_level")] + [g.name for g in top_groups]
            choice, ok2 = QInputDialog.getItem(
                self, tr("vnc_dlg_parent_title"), tr("vnc_dlg_parent_prompt"), choices, 0, False
            )
            if not ok2:
                return
            if choice != choices[0]:
                parent_id = top_groups[choices.index(choice) - 1].id
        self._groups.append(VncGroup(name=name.strip(), parent_id=parent_id))
        self._store.save(self._groups, self._connections)
        self._refresh_list()

    def _new_subgroup(self, parent_group_id: str) -> None:
        parent = next((g for g in self._groups if g.id == parent_group_id), None)
        if parent is None:
            return
        name, ok = QInputDialog.getText(
            self, tr("vnc_dlg_new_sub_title"),
            tr("vnc_dlg_new_sub_prompt", parent=parent.name)
        )
        if not ok or not name.strip():
            return
        self._groups.append(VncGroup(name=name.strip(), parent_id=parent_group_id))
        self._store.save(self._groups, self._connections)
        self._refresh_list()

    def _rename_group(self, group_id: str) -> None:
        grp = next((g for g in self._groups if g.id == group_id), None)
        if grp is None:
            return
        name, ok = QInputDialog.getText(
            self, tr("vnc_dlg_rename_title"), tr("vnc_dlg_rename_prompt"), text=grp.name
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
            self, tr("vnc_dlg_del_grp_title"),
            tr("vnc_dlg_del_grp_msg", name=grp.name),
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

    # ── VNC launch ─────────────────────────────────────────────────────────

    def _launch_vnc(self, conn: VncConnection) -> None:
        binary = find_vncviewer()
        if binary is None:
            QMessageBox.warning(self, tr("vnc_missing_title"), tr("vnc_missing_msg"))
            return
        password, ok = QInputDialog.getText(
            self,
            conn.display_name,
            tr("vnc_password_prompt"),
            QLineEdit.EchoMode.Password,
        )
        if not ok:
            return
        try:
            proc = subprocess.Popen(
                build_vnc_args(conn, binary),
                stdin=subprocess.PIPE,
                start_new_session=True,
                close_fds=True,
            )
            proc.stdin.write(password.encode() + b'\n')
            proc.stdin.close()
        except Exception as exc:
            QMessageBox.critical(self, "VNC", str(exc))
```

- [ ] **Step 2: Verify syntax**

```bash
cd /home/luust/claude-projects/nmlinux && python3 -c "from nmlinux.pages.vnc import VncPage; print('OK')"
```
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
cd /home/luust/claude-projects/nmlinux
git add nmlinux/pages/vnc.py
git commit -m "feat(vnc): add pages/vnc.py — VNC connection manager UI"
```

---

## Task 4: `window.py` — sidebar integration

**Files:**
- Modify: `nmlinux/window.py`

- [ ] **Step 1: Add import** (after `from nmlinux.pages.rdp import RdpPage`):

```python
from nmlinux.pages.vnc import VncPage
```

- [ ] **Step 2: Add `_TOOLS` entry** (after the Remote Desktop entry):

```python
    (
        ("computer", "video-display", "network-workgroup"),
        "VNC", VncPage,
        "Gère les profils de connexion VNC\net lance vncviewer vers des machines macOS, Linux ou Windows.",
    ),
```

- [ ] **Step 3: Verify import**

```bash
cd /home/luust/claude-projects/nmlinux && python3 -c "from nmlinux.window import MainWindow; print('OK')"
```
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
cd /home/luust/claude-projects/nmlinux
git add nmlinux/window.py
git commit -m "feat(vnc): wire VNC module into sidebar"
```

---

## Task 5: Version bump v1.2.9 + push

**Files:**
- Modify: `pyproject.toml`
- Modify: `README.md`

- [ ] **Step 1: Bump version in `pyproject.toml`**

Change:
```toml
version = "1.2.8"
```
To:
```toml
version = "1.2.9"
```

- [ ] **Step 2: Update README.md title and changelog**

Change `# NMLinux · v1.2.8` → `# NMLinux · v1.2.9`

Add above `### v1.2.8`:

```markdown
### v1.2.9 — 2026-05-30

- **VNC** — new module for managing VNC connection profiles; groups/subgroups like SSH and RDP; launches `vncviewer` (TigerVNC) via `-autopass` stdin; username field for macOS ARD compatibility; password prompted at connect time, never stored; detects missing `vncviewer` with distro-specific install instructions
```

- [ ] **Step 3: Final import check**

```bash
cd /home/luust/claude-projects/nmlinux && python3 -c "from nmlinux.window import MainWindow; print('OK')"
```
Expected: `OK`

- [ ] **Step 4: Commit and push**

```bash
cd /home/luust/claude-projects/nmlinux
git add pyproject.toml README.md
git commit -m "chore: bump to v1.2.9 — add VNC module"
git push origin main
```
