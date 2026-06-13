"""SSH connection profiles — pure logic, no Qt dependency."""

from __future__ import annotations

import json
import shutil
import subprocess
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path


# ── Model ──────────────────────────────────────────────────────────────────


@dataclass
class SshGroup:
    id:        str = field(default_factory=lambda: str(uuid.uuid4()))
    name:      str = ""
    parent_id: str = ""   # "" = top-level group


@dataclass
class SshConnection:
    id:            str  = field(default_factory=lambda: str(uuid.uuid4()))
    name:          str  = ""
    host:          str  = ""
    port:          int  = 22
    username:      str  = ""
    key_path:      str  = ""
    notes:         str  = ""
    group_id:      str  = ""    # "" = no group (root level)
    forward_agent: bool = False

    @property
    def display_name(self) -> str:
        return self.name if self.name else self.host

    @property
    def subtitle(self) -> str:
        target = f"{self.username}@{self.host}" if self.username else self.host
        return f"{target}:{self.port}" if self.port != 22 else target

    @property
    def ssh_command(self) -> str:
        return " ".join(build_ssh_args(self))


# ── Persistence ────────────────────────────────────────────────────────────


class SshStore:
    def __init__(self, path: Path | None = None) -> None:
        if path is None:
            data_dir = Path.home() / ".local" / "share" / "nmlinux"
            data_dir.mkdir(parents=True, exist_ok=True)
            path = data_dir / "ssh_connections.json"
        self._path = path

    def load(self) -> tuple[list[SshGroup], list[SshConnection]]:
        if not self._path.exists():
            return [], []
        try:
            raw = json.loads(self._path.read_text())
            conn_fields  = SshConnection.__dataclass_fields__
            group_fields = SshGroup.__dataclass_fields__

            # Legacy: flat list of connections (v1 format)
            if isinstance(raw, list):
                conns = [
                    SshConnection(**{k: v for k, v in d.items() if k in conn_fields})
                    for d in raw
                ]
                return [], conns

            # v2 format
            groups = [
                SshGroup(**{k: v for k, v in g.items() if k in group_fields})
                for g in raw.get('groups', [])
            ]
            conns = [
                SshConnection(**{k: v for k, v in c.items() if k in conn_fields})
                for c in raw.get('connections', [])
            ]
            return groups, conns
        except Exception:
            return [], []

    def save(self, groups: list[SshGroup], connections: list[SshConnection]) -> None:
        data = {
            'version': 2,
            'groups': [asdict(g) for g in groups],
            'connections': [asdict(c) for c in connections],
        }
        self._path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False)
        )


# ── SSH args builder ───────────────────────────────────────────────────────


def build_ssh_args(conn: SshConnection) -> list[str]:
    args = ["ssh"]
    if conn.forward_agent:
        args.append("-A")
    if conn.key_path:
        args += ["-i", conn.key_path]
    if conn.port != 22:
        args += ["-p", str(conn.port)]
    target = f"{conn.username}@{conn.host}" if conn.username else conn.host
    args.append(target)
    return args


# ── Terminal launcher ──────────────────────────────────────────────────────

_TERMINALS: list[tuple[str, object]] = [
    ("konsole",        lambda a: ["konsole",        "-e",  *a]),
    ("alacritty",      lambda a: ["alacritty",      "-e",  *a]),
    ("kitty",          lambda a: ["kitty",                 *a]),
    ("wezterm",        lambda a: ["wezterm", "start", "--", *a]),
    ("foot",           lambda a: ["foot",                  *a]),
    ("xfce4-terminal", lambda a: ["xfce4-terminal", "-x",  *a]),
    ("gnome-terminal", lambda a: ["gnome-terminal", "--",  *a]),
    ("xterm",          lambda a: ["xterm",          "-e",  *a]),
]


def _find_terminal():
    for name, builder in _TERMINALS:
        if shutil.which(name):
            return builder
    return None


def launch(conn: SshConnection) -> tuple[bool, str]:
    builder = _find_terminal()
    if builder is None:
        return False, "Aucun émulateur de terminal trouvé."
    cmd = builder(build_ssh_args(conn))
    try:
        subprocess.Popen(cmd, start_new_session=True)
        return True, ""
    except FileNotFoundError as exc:
        return False, str(exc)
