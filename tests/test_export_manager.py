from __future__ import annotations
import json
from pathlib import Path
from unittest.mock import patch
import pytest

from nmlinux.export_manager import (
    to_json, to_text, to_markdown, to_pdf, save_export, _collect_dns,
)

SAMPLE: dict = {
    "timestamp": "2026-06-13T10:00:00",
    "platform": "Linux",
    "interfaces": [
        {
            "ifname": "eth0",
            "operstate": "UP",
            "addr_info": [{"local": "192.168.1.10", "prefixlen": 24}],
        }
    ],
    "routes": [
        {"dst": "default", "gateway": "192.168.1.1", "dev": "eth0"},
    ],
    "dns": ["1.1.1.1", "8.8.8.8"],
}


def test_to_json_round_trip():
    result = to_json(SAMPLE)
    parsed = json.loads(result)
    assert parsed["platform"] == "Linux"
    assert parsed["interfaces"][0]["ifname"] == "eth0"


def test_to_text_contains_key_values():
    result = to_text(SAMPLE)
    assert "eth0" in result
    assert "192.168.1.1" in result
    assert "1.1.1.1" in result


def test_to_markdown_contains_table():
    result = to_markdown(SAMPLE)
    assert "|" in result
    assert "eth0" in result


def test_to_markdown_contains_dns():
    result = to_markdown(SAMPLE)
    assert "1.1.1.1" in result


def test_to_pdf_missing_reportlab_returns_message():
    with patch.dict("sys.modules", {
        "reportlab": None,
        "reportlab.lib": None,
        "reportlab.lib.pagesizes": None,
        "reportlab.pdfgen": None,
        "reportlab.pdfgen.canvas": None,
    }):
        error = to_pdf(SAMPLE, "/tmp/test_nmlinux.pdf")
    assert error is not None
    assert "reportlab" in error


def test_save_export_json(tmp_path):
    path = str(tmp_path / "report.json")
    error = save_export(SAMPLE, "json", path)
    assert error is None
    parsed = json.loads(Path(path).read_text())
    assert parsed["platform"] == "Linux"


def test_save_export_txt(tmp_path):
    path = str(tmp_path / "report.txt")
    error = save_export(SAMPLE, "txt", path)
    assert error is None
    content = Path(path).read_text()
    assert "eth0" in content


def test_save_export_md(tmp_path):
    path = str(tmp_path / "report.md")
    error = save_export(SAMPLE, "md", path)
    assert error is None
    content = Path(path).read_text()
    assert "|" in content


def test_collect_dns_parses_resolv_conf(tmp_path):
    resolv = tmp_path / "resolv.conf"
    resolv.write_text("# generated\nnameserver 1.1.1.1\nnameserver 8.8.8.8\n")
    result = _collect_dns(str(resolv))
    assert result == ["1.1.1.1", "8.8.8.8"]


def test_collect_dns_ignores_comments(tmp_path):
    resolv = tmp_path / "resolv.conf"
    resolv.write_text("# comment\nsearch local\nnameserver 9.9.9.9\n")
    result = _collect_dns(str(resolv))
    assert result == ["9.9.9.9"]


def test_collect_dns_missing_file_returns_empty():
    result = _collect_dns("/nonexistent/resolv.conf")
    assert result == []


def test_save_export_unknown_format_returns_error(tmp_path):
    path = str(tmp_path / "report.xyz")
    error = save_export(SAMPLE, "xyz", path)
    assert error is not None
    assert "xyz" in error
