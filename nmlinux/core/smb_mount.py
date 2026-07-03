"""SMB mount/unmount — pure logic, no Qt dependency."""

from __future__ import annotations

import os
import platform
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

_IS_MACOS = platform.system() == 'Darwin'


def _sanitize(name: str) -> str:
    """Keep filesystem-safe characters only, collapse everything else to '_'."""
    return re.sub(r'[^A-Za-z0-9._-]', '_', name) or '_'


def mount_point_for(host: str, share: str, base_dir: Path | None = None) -> Path:
    """~/mnt/<host>_<share> by default. Host is included to avoid collisions
    when two different hosts expose a share with the same name."""
    base = base_dir if base_dir is not None else (Path.home() / 'mnt')
    return base / f"{_sanitize(host)}_{_sanitize(share)}"


def is_mounted(path: Path) -> bool:
    return os.path.ismount(path)


def has_mount_cifs() -> bool:
    """mount_smbfs is built into macOS; mount.cifs (cifs-utils) is optional
    on Linux and must be checked explicitly."""
    if _IS_MACOS:
        return True
    return shutil.which('mount.cifs') is not None


def mount(host: str, share: str, user: str, password: str) -> tuple[bool, str]:
    if not has_mount_cifs():
        return False, "MOUNT_CIFS_NOT_FOUND"

    mountpoint = mount_point_for(host, share)
    try:
        mountpoint.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        return False, str(exc)

    if _IS_MACOS:
        return _mount_macos(host, share, user, password, mountpoint)
    return _mount_linux(host, share, user, password, mountpoint)


def unmount(path: Path) -> tuple[bool, str]:
    cmd = ["umount", str(path)] if _IS_MACOS else ["pkexec", "umount", str(path)]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    except FileNotFoundError:
        return False, "UMOUNT_NOT_FOUND"
    except subprocess.TimeoutExpired:
        return False, "Timeout"

    if proc.returncode != 0:
        return False, (proc.stderr or proc.stdout).strip()[:200]

    try:
        path.rmdir()
    except OSError:
        pass
    return True, ""


def _mount_linux(
    host: str, share: str, user: str, password: str, mountpoint: Path,
) -> tuple[bool, str]:
    fd, cred_path = tempfile.mkstemp(prefix='nmlinux_smb_')
    try:
        os.chmod(cred_path, 0o600)
        with os.fdopen(fd, 'w') as f:
            f.write(f"username={user}\npassword={password}\n")

        ok, err = _run_mount_cifs(host, share, cred_path, mountpoint)
        # errno 95 (ENOTSUPP) is mount.cifs's own signal that the server
        # doesn't support the default dialect negotiation — common with
        # older NAS units. Retry once with an older, widely-supported one.
        if not ok and 'mount error(95)' in err:
            ok, err = _run_mount_cifs(host, share, cred_path, mountpoint, vers='2.0')
    finally:
        os.unlink(cred_path)

    return ok, err


def _run_mount_cifs(
    host: str, share: str, cred_path: str, mountpoint: Path, vers: str | None = None,
) -> tuple[bool, str]:
    opts = f"credentials={cred_path}"
    if vers:
        opts += f",vers={vers}"
    cmd = ["pkexec", "mount", "-t", "cifs", "-o", opts, f"//{host}/{share}", str(mountpoint)]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    except FileNotFoundError:
        return False, "PKEXEC_NOT_FOUND"
    except subprocess.TimeoutExpired:
        return False, "Timeout"

    # pkexec itself uses 126 (dialog dismissed) / 127 (authorization/other
    # error) — any other non-zero code is mount.cifs's own exit status.
    if proc.returncode in (126, 127):
        return False, "PKEXEC_AUTH_FAILED"
    if proc.returncode != 0:
        return False, (proc.stderr or proc.stdout).strip()[:200]
    return True, ""


def _mount_macos(
    host: str, share: str, user: str, password: str, mountpoint: Path,
) -> tuple[bool, str]:
    target = f"//{user}:{password}@{host}/{share}" if user else f"//{host}/{share}"
    cmd = ["mount_smbfs", target, str(mountpoint)]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    except FileNotFoundError:
        return False, "MOUNT_SMBFS_NOT_FOUND"
    except subprocess.TimeoutExpired:
        return False, "Timeout"

    if proc.returncode != 0:
        return False, (proc.stderr or proc.stdout).strip()[:200]
    return True, ""
