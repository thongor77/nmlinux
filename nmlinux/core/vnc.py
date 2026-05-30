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
