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

        def _safe_target(self, filename: str) -> "Path | None":
            """Return resolved path if it is safely within root, else None."""
            try:
                target = (root / filename).resolve()
                target.relative_to(root.resolve())  # raises ValueError if outside
                return target
            except ValueError:
                return None

        def do_GET(self) -> None:
            filename = self.path.lstrip("/") or "index"
            target = self._safe_target(filename)
            if target is None:
                self.send_error(403)
                on_log("↓", filename, self.client_address[0], 0, "403")
                return
            if not target.exists() or not target.is_file():
                self.send_error(404)
                on_log("↓", filename, self.client_address[0], 0, "404")
                return
            try:
                data = target.read_bytes()
            except OSError as exc:
                self.send_error(500)
                on_log("↓", filename, self.client_address[0], 0, f"ERROR: {exc.__class__.__name__}")
                return
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
            target = self._safe_target(filename)
            if target is None:
                self.send_error(403)
                on_log("↑", filename, self.client_address[0], 0, "403")
                return
            length = int(self.headers.get("Content-Length", 0))
            try:
                data = self.rfile.read(length) if length > 0 else b""
            except OSError as exc:
                self.send_error(500)
                on_log("↑", filename, self.client_address[0], 0, f"ERROR: {exc.__class__.__name__}")
                return
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
            except OSError as exc:
                self.send_error(500)
                on_log("↑", filename, self.client_address[0], 0, f"ERROR: {exc.__class__.__name__}")
                return
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
