from __future__ import annotations
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from nmlinux.core.smb_mount import (
    mount_point_for, is_mounted, has_mount_cifs,
)


# ── mount_point_for ─────────────────────────────────────────────────────────

def test_mount_point_basic(tmp_path):
    result = mount_point_for("nas.local", "public", base_dir=tmp_path)
    assert result == tmp_path / "nas.local_public"

def test_mount_point_sanitizes_unusual_characters(tmp_path):
    result = mount_point_for("nas server!", "my share/docs", base_dir=tmp_path)
    assert result.name == "nas_server__my_share_docs"

def test_mount_point_avoids_collision_between_hosts(tmp_path):
    a = mount_point_for("nas-a", "public", base_dir=tmp_path)
    b = mount_point_for("nas-b", "public", base_dir=tmp_path)
    assert a != b

def test_mount_point_default_base_dir_is_home_mnt():
    result = mount_point_for("nas.local", "public")
    assert result == Path.home() / "mnt" / "nas.local_public"


# ── is_mounted ──────────────────────────────────────────────────────────────

def test_is_mounted_true(tmp_path):
    with patch("os.path.ismount", return_value=True) as mock_ismount:
        assert is_mounted(tmp_path) is True
        mock_ismount.assert_called_once_with(tmp_path)

def test_is_mounted_false(tmp_path):
    with patch("os.path.ismount", return_value=False):
        assert is_mounted(tmp_path) is False


# ── has_mount_cifs ──────────────────────────────────────────────────────────

def test_has_mount_cifs_found_on_linux(monkeypatch):
    import nmlinux.core.smb_mount as smb_mount
    monkeypatch.setattr(smb_mount, "_IS_MACOS", False)
    with patch("shutil.which", return_value="/usr/sbin/mount.cifs"):
        assert has_mount_cifs() is True

def test_has_mount_cifs_missing_on_linux(monkeypatch):
    import nmlinux.core.smb_mount as smb_mount
    monkeypatch.setattr(smb_mount, "_IS_MACOS", False)
    with patch("shutil.which", return_value=None):
        assert has_mount_cifs() is False

def test_has_mount_cifs_always_true_on_macos(monkeypatch):
    import nmlinux.core.smb_mount as smb_mount
    monkeypatch.setattr(smb_mount, "_IS_MACOS", True)
    with patch("shutil.which", return_value=None):
        assert has_mount_cifs() is True
