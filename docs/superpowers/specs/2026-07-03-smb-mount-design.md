# SMB Mount — Design Spec
Date: 2026-07-03

## Overview

Right-click a share row on the SMB/NFS page's SMB tab and mount it at a stable,
predictable local path — usable from the terminal and any other app, not a
transient Finder/Dolphin browse view. Unmount the same way. nmlinux implements
this itself (no dependency on the separate `netmnt` project, which is
Linux/KDE/Dolphin-specific and uses a different integration point — a file
manager service menu, not an in-app action).

## Constraints

- SMB/CIFS only for this iteration — NFS mounting is out of scope
- Session-only mounts — no fstab entries, no systemd `.mount` units, no
  persistence across reboot
- Mount point: fixed convention `~/mnt/<host>_<share-name>`, created
  automatically, no user prompt for the path (host prefix avoids collisions
  when two different hosts happen to expose a share with the same name,
  e.g. two NAS boxes both sharing a folder called `public`)
- Trigger: right-click on a row in the SMB tab's table (`Monter` / `Démonter`
  depending on current state) — not a toolbar button or extra table column
- Credentials: reuse the existing `_user_edit` / `_pass_edit` fields already
  present in the SMB tab (used today for the share-listing scan)

## Architecture

### `nmlinux/core/smb_mount.py` (new, pure logic, no Qt — same convention as `core/rdp.py`)

```python
def mount_point_for(host: str, share: str) -> Path:
    """~/mnt/<host>_<share>, sanitized for filesystem-safe characters."""

def is_mounted(path: Path) -> bool:
    """os.path.ismount(path)"""

def mount(host: str, share: str, user: str, password: str) -> tuple[bool, str]:
    """Returns (success, error_message). Builds mount point, writes a
    restricted-permission (0600) credentials file, runs the platform mount
    command, deletes the credentials file immediately after (success or
    failure)."""

def unmount(path: Path) -> tuple[bool, str]:
    """Runs the platform unmount command, removes the now-empty mount point
    directory on success."""
```

Platform commands:

- **Linux**: credentials file with `username=<user>\npassword=<password>\n`
  (mode 0600, `tempfile.mkstemp`), then
  `pkexec mount -t cifs -o credentials=<tmpfile> //host/share <mountpoint>`.
  Password never appears in argv/`ps` (unlike the existing share-listing scan,
  which already passes `-U user%pass` to `smbclient` — a pre-existing,
  lower-risk pattern for a short-lived scan that this feature does not need
  to replicate).
- **macOS**: `mount_smbfs //user:pass@host/share <mountpoint>` as the current
  user, no privilege escalation. **To verify on real hardware**: user-owned
  mounts under `$HOME` are not expected to require admin rights, unlike
  writing `/etc/hosts` (which does use `osascript ... with administrator
  privileges` elsewhere in the codebase) — if this assumption is wrong, add
  the same osascript wrapper used in `pages/hosts.py`.

### `nmlinux/pages/smb_nfs.py` (modify)

- Enable custom context menu on `_smb_table`
  (`setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)` +
  `customContextMenuRequested.connect(...)`)
- Menu built per-row: label and action depend on `is_mounted(mount_point_for(share_name))`
- Mount/unmount runs in a `QThread` (`_MountWorker`, mirrors the existing
  `_SmbWorker`/`_NfsWorker` pattern) so the `pkexec` polkit prompt doesn't
  block the UI thread
- On success: status label updated ("Mounted at ~/mnt/<share>" /
  "Unmounted"); no persistent mounted-state tracking beyond re-checking
  `is_mounted()` each time the menu is opened (simplest option — matches
  session-only scope, avoids a state cache that could drift from reality)

## Data Flow

1. User right-clicks a share row → `_MountWorker` state check happens
   synchronously (`os.path.ismount` is cheap, no subprocess needed) to decide
   which menu item to show
2. **Monter**: `_MountWorker(mount, host, share, user, password)` starts →
   `pkexec` prompts for the user's password (Linux) → on success, status
   label shows the mount point
3. **Démonter**: `_MountWorker(unmount, path)` starts → `pkexec umount` →
   mount point directory removed on success

## Files to Create / Modify

| File | Action |
|------|--------|
| `nmlinux/core/smb_mount.py` | Create — mount/unmount/is_mounted logic |
| `nmlinux/pages/smb_nfs.py` | Modify — context menu on `_smb_table`, `_MountWorker` |
| `nmlinux/core/i18n.py` | Modify — add `smb_mount_*` i18n keys, 8 languages |
| `aur/PKGBUILD` | Modify — add `cifs-utils` to `optdepends` |
| `tests/test_smb_mount.py` | Create — unit tests for `core/smb_mount.py` |

## i18n Keys (prefix `smb_mount_`)

All 8 languages: FR, EN, ES, DE, IT, PT, JA, ZH.

```
smb_mount_ctx_mount, smb_mount_ctx_unmount
smb_mount_status_mounted, smb_mount_status_unmounted
smb_mount_err_no_cifs_utils
smb_mount_err_pkexec_fail
smb_mount_err_auth
smb_mount_err_generic
```

## Dependencies

- **Linux**: `cifs-utils` (provides `mount.cifs`) — added to PKGBUILD
  `optdepends`, detected via `shutil.which('mount.cifs')`; clear error +
  install hint if missing, matching the existing tool-detection convention
  (`_which` in `smb_nfs.py`, `find_xfreerdp` in `core/rdp.py`)
- **macOS**: `mount_smbfs` is built-in, no install needed
- `pkexec` — system tool, already present on most Linux desktops (polkit),
  same assumption as `pages/hosts.py` and `pages/file_transfer.py`

## Error Handling

| Scenario | Behaviour |
|----------|-----------|
| `mount.cifs` not found (Linux) | Error message + install hint (`cifs-utils`), no pkexec attempt |
| pkexec cancelled/refused | Error message (matches `fw_err_pkexec_fail` pattern) |
| Wrong credentials | Detected from mount command stderr, shown as `smb_mount_err_auth` |
| Host unreachable / share doesn't exist | Generic error with truncated stderr, `smb_mount_err_generic` |
| Already mounted at that path | Menu shows "Démonter" instead of "Monter" — no error, just the correct action |
| Unmount fails (busy resource) | Error message with stderr, mount point directory left in place |

## Testing

`tests/test_smb_mount.py` — pure logic, `subprocess.run` and `platform.system`
mocked, no real mount attempted (matches `test_rdp_core.py` / `test_vnc_core.py`
approach):

- `mount_point_for()` — path derivation, sanitization of unusual host/share
  names, collision avoidance for same-named shares on different hosts
- `is_mounted()` — wraps `os.path.ismount`, mocked true/false
- `mount()` — command construction per platform, credentials file written
  with 0600 permissions and deleted after (success and failure paths both
  clean up)
- `unmount()` — command construction per platform, mount point directory
  removed only on success

No integration test against a real SMB server — out of scope, matches
existing testing philosophy in this repo.

## Out of Scope

- NFS mounting (SMB only for this iteration)
- Persistent mounts (fstab / systemd `.mount` units) — see `netmnt` if that's
  needed on Linux/KDE
- Credential storage/reuse across sessions (no keychain/KWallet integration)
- Mounting from Dolphin/Finder's own right-click menu (that's `netmnt`'s and
  macOS's native domain, respectively) — this feature is in-app only
