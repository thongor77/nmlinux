"""Lightweight HTTP file server — GET (serve) + POST/PUT (receive).

No Qt dependency. Use make_handler() to get a handler class for HTTPServer.
"""

from __future__ import annotations

import socket
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from typing import Callable
from urllib.parse import quote, unquote

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
            filename = unquote(self.path.lstrip("/"))
            if filename == "":
                target = root.resolve()
            else:
                target = self._safe_target(filename)
                if target is None:
                    self.send_error(403)
                    on_log("↓", filename, self.client_address[0], 0, "403")
                    return

            if target.is_dir():
                self._serve_listing(target)
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
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Content-Disposition",
                             f'attachment; filename="{target.name}"')
            self.end_headers()
            self.wfile.write(data)
            on_log("↓", filename or "/", self.client_address[0], len(data), "OK")

        def _serve_listing(self, directory: Path) -> None:
            url = self.path.rstrip("/") or "/"
            try:
                entries = sorted(directory.iterdir(),
                                 key=lambda p: (not p.is_dir(), p.name.lower()))
            except OSError:
                self.send_error(500)
                return

            rows = []
            if url != "/":
                parent = str(Path(url).parent)
                rows.append(f'<tr><td colspan="2"><a href="{parent}">📁 ..</a></td></tr>')
            for entry in entries:
                icon  = "📁" if entry.is_dir() else "📄"
                href  = quote((url + "/" + entry.name).replace("//", "/"))
                try:
                    size = "—" if entry.is_dir() else f"{entry.stat().st_size:,} B"
                except OSError:
                    size = "?"
                rows.append(
                    f'<tr><td><a href="{href}">{icon} {entry.name}</a></td>'
                    f'<td style="color:#888;padding-left:24px">{size}</td></tr>'
                )

            body = (
                "<!DOCTYPE html><html><head><meta charset='utf-8'>"
                f"<title>NMLinux — {url}</title>"
                "<style>body{font-family:monospace;padding:20px;max-width:800px}"
                "h2{margin-bottom:8px}table{border-collapse:collapse;width:100%}"
                "td{padding:5px 8px;border-bottom:1px solid #e0e0e0}"
                "a{text-decoration:none;color:#1a73e8}a:hover{text-decoration:underline}"
                "</style></head><body>"
                f"<h2>📂 {url}</h2><table>{''.join(rows)}</table></body></html>"
            ).encode("utf-8")

            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            on_log("↓", url, self.client_address[0], len(body), "OK")

        def do_POST(self) -> None:
            self._receive()

        def do_PUT(self) -> None:
            self._receive()

        def _receive(self) -> None:
            filename = unquote(self.path.lstrip("/")) or "upload"
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
