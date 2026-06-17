"""Standalone TFTP server — launched by FileTransferPage via QProcess.

Outputs one structured line per event to stdout:
  READY
  EPERM
  ERROR|<message>
  TFTP|<HH:MM:SS>|<direction>|<filename>|<client_ip>|<bytes>|<status>
"""

from __future__ import annotations

import argparse
import datetime
import logging
import re
import sys


# ── Public helpers (tested) ───────────────────────────────────────────────────

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="NMLinux TFTP helper")
    p.add_argument("--port", type=int, default=69)
    p.add_argument("--root", required=True)
    return p.parse_args(argv)


def format_log_line(direction: str, filename: str, client_ip: str,
                    nbytes: int, status: str,
                    ts: str | None = None) -> str:
    if ts is None:
        ts = datetime.datetime.now().strftime("%H:%M:%S")
    return f"TFTP|{ts}|{direction}|{filename}|{client_ip}|{nbytes}|{status}"


# ── tftpy log forwarding ──────────────────────────────────────────────────────

# Matches: "Transferred 4096 bytes in 0.01 seconds"
_RE_TRANSFERRED   = re.compile(r"Transferred (\d+) bytes in", re.I)
# Matches: "Requested filename is startup-config"
# Matches: "    filename -> startup-config"
_RE_FILENAME      = re.compile(
    r"(?:Requested filename is|filename\s*->)\s*(\S+)", re.I
)
# Matches: "Opening file /root/startup-config for reading"  (client GET → server reads)
_RE_OPENING_READ  = re.compile(r"Opening file .+ for reading", re.I)
# Matches: "Opening file /root/startup-config for writing"  (client PUT → server writes)
_RE_OPENING_WRITE = re.compile(r"Opening file .+ for writing", re.I)
# Matches session completion line: "Session 192.168.1.1:12345 complete"
_RE_SESSION       = re.compile(r"Session ([\d.]+):\d+ complete", re.I)


class _TftpForwarder(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self._filename  = "unknown"
        self._client    = "unknown"
        self._direction = "↓"   # default: client download (server reads file)

    def emit(self, record: logging.LogRecord) -> None:
        msg = record.getMessage()

        m = _RE_FILENAME.search(msg)
        if m:
            self._filename = m.group(1)
            return

        if _RE_OPENING_READ.search(msg):
            self._direction = "↓"   # server opens for reading → client downloads
            return

        if _RE_OPENING_WRITE.search(msg):
            self._direction = "↑"   # server opens for writing → client uploads
            return

        m = _RE_SESSION.search(msg)
        if m:
            self._client = m.group(1)
            return

        m = _RE_TRANSFERRED.search(msg)
        if m:
            print(format_log_line(self._direction, self._filename,
                                  self._client, int(m.group(1)), "OK"),
                  flush=True)


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    args = parse_args()

    try:
        import tftpy
    except ImportError:
        print("ERROR|tftpy not installed. Run: pip install tftpy", flush=True)
        sys.exit(3)

    handler = _TftpForwarder()
    handler.setLevel(logging.DEBUG)
    tftpy_log = logging.getLogger("tftpy")
    tftpy_log.setLevel(logging.DEBUG)
    tftpy_log.addHandler(handler)

    try:
        server = tftpy.TftpServer(args.root)
        print("READY", flush=True)
        server.listen("0.0.0.0", args.port)
    except PermissionError:
        print("EPERM", flush=True)
        sys.exit(1)
    except OSError as exc:
        print(f"ERROR|{exc}", flush=True)
        sys.exit(2)
    except Exception as exc:
        print(f"ERROR|{exc}", flush=True)
        sys.exit(2)


if __name__ == "__main__":
    main()
