"""RDP connection profiles — pure logic, no Qt dependency."""

from __future__ import annotations

import json
import platform
import shutil
import subprocess
import uuid

_IS_MACOS = platform.system() == 'Darwin'
from dataclasses import asdict, dataclass, field
from pathlib import Path

# freerdp 3.x (Arch) ships xfreerdp3; freerdp 2.x (Debian/Ubuntu) ships xfreerdp
_XFREERDP_CANDIDATES = ["xfreerdp3", "xfreerdp"]


def find_xfreerdp() -> str | None:
    for name in _XFREERDP_CANDIDATES:
        if shutil.which(name):
            return name
    return None


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


def build_rdp_args(conn: RdpConnection, password: str, binary: str = "xfreerdp") -> list[str]:
    args = [
        binary,
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


def launch_rdp_macos(conn: RdpConnection) -> tuple[bool, str]:
    """Open RDP via URL scheme — works with Microsoft Remote Desktop (App Store)."""
    url = f"rdp://full%20address=s:{conn.host}:{conn.port}"
    if conn.username:
        url += f"&username=s:{conn.username}"
    if conn.domain:
        url += f"&domain=s:{conn.domain}"
    try:
        subprocess.Popen(["open", url], start_new_session=True)
        return True, ""
    except Exception as exc:
        return False, str(exc)
