from __future__ import annotations
import pytest

from nmlinux.core.i18n import _T

_LANGS = ["fr", "en", "es", "de", "it", "pt", "ja", "zh"]

@pytest.mark.parametrize("lang", _LANGS)
def test_inv_ctx_refresh_present_and_non_empty(lang):
    assert "inv_ctx_refresh" in _T[lang], f"inv_ctx_refresh missing for language '{lang}'"
    assert _T[lang]["inv_ctx_refresh"].strip() != "", f"inv_ctx_refresh is empty for '{lang}'"
