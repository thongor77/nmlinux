# RDP Module Design — NMLinux

**Date:** 2026-05-30
**Status:** Approved

---

## Summary

Add a Remote Desktop Protocol (RDP) module to NMLinux that manages Windows connection profiles and launches `xfreerdp` as an external process. No window embedding — xfreerdp opens in its own OS window.

---

## Architecture

### New files

| File | Role |
|------|------|
| `nmlinux/core/rdp.py` | Pure logic: models, persistence, arg builder |
| `nmlinux/pages/rdp.py` | Qt UI: RdpPage |

### Modified files

| File | Change |
|------|--------|
| `nmlinux/window.py` | Add "Remote Desktop" sidebar entry after SSH |
| `nmlinux/core/i18n.py` | Add `rdp_*` and `nav_rdp` keys (fr/en/es) |

No new dependencies. `QProcess` (PySide6), `shutil` (stdlib) are sufficient.

---

## Data Model (`core/rdp.py`)

Mirrors `core/ssh.py` exactly.

```python
@dataclass
class RdpGroup:
    id:        str   # uuid
    name:      str
    parent_id: str   # "" = top-level

@dataclass
class RdpConnection:
    id:         str   # uuid
    name:       str
    host:       str
    port:       int   = 3389
    username:   str   = ""
    domain:     str   = ""
    resolution: str   = "1920x1080"
    fullscreen: bool  = False
    notes:      str   = ""
    group_id:   str   = ""
```

**Persistence:** `~/.local/share/nmlinux/rdp_connections.json` — same structure as `ssh_connections.json` (groups + connections lists).

**Password:** never persisted. Passed to `build_rdp_args()` at connection time only.

---

## `build_rdp_args(conn, password) -> list[str]`

```
xfreerdp
  /v:<host>:<port>
  /u:<username>
  /p:<password>
  /d:<domain>          (omitted if empty)
  /size:<resolution>   (omitted if fullscreen)
  /f                   (only if fullscreen=True)
  /dynamic-resolution
  /cert:ignore
```

---

## UI Layout (`pages/rdp.py`)

Splitter horizontal, ratio 220 / 700 (identical to SSH).

### Left panel
- Buttons: `[+ Connexion]` `[+ Groupe]`
- `QTreeWidget` (header hidden) — groups as folders, connections as leaves
- Context menu on right-click: Edit / Delete (for both groups and connections)

### Right panel — `QStackedWidget` with 3 states

| State | Trigger | Content |
|-------|---------|---------|
| `EMPTY` (0) | Nothing selected | Invite message |
| `DETAIL` (1) | Connection selected | Read-only field display + `[Modifier]` `[Connecter]` buttons |
| `FORM` (2) | New or Edit | Editable form + `[Sauvegarder]` `[Annuler]` buttons |

### Connect flow
1. User clicks **Connecter** in DETAIL state.
2. `shutil.which("xfreerdp")` — if absent: `QMessageBox` with distro-aware install hint (`pacman -S freerdp` / `apt install freerdp2-x11`).
3. `QInputDialog.getText()` prompts for password (echo mode hidden).
4. `QProcess` launched in detached mode with `build_rdp_args(conn, password)`.
5. Password reference dropped immediately after launch.

---

## Sidebar Integration

Entry added to `window.py` after SSH:

```python
("remote-desktop", tr("nav_rdp"), "monitor")
```

Icon: `monitor.svg` from existing Lucide bundle (`assets/icons/`).

---

## i18n Keys

Prefix `rdp_` — added to fr/en/es in `core/i18n.py`:

```
nav_rdp
rdp_new_conn_btn
rdp_new_grp_btn
rdp_host
rdp_port
rdp_username
rdp_domain
rdp_resolution
rdp_fullscreen
rdp_notes
rdp_connect_btn
rdp_edit_btn
rdp_save_btn
rdp_cancel_btn
rdp_password_prompt
rdp_missing_xfreerdp
rdp_missing_xfreerdp_detail
```

---

## Error Handling

| Situation | Response |
|-----------|----------|
| `xfreerdp` absent du PATH | `QMessageBox.warning` avec commande d'installation |
| Hôte vide au moment de sauvegarder | Validation inline, champ surligné |
| `QProcess` échec au lancement | `QMessageBox.critical` avec code d'erreur |

---

## Out of Scope (v1)

- Stockage sécurisé du mot de passe (keyring) — ajout futur si demande
- VNC / macOS — module séparé ultérieur
- Intégration visuelle de la fenêtre xfreerdp (incompatible Wayland)
- Redirection de dossiers (`/drive:`) — option future dans le formulaire avancé
