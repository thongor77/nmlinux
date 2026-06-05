from __future__ import annotations
import os
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from nmlinux.pages.ssh_keys import _parse_keygen_line, _scan_keys, _keygen_args


# ── _parse_keygen_line ─────────────────────────────────────────────────────

def test_parse_ed25519():
    line = "256 SHA256:AbCdEfGhIjKlMnOpQrStUvWxYz user@host (ED25519)"
    result = _parse_keygen_line(line)
    assert result is not None
    assert result["bits"] == 256
    assert result["fingerprint"] == "SHA256:AbCdEfGhIjKlMnOpQrStUvWxYz"
    assert result["comment"] == "user@host"
    assert result["type"] == "ED25519"

def test_parse_rsa():
    line = "4096 SHA256:XxXxXxXxXxXxXxXxXxXxXxXxXx admin@server (RSA)"
    result = _parse_keygen_line(line)
    assert result is not None
    assert result["bits"] == 4096
    assert result["type"] == "RSA"

def test_parse_comment_with_spaces():
    line = "256 SHA256:AAAAbbbbCCCCdddd my laptop key (ED25519)"
    result = _parse_keygen_line(line)
    assert result is not None
    assert result["comment"] == "my laptop key"

def test_parse_invalid_returns_none():
    assert _parse_keygen_line("not a valid line") is None
    assert _parse_keygen_line("") is None


# ── _scan_keys ─────────────────────────────────────────────────────────────

def test_scan_keys_returns_only_complete_pairs(tmp_path):
    # Create a complete pair
    (tmp_path / "id_ed25519").write_text("PRIVATE")
    (tmp_path / "id_ed25519.pub").write_text("PUBLIC")
    # Create an orphan .pub (no private key)
    (tmp_path / "id_rsa.pub").write_text("PUBLIC_ONLY")

    fake_output = "256 SHA256:AbCdEfGh user@host (ED25519)\n"

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0, stdout=fake_output
        )
        results = _scan_keys(tmp_path)

    assert len(results) == 1
    assert results[0]["file"] == "id_ed25519"
    assert results[0]["type"] == "ED25519"
    assert results[0]["pub_path"] == tmp_path / "id_ed25519.pub"
    assert results[0]["priv_path"] == tmp_path / "id_ed25519"

def test_scan_keys_empty_dir(tmp_path):
    results = _scan_keys(tmp_path)
    assert results == []

def test_scan_keys_keygen_fails_skips_key(tmp_path):
    (tmp_path / "id_ed25519").write_text("PRIVATE")
    (tmp_path / "id_ed25519.pub").write_text("PUBLIC")

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        results = _scan_keys(tmp_path)

    assert results == []


# ── _keygen_args ───────────────────────────────────────────────────────────

def test_keygen_args_ed25519():
    args = _keygen_args("ED25519", Path("/home/user/.ssh/id_ed25519"), "user@host", "")
    assert args[0] == "ssh-keygen"
    assert "-t" in args
    assert "ed25519" in args
    assert "-f" in args
    assert "/home/user/.ssh/id_ed25519" in args
    assert "-C" in args
    assert "user@host" in args
    assert "-N" in args
    assert "" in args

def test_keygen_args_rsa():
    args = _keygen_args("RSA", Path("/home/user/.ssh/id_rsa"), "comment", "mypass")
    assert "rsa" in args
    assert "-b" in args
    assert "4096" in args
    assert "mypass" in args

def test_keygen_args_no_xfreerdp_as_first():
    args = _keygen_args("ED25519", Path("/tmp/key"), "c", "")
    assert args[0] == "ssh-keygen"
