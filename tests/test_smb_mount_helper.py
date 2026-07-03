from __future__ import annotations
from unittest.mock import patch, MagicMock

from nmlinux.core.smb_mount_helper import parse_args, try_mount, main


# ── parse_args ──────────────────────────────────────────────────────────────

def test_parse_args_basic():
    args = parse_args([
        "--target", "//nas.local/public",
        "--mountpoint", "/home/user/mnt/nas.local_public",
        "--credentials", "/tmp/cred_file",
    ])
    assert args.target == "//nas.local/public"
    assert args.mountpoint == "/home/user/mnt/nas.local_public"
    assert args.credentials == "/tmp/cred_file"


# ── try_mount ────────────────────────────────────────────────────────────────

def test_try_mount_builds_correct_command():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        try_mount("//nas.local/public", "/mnt/point", "credentials=/tmp/cred")
    cmd = mock_run.call_args[0][0]
    assert cmd == [
        "mount", "-t", "cifs", "-o", "credentials=/tmp/cred",
        "//nas.local/public", "/mnt/point",
    ]


# ── main ─────────────────────────────────────────────────────────────────────

def test_main_success_no_retry():
    argv = ["--target", "//nas.local/public", "--mountpoint", "/mnt/p", "--credentials", "/tmp/c"]
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        code = main(argv)
    assert code == 0
    assert mock_run.call_count == 1

def test_main_retries_once_on_error_95():
    argv = ["--target", "//192.168.1.99/video", "--mountpoint", "/mnt/p", "--credentials", "/tmp/c"]
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = [
            MagicMock(returncode=1, stdout="", stderr="mount error(95): Operation not supported"),
            MagicMock(returncode=0, stdout="", stderr=""),
        ]
        code = main(argv)
    assert code == 0
    assert mock_run.call_count == 2
    second_opts = mock_run.call_args_list[1][0][0][4]
    assert "vers=2.0" in second_opts

def test_main_no_retry_for_unrelated_error():
    argv = ["--target", "//nas.local/public", "--mountpoint", "/mnt/p", "--credentials", "/tmp/c"]
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="mount error(13): Permission denied"
        )
        code = main(argv)
    assert code == 1
    assert mock_run.call_count == 1

def test_main_retry_also_fails_returns_last_returncode():
    argv = ["--target", "//192.168.1.99/video", "--mountpoint", "/mnt/p", "--credentials", "/tmp/c"]
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = [
            MagicMock(returncode=1, stdout="", stderr="mount error(95): Operation not supported"),
            MagicMock(returncode=13, stdout="", stderr="mount error(13): Permission denied"),
        ]
        code = main(argv)
    assert code == 13
    assert mock_run.call_count == 2
