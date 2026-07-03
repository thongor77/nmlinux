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


from nmlinux.core.smb_mount import mount, unmount


# ── mount() — Linux ─────────────────────────────────────────────────────────

def test_mount_linux_success(monkeypatch, tmp_path):
    import nmlinux.core.smb_mount as smb_mount
    monkeypatch.setattr(smb_mount, "_IS_MACOS", False)
    monkeypatch.setattr(smb_mount, "mount_point_for", lambda h, s: tmp_path / "mnt")

    with patch("shutil.which", return_value="/usr/sbin/mount.cifs"), \
         patch("subprocess.run") as mock_run, \
         patch("tempfile.mkstemp") as mock_mkstemp, \
         patch("os.fdopen"), \
         patch("os.chmod"), \
         patch("os.unlink") as mock_unlink:
        mock_mkstemp.return_value = (99, "/tmp/nmlinux_smb_fake")
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        ok, err = mount("nas.local", "public", "alice", "secret")

    assert ok is True
    assert err == ""
    cmd = mock_run.call_args[0][0]
    assert cmd[0] == "pkexec"
    assert "mount" in cmd
    assert "-t" in cmd and "cifs" in cmd
    assert any(a.startswith("credentials=") for a in cmd)
    # credentials file must be cleaned up regardless of outcome
    mock_unlink.assert_called_once_with("/tmp/nmlinux_smb_fake")

def test_mount_linux_missing_cifs_utils(monkeypatch, tmp_path):
    import nmlinux.core.smb_mount as smb_mount
    monkeypatch.setattr(smb_mount, "_IS_MACOS", False)
    monkeypatch.setattr(smb_mount, "mount_point_for", lambda h, s: tmp_path / "mnt")

    with patch("shutil.which", return_value=None):
        ok, err = mount("nas.local", "public", "", "")

    assert ok is False
    assert err == "MOUNT_CIFS_NOT_FOUND"

def test_mount_linux_failure_cleans_up_credentials_file(monkeypatch, tmp_path):
    import nmlinux.core.smb_mount as smb_mount
    monkeypatch.setattr(smb_mount, "_IS_MACOS", False)
    monkeypatch.setattr(smb_mount, "mount_point_for", lambda h, s: tmp_path / "mnt")

    with patch("shutil.which", return_value="/usr/sbin/mount.cifs"), \
         patch("subprocess.run") as mock_run, \
         patch("tempfile.mkstemp") as mock_mkstemp, \
         patch("os.fdopen"), \
         patch("os.chmod"), \
         patch("os.unlink") as mock_unlink:
        mock_mkstemp.return_value = (99, "/tmp/nmlinux_smb_fake")
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="mount error(13): Permission denied"
        )

        ok, err = mount("nas.local", "public", "alice", "wrong")

    assert ok is False
    assert "Permission denied" in err
    mock_unlink.assert_called_once_with("/tmp/nmlinux_smb_fake")


# ── mount() — macOS ─────────────────────────────────────────────────────────

def test_mount_macos_success(monkeypatch, tmp_path):
    import nmlinux.core.smb_mount as smb_mount
    monkeypatch.setattr(smb_mount, "_IS_MACOS", True)
    monkeypatch.setattr(smb_mount, "mount_point_for", lambda h, s: tmp_path / "mnt")

    with patch("shutil.which", return_value="/sbin/mount_smbfs"), \
         patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        ok, err = mount("nas.local", "public", "alice", "secret")

    assert ok is True
    assert err == ""
    cmd = mock_run.call_args[0][0]
    assert cmd[0] == "mount_smbfs"
    assert "alice:secret@nas.local" in cmd[1]

def test_mount_macos_no_credentials(monkeypatch, tmp_path):
    import nmlinux.core.smb_mount as smb_mount
    monkeypatch.setattr(smb_mount, "_IS_MACOS", True)
    monkeypatch.setattr(smb_mount, "mount_point_for", lambda h, s: tmp_path / "mnt")

    with patch("shutil.which", return_value="/sbin/mount_smbfs"), \
         patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        mount("nas.local", "public", "", "")

    cmd = mock_run.call_args[0][0]
    assert cmd[1] == "//nas.local/public"


# ── unmount() ───────────────────────────────────────────────────────────────

def test_unmount_linux_success(monkeypatch, tmp_path):
    import nmlinux.core.smb_mount as smb_mount
    monkeypatch.setattr(smb_mount, "_IS_MACOS", False)
    mountpoint = tmp_path / "mnt"
    mountpoint.mkdir()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        ok, err = unmount(mountpoint)

    assert ok is True
    assert err == ""
    assert mock_run.call_args[0][0][0] == "pkexec"
    assert not mountpoint.exists()

def test_unmount_macos_success(monkeypatch, tmp_path):
    import nmlinux.core.smb_mount as smb_mount
    monkeypatch.setattr(smb_mount, "_IS_MACOS", True)
    mountpoint = tmp_path / "mnt"
    mountpoint.mkdir()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        ok, err = unmount(mountpoint)

    assert ok is True
    assert mock_run.call_args[0][0][0] == "umount"
    assert not mountpoint.exists()

def test_unmount_failure_keeps_directory(monkeypatch, tmp_path):
    import nmlinux.core.smb_mount as smb_mount
    monkeypatch.setattr(smb_mount, "_IS_MACOS", False)
    mountpoint = tmp_path / "mnt"
    mountpoint.mkdir()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="umount: target is busy"
        )
        ok, err = unmount(mountpoint)

    assert ok is False
    assert "busy" in err
    assert mountpoint.exists()
