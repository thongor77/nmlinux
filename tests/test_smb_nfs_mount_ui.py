from __future__ import annotations
import sys
import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QTableWidgetItem

@pytest.fixture(scope='session')
def qapp():
    app = QApplication.instance() or QApplication(sys.argv)
    return app

from nmlinux.core.i18n import tr
from nmlinux.pages.smb_nfs import (
    SmbNfsPage, _mount_menu_label, _mount_error_message,
)


# ── _mount_menu_label ────────────────────────────────────────────────────────

def test_menu_label_not_mounted():
    assert _mount_menu_label(False) == tr("smb_mount_ctx_mount")

def test_menu_label_mounted():
    assert _mount_menu_label(True) == tr("smb_mount_ctx_unmount")


# ── _mount_error_message ─────────────────────────────────────────────────────

def test_error_message_auth_failure():
    assert _mount_error_message("NT_STATUS_LOGON_FAILURE") == tr("smb_err_auth")

def test_error_message_generic_linux(monkeypatch):
    monkeypatch.setattr("nmlinux.pages.smb_nfs._IS_MACOS", False)
    assert _mount_error_message("some random mount error") == tr("smb_mount_err_pkexec_fail")

def test_error_message_generic_macos(monkeypatch):
    monkeypatch.setattr("nmlinux.pages.smb_nfs._IS_MACOS", True)
    msg = _mount_error_message("weird failure text")
    assert msg == tr("smb_err_failed", msg="weird failure text")


# ── SmbNfsPage wiring ────────────────────────────────────────────────────────

def test_context_menu_policy_set(qapp):
    page = SmbNfsPage()
    assert page._smb_table.contextMenuPolicy() == Qt.ContextMenuPolicy.CustomContextMenu

def test_do_mount_shows_error_when_cifs_missing(qapp, monkeypatch):
    monkeypatch.setattr("nmlinux.pages.smb_nfs._IS_MACOS", False)
    monkeypatch.setattr("nmlinux.pages.smb_nfs.has_mount_cifs", lambda: False)
    page = SmbNfsPage()
    page._do_mount("nas.local", "public")
    assert page._status.text() == tr("smb_mount_err_no_cifs_utils")

def test_on_mount_done_success_updates_status(qapp, monkeypatch):
    monkeypatch.setattr(
        "nmlinux.pages.smb_nfs.mount_point_for",
        lambda h, s: "/home/user/mnt/nas.local_public",
    )
    page = SmbNfsPage()
    page._on_mount_done(True, "", "nas.local", "public")
    assert page._status.text() == tr(
        "smb_mount_status_mounted", path="/home/user/mnt/nas.local_public"
    )

def test_on_unmount_done_success_updates_status(qapp):
    page = SmbNfsPage()
    page._on_unmount_done(True, "")
    assert page._status.text() == tr("smb_mount_status_unmounted")

def test_on_unmount_done_failure_shows_error(qapp, monkeypatch):
    monkeypatch.setattr("nmlinux.pages.smb_nfs._IS_MACOS", True)
    page = SmbNfsPage()
    page._on_unmount_done(False, "target is busy")
    assert page._status.text() == tr("smb_err_failed", msg="target is busy")
