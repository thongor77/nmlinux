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
