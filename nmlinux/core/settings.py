"""Application settings — persistence and access."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


_SUPPORTED_LANGUAGES = {
    "fr": "Français",
    "en": "English",
    "es": "Español",
    "de": "Deutsch",
    "it": "Italiano",
    "pt": "Português",
    "ja": "日本語",
    "zh": "中文",
}


@dataclass
class AppSettings:
    language: str = "fr"   # fr | en | es | de | it | pt | ja | zh


class SettingsStore:
    def __init__(self, path: Path | None = None) -> None:
        if path is None:
            data_dir = Path.home() / ".local" / "share" / "nmlinux"
            data_dir.mkdir(parents=True, exist_ok=True)
            path = data_dir / "settings.json"
        self._path = path

    def load(self) -> AppSettings:
        if not self._path.exists():
            return AppSettings()
        try:
            raw = json.loads(self._path.read_text())
            fields = AppSettings.__dataclass_fields__
            return AppSettings(**{k: v for k, v in raw.items() if k in fields})
        except Exception:
            return AppSettings()

    def save(self, settings: AppSettings) -> None:
        self._path.write_text(
            json.dumps(asdict(settings), indent=2, ensure_ascii=False)
        )


# Module-level singleton — loaded once at import time
_store    = SettingsStore()
_settings = _store.load()


def get() -> AppSettings:
    return _settings


def save() -> None:
    _store.save(_settings)
