"""Tests for File Transfer server helpers (no Qt, no network)."""
from __future__ import annotations

import sys
import importlib
from pathlib import Path

# ── tftp_helper ───────────────────────────────────────────────────────────────

def _import_helper():
    spec = importlib.util.spec_from_file_location(
        "tftp_helper",
        Path(__file__).parent.parent / "nmlinux" / "core" / "tftp_helper.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_parse_args_defaults():
    helper = _import_helper()
    args = helper.parse_args(["--root", "/tmp/tftp"])
    assert args.port == 69
    assert args.root == "/tmp/tftp"


def test_parse_args_custom_port():
    helper = _import_helper()
    args = helper.parse_args(["--port", "6969", "--root", "/tmp"])
    assert args.port == 6969


def test_format_log_line_download():
    helper = _import_helper()
    line = helper.format_log_line("↓", "startup-config", "192.168.1.1", 4096, "OK")
    parts = line.split("|")
    assert parts[0] == "TFTP"
    assert parts[2] == "↓"
    assert parts[3] == "startup-config"
    assert parts[4] == "192.168.1.1"
    assert parts[5] == "4096"
    assert parts[6] == "OK"


def test_format_log_line_upload():
    helper = _import_helper()
    line = helper.format_log_line("↑", "firmware.bin", "10.0.0.1", 1024, "OK")
    assert "↑" in line
    assert "firmware.bin" in line


def test_format_log_line_injectable_ts():
    helper = _import_helper()
    line = helper.format_log_line("↓", "startup-config", "192.168.1.1", 4096, "OK", ts="12:34:56")
    assert line.startswith("TFTP|12:34:56|")


def test_tftp_forwarder_download(capsys):
    from nmlinux.core.tftp_helper import _TftpForwarder
    import logging

    handler = _TftpForwarder()

    # Simulate tftpy logs in order: filename, direction, then transfer complete
    for msg in [
        "Requested filename is startup-config",
        "Opening file /root/startup-config for reading",
        "192.168.1.1:12345 Transferred 4096 bytes in 0.01 seconds",
    ]:
        record = logging.LogRecord(
            name="tftpy", level=logging.DEBUG,
            pathname="", lineno=0, msg=msg,
            args=(), exc_info=None,
        )
        handler.emit(record)

    captured = capsys.readouterr()
    assert "TFTP|" in captured.out
    assert "↓" in captured.out
    assert "startup-config" in captured.out
    assert "4096" in captured.out


def test_tftp_forwarder_upload(capsys):
    from nmlinux.core.tftp_helper import _TftpForwarder
    import logging

    handler = _TftpForwarder()

    for msg in [
        "    filename -> firmware.bin",
        "Opening file /srv/tftp/firmware.bin for writing",
        "Session 10.0.0.5:54321 complete",
        "Transferred 2048 bytes in 0.05 seconds",
    ]:
        record = logging.LogRecord(
            name="tftpy", level=logging.DEBUG,
            pathname="", lineno=0, msg=msg,
            args=(), exc_info=None,
        )
        handler.emit(record)

    captured = capsys.readouterr()
    assert "TFTP|" in captured.out
    assert "↑" in captured.out
    assert "firmware.bin" in captured.out
    assert "10.0.0.5" in captured.out
    assert "2048" in captured.out


# ── http_server ───────────────────────────────────────────────────────────────

import threading
import http.client
from nmlinux.core.http_server import make_handler, get_local_ips
from http.server import HTTPServer


def _start_test_server(tmp_path):
    """Start an HTTPServer on a free port, return (server, port)."""
    log_events = []

    def on_log(direction, filename, client_ip, nbytes, status):
        log_events.append((direction, filename, nbytes, status))

    handler_cls = make_handler(tmp_path, on_log)
    server = HTTPServer(("127.0.0.1", 0), handler_cls)
    port = server.server_address[1]
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server, port, log_events


def test_http_get_existing_file(tmp_path):
    (tmp_path / "startup-config.cfg").write_bytes(b"hostname router1\n")
    server, port, log_events = _start_test_server(tmp_path)

    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    conn.request("GET", "/startup-config.cfg")
    resp = conn.getresponse()
    body = resp.read()
    server.shutdown()

    assert resp.status == 200
    assert body == b"hostname router1\n"
    assert len(log_events) == 1
    assert log_events[0][0] == "↓"
    assert log_events[0][3] == "OK"


def test_http_get_missing_file(tmp_path):
    server, port, log_events = _start_test_server(tmp_path)

    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    conn.request("GET", "/nothere.cfg")
    resp = conn.getresponse()
    resp.read()
    server.shutdown()

    assert resp.status == 404


def test_http_post_saves_file(tmp_path):
    server, port, log_events = _start_test_server(tmp_path)

    body = b"interface eth0\n  ip address 10.0.0.1/24\n"
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    conn.request("POST", "/backup.cfg",
                 body=body,
                 headers={"Content-Length": str(len(body))})
    resp = conn.getresponse()
    resp.read()
    server.shutdown()

    assert resp.status == 200
    assert (tmp_path / "backup.cfg").read_bytes() == body
    assert log_events[0][0] == "↑"


def test_http_put_saves_file(tmp_path):
    server, port, log_events = _start_test_server(tmp_path)

    body = b"config data"
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    conn.request("PUT", "/config.txt",
                 body=body,
                 headers={"Content-Length": str(len(body))})
    resp = conn.getresponse()
    resp.read()
    server.shutdown()

    assert resp.status == 200
    assert (tmp_path / "config.txt").read_bytes() == body


def test_get_local_ips_returns_list():
    ips = get_local_ips()
    assert isinstance(ips, list)
    assert len(ips) >= 1
    for ip in ips:
        assert isinstance(ip, str)
        parts = ip.split(".")
        assert len(parts) == 4


def test_http_path_traversal_blocked(tmp_path):
    server, port, _ = _start_test_server(tmp_path)
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    conn.request("GET", "/../../../etc/passwd")
    resp = conn.getresponse()
    resp.read()
    server.shutdown()
    assert resp.status == 403


def test_http_post_path_traversal_blocked(tmp_path):
    server, port, _ = _start_test_server(tmp_path)
    body = b"evil content"
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    conn.request("POST", "/../evil.txt", body=body,
                 headers={"Content-Length": str(len(body))})
    resp = conn.getresponse()
    resp.read()
    server.shutdown()
    assert resp.status == 403
    assert not (tmp_path.parent / "evil.txt").exists()
