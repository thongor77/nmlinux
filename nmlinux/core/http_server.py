"""Lightweight HTTP file server — GET (serve) + POST/PUT (receive).

No Qt dependency. Use make_handler() to get a handler class for HTTPServer.
"""

from __future__ import annotations

import socket
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from typing import Callable

LogCallback = Callable[[str, str, str, int, str], None]
# args: direction("↓"/"↑"), filename, client_ip, nbytes, status


def make_handler(root: Path, on_log: LogCallback) -> type:
    """Return a BaseHTTPRequestHandler subclass bound to root and on_log."""

    class _Handler(BaseHTTPRequestHandler):

        def log_message(self, fmt, *args) -> None:  # suppress default stderr output
            pass

        def do_GET(self) -> None:
            filename = self.path.lstrip("/") or "index"
            target = root / filename
            if not target.exists() or not target.is_file():
                self.send_error(404)
                on_log("↓", filename, self.client_address[0], 0, "404")
                return
            data = target.read_bytes()
            self.send_response(200)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            on_log("↓", filename, self.client_address[0], len(data), "OK")

        def do_POST(self) -> None:
            self._receive()

        def do_PUT(self) -> None:
            self._receive()

        def _receive(self) -> None:
            filename = self.path.lstrip("/") or "upload"
            length = int(self.headers.get("Content-Length", 0))
            data = self.rfile.read(length) if length > 0 else b""
            target = root / filename
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            self.send_response(200)
            self.send_header("Content-Length", "0")
            self.end_headers()
            on_log("↑", filename, self.client_address[0], len(data), "OK")

    return _Handler


def get_local_ips() -> list[str]:
    """Return non-loopback IPv4 addresses for the current machine."""
    ips: list[str] = []
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            ips.append(s.getsockname()[0])
    except OSError:
        pass

    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ip = info[4][0]
            if not ip.startswith("127.") and ip not in ips:
                ips.append(ip)
    except OSError:
        pass

    return ips if ips else ["127.0.0.1"]
