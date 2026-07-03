from __future__ import annotations
import pytest

from nmlinux.core.i18n import _T

_KEYS = [
    "smb_mount_ctx_mount",
    "smb_mount_ctx_unmount",
    "smb_mount_status_mounted",
    "smb_mount_status_unmounted",
    "smb_mount_err_no_cifs_utils",
    "smb_mount_err_pkexec_fail",
]
_LANGS = ["fr", "en", "es", "de", "it", "pt", "ja", "zh"]

@pytest.mark.parametrize("lang", _LANGS)
def test_smb_mount_keys_present_and_non_empty(lang):
    for key in _KEYS:
        assert key in _T[lang], f"{key} missing for language '{lang}'"
        assert _T[lang][key].strip() != "", f"{key} is empty for '{lang}'"

def test_smb_mount_status_mounted_has_path_placeholder():
    for lang in _LANGS:
        assert "{path}" in _T[lang]["smb_mount_status_mounted"]
