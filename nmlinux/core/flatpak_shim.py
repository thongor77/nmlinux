"""Flatpak sandbox helpers — bridge sandbox-private paths to host-visible ones.

Any path handed to `pkexec` or a `flatpak-spawn --host` command is resolved
in the *host* mount namespace, not the sandbox's. The sandbox's private
/tmp is invisible there, so temp files and in-package helper scripts must
live under XDG_CACHE_HOME instead — Flatpak binds that to a real host
directory (~/.var/app/<id>/cache), identical on both sides.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

IS_FLATPAK = "FLATPAK_ID" in os.environ


def host_visible_tmp_dir() -> Path:
    """Directory usable both inside the sandbox and by host-spawned commands."""
    if not IS_FLATPAK:
        return Path(tempfile.gettempdir())
    base = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    d = base / "nmlinux" / "tmp"
    d.mkdir(parents=True, exist_ok=True)
    return d


def host_visible_path(src: Path) -> Path:
    """Return a path to `src`'s content that a host-spawned process can read.

    Outside Flatpak, `src` (e.g. an in-package helper script) is already
    host-visible. Inside Flatpak, copy it into host_visible_tmp_dir() once
    (refreshed if the packaged copy changed) and return that path instead.
    """
    if not IS_FLATPAK:
        return src
    dest = host_visible_tmp_dir() / src.name
    data = src.read_bytes()
    if not dest.exists() or dest.read_bytes() != data:
        dest.write_bytes(data)
    return dest
