"""SMB mount/unmount — pure logic, no Qt dependency."""

from __future__ import annotations

import os
import platform
import re
import shutil
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
