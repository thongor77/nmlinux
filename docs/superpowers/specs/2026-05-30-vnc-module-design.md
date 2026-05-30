# VNC Module Design — NMLinux

**Date:** 2026-05-30
**Status:** Approved

---

## Summary

Add a VNC module to NMLinux that manages connection profiles and launches `vncviewer` (TigerVNC) as an external process. Password is prompted in nmlinux and passed to vncviewer via stdin (`-autopass`). No window embedding — vncviewer opens in its own OS window.

---

## Architecture

### New files

| File | Role |
|------|------|
| `nmlinux/core/vnc.py` | Pure logic: models, persistence, arg builder, binary detection |
| `nmlinux/pages/vnc.py` | Qt UI: VncPage |

### Modified files

| File | Change |
|------|--------|
| `nmlinux/window.py` | Add "VNC" sidebar entry after Remote Desktop |
| `nmlinux/core/i18n.py` | Add `vnc_*` and `nav_vnc` keys (fr/en/es/de) |

No new dependencies. `subprocess` (stdlib), `QInputDialog` (PySide6) are sufficient.

---

## Data Model (`core/vnc.py`)

Mirrors `core/rdp.py`.

```python
@dataclass
class VncGroup:
    id:        str   # uuid
    name:      str
    parent_id: str   # "" = top-level

@dataclass
class VncConnection:
    id:       str   # uuid
    name:     str
    host:     str
    port:     int   = 5900
    username: str   = ""   # optional — omitted if empty
    notes:    str   = ""
    group_id: str   = ""
```

**Persistence:** `~/.local/share/nmlinux/vnc_connections.json`

**Password:** never persisted. Prompted at connect time, written to vncviewer stdin, then discarded.

---

## `find_vncviewer() -> str | None`

Tries candidates in order:
1. `vncviewer` — TigerVNC on most distros (Arch package: `tigervnc`)
2. `tigervnc` — alternative name on some distros

---

## `build_vnc_args(conn, binary) -> list[str]`

```
vncviewer -autopass [-username <username>] <host>::<port>
```

- `-autopass` reads password from stdin (one line)
- `-username` omitted if `conn.username` is empty (standard VNC auth)
- Port format: `host::port` (double colon = explicit port in TigerVNC)

---

## UI Layout (`pages/vnc.py`)

Splitter horizontal, ratio 220 / 700. Calque exact de `pages/rdp.py`.

### Left panel
- Buttons: `[+ Connexion]` `[+ Groupe]`
- `QTreeWidget` — groups as folders, connections as leaves
- Context menu: Connect / Edit / Delete (connections), Rename / Add subgroup / Delete (groups)

### Right panel — `QStackedWidget` with 3 states

| State | Content |
|-------|---------|
| `EMPTY` (0) | Invite message |
| `DETAIL` (1) | Read-only fields: Host, Port, Username, Notes + `[Modifier]` `[Connecter]` |
| `FORM` (2) | Editable form: Name, Group, Host*, Port, Username, Notes + `[Enregistrer]` `[Annuler]` |

### Connect flow

1. `find_vncviewer()` — if absent: `QMessageBox` with distro-aware install hint
2. `QInputDialog.getText()` — password (hidden)
3. User cancels → abort
4. `subprocess.Popen(build_vnc_args(conn, binary), stdin=PIPE, start_new_session=True, close_fds=True)`
5. Write `password + '\n'` to stdin, close stdin
6. vncviewer runs independently of nmlinux

---

## Sidebar Integration

Entry added to `window.py` after Remote Desktop:

```python
("computer", "network-workgroup", "video-display"),
"VNC", VncPage,
"Gère les profils de connexion VNC\net lance vncviewer vers des machines macOS, Linux ou Windows.",
```

---

## i18n Keys

Prefix `vnc_` — added to fr/en/es/de. Same set as RDP minus domain/resolution/fullscreen keys:

```
nav_vnc
vnc_new_conn_btn, vnc_new_grp_btn, vnc_empty_state
vnc_det_lbl_host, vnc_det_lbl_port, vnc_det_lbl_user, vnc_det_lbl_notes
vnc_connect_btn, vnc_edit_btn, vnc_delete_btn
vnc_form_lbl_name, vnc_form_lbl_group, vnc_form_lbl_host
vnc_form_lbl_port, vnc_form_lbl_user, vnc_form_lbl_notes
vnc_form_name_ph, vnc_form_user_ph
vnc_save_btn, vnc_cancel_btn
vnc_form_title_new, vnc_form_title_edit
vnc_ctx_connect, vnc_ctx_edit, vnc_ctx_delete
vnc_ctx_rename_grp, vnc_ctx_add_sub, vnc_ctx_delete_grp
vnc_no_group, vnc_root_level
vnc_dlg_new_grp_title, vnc_dlg_new_grp_prompt
vnc_dlg_parent_title, vnc_dlg_parent_prompt
vnc_dlg_new_sub_title, vnc_dlg_new_sub_prompt
vnc_dlg_rename_title, vnc_dlg_rename_prompt
vnc_dlg_req_title, vnc_dlg_req_msg
vnc_dlg_del_title, vnc_dlg_del_msg
vnc_dlg_del_grp_title, vnc_dlg_del_grp_msg
vnc_password_prompt
vnc_missing_title, vnc_missing_msg
```

---

## Error Handling

| Situation | Response |
|-----------|----------|
| `vncviewer` absent | `QMessageBox.warning` avec commande d'installation |
| Hôte vide au save | Validation inline, focus sur le champ |
| `Popen` échec | `QMessageBox.critical` avec message d'erreur |

---

## Out of Scope (v1)

- Stockage sécurisé du mot de passe (keyring)
- Chiffrement VNC / TLS
- Redirection de fichiers ou clipboard
- Intégration visuelle (incompatible Wayland)
