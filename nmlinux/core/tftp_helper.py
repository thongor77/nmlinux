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
                    nbytes: int, status: str) -> str:
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    return f"TFTP|{ts}|{direction}|{filename}|{client_ip}|{nbytes}|{status}"


# ── tftpy log forwarding ──────────────────────────────────────────────────────

_RE_DOWNLOAD  = re.compile(r"completed download of (\d+) bytes", re.I)
_RE_UPLOAD    = re.compile(r"completed upload of (\d+) bytes", re.I)
_RE_FILENAME  = re.compile(r"filename\s*=\s*(\S+)", re.I)
_RE_PEER      = re.compile(r"peer\s*=\s*([\d.]+)", re.I)


class _TftpForwarder(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self._filename = "unknown"
        self._client   = "unknown"

    def emit(self, record: logging.LogRecord) -> None:
        msg = record.getMessage()

        m = _RE_FILENAME.search(msg)
        if m:
            self._filename = m.group(1)

        m = _RE_PEER.search(msg)
        if m:
            self._client = m.group(1)

        m = _RE_DOWNLOAD.search(msg)
        if m:
            print(format_log_line("↓", self._filename, self._client,
                                  int(m.group(1)), "OK"), flush=True)
            return

        m = _RE_UPLOAD.search(msg)
        if m:
            print(format_log_line("↑", self._filename, self._client,
                                  int(m.group(1)), "OK"), flush=True)


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

    server = tftpy.TftpServer(args.root)

    try:
        print("READY", flush=True)
        server.listen("0.0.0.0", args.port)
    except PermissionError:
        print("EPERM", flush=True)
        sys.exit(1)
    except OSError as exc:
        print(f"ERROR|{exc}", flush=True)
        sys.exit(2)


if __name__ == "__main__":
    main()
