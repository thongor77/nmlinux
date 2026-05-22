# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the App

```bash
# Development (from repo root)
./nmlinux.sh
# or
python3 -m nmlinux.main

# After pip install
nmlinux
```

## Build & Install

```bash
pip install -e .                        # editable install for dev
python -m build --wheel --no-isolation  # build wheel (skip sdist — aur/src symlink breaks sdist)
```

No test suite exists.

## Architecture

`window.py` — `MainWindow` holds a `QListWidget` sidebar and a `QStackedWidget`. Every page is registered in `_TOOLS` as `(icon_names_tuple, label_str, PageClass)`. Adding a page = append to `_TOOLS` + import.

`nmlinux/core/` — shared utilities used by all pages:
- `i18n.py` — `tr(key, **kwargs)`: translated string lookup. Add new keys in all 4 language blocks (FR, EN, ES, DE) before `common_export_csv` in each block.
- `theme.py` — `is_dark()`, `color_ok()`, `color_err()`: call at widget creation time, never at module load. Override `changeEvent(QEvent.Type.ApplicationPaletteChange)` + `update()` on any widget with custom painting.
- `cli_bar.py` — `get_cli_bar().set_cmd(cmd)`: call in `_update_cli()`, wired to input changes and `showEvent`.
- `settings.py` — `AppSettings` singleton (JSON at `~/.local/share/nmlinux/settings.json`).

`nmlinux/pages/` — one `QWidget` subclass per page. Standard pattern:

```python
class FooPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)

    def showEvent(self, event) -> None:
        self._update_cli()
        super().showEvent(event)
```

Heavy work runs in a `QThread` subclass with typed `Signal`s; the page connects signals in `_build_ui` and stops the worker via a `stop()` method. Never block the main thread.

Column indices for `QTableWidget` are module-level constants: `_C_IP, _C_HOST, _C_STATE = range(3)`.

## System Dependencies

Required: `networkmanager` (`nmcli`), `iproute2` (`ip`), `iputils` (`ping`/`tracepath`)

Optional: `nmap`, `whois`, `net-snmp` (`snmpwalk`/`snmpget`), `bind` (`dig`), `traceroute`, `python-hwdata` (OUI lookup), `nm-connection-editor`

## AUR Update Workflow

```bash
# Bump pkgver + sha256sums in aur/PKGBUILD, then:
cd /tmp && git clone ssh://aur.archlinux.org/nmlinux.git aur-nmlinux
cp ~/claude-projects/nmlinux/aur/PKGBUILD aur-nmlinux/
cd aur-nmlinux && makepkg --printsrcinfo > .SRCINFO
git add PKGBUILD .SRCINFO && git commit -m "Update to vX.Y.Z"
git push
# SSH key: ~/.ssh/id_aur  |  AUR account: magetriste  |  GitHub: thongor77
```

## Persistence Files

- SSH connections: `~/.local/share/nmlinux/ssh_connections.json`
- Settings (language): `~/.local/share/nmlinux/settings.json`
- Desktop entry: `~/.local/share/applications/nmlinux.desktop`
