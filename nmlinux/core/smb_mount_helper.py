"""Standalone CIFS mount helper — launched via pkexec by core.smb_mount.

Runs entirely as root (via pkexec) so both the default mount attempt and
the older-dialect retry happen under a single authentication prompt,
instead of asking for the password once per attempt.
"""

from __future__ import annotations

import argparse
import subprocess
import sys


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="NMLinux CIFS mount helper")
    p.add_argument("--target", required=True)
    p.add_argument("--mountpoint", required=True)
    p.add_argument("--credentials", required=True)
    return p.parse_args(argv)


def try_mount(target: str, mountpoint: str, opts: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["mount", "-t", "cifs", "-o", opts, target, mountpoint],
        capture_output=True, text=True,
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    proc = try_mount(args.target, args.mountpoint, f"credentials={args.credentials}")
    # errno 95 (ENOTSUPP) is mount.cifs's own signal that the server doesn't
    # support the default dialect negotiation — common with older NAS units.
    if proc.returncode != 0 and 'mount error(95)' in (proc.stderr or proc.stdout):
        proc = try_mount(
            args.target, args.mountpoint, f"credentials={args.credentials},vers=2.0",
        )
    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
