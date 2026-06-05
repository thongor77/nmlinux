from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path


# ── Pure functions ─────────────────────────────────────────────────────────

def _parse_keygen_line(line: str) -> dict | None:
    """Parse one line of `ssh-keygen -l -f` output.

    Format: '256 SHA256:xxx comment (ED25519)'
    """
    m = re.match(r"(\d+)\s+(SHA256:\S+)\s+(.*)\s+\((\w+)\)", line.strip())
    if not m:
        return None
    return {
        "bits":        int(m.group(1)),
        "fingerprint": m.group(2),
        "comment":     m.group(3).strip(),
        "type":        m.group(4),
    }


def _scan_keys(ssh_dir: Path) -> list[dict]:
    """Return list of complete key pairs found in ssh_dir.

    Each dict: {file, type, bits, fingerprint, comment, pub_path, priv_path}
    Pairs without a matching private key are silently skipped.
    """
    results = []
    for pub in sorted(ssh_dir.glob("*.pub")):
        priv = pub.with_suffix("")
        if not priv.exists():
            continue
        try:
            proc = subprocess.run(
                ["ssh-keygen", "-l", "-f", str(pub)],
                capture_output=True, text=True, timeout=5,
            )
        except Exception:
            continue
        if proc.returncode != 0:
            continue
        info = _parse_keygen_line(proc.stdout.strip())
        if not info:
            continue
        results.append({
            **info,
            "file":     pub.stem,
            "pub_path": pub,
            "priv_path": priv,
        })
    return results


def _keygen_args(key_type: str, path: Path, comment: str, passphrase: str) -> list[str]:
    """Build the ssh-keygen argument list."""
    args = ["ssh-keygen"]
    if key_type == "ED25519":
        args += ["-t", "ed25519"]
    else:
        args += ["-t", "rsa", "-b", "4096"]
    args += ["-f", str(path), "-C", comment, "-N", passphrase]
    return args
