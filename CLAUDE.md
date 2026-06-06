# CLAUDE.md

Guidance for Claude Code when working in this repository.
**Knowledge base:** `docs/` — read it before making structural changes.

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
python -m build --wheel --no-isolation  # wheel only — sdist fails (aur/ symlink)
```

## Tests

```bash
pytest tests/ -v    # 37 tests covering RDP/VNC/SSH-Keys logic (no Qt widgets)
```

## Architecture

Full details in `docs/Architecture.md`. Key points:

`window.py` — `MainWindow` holds a `QListWidget` sidebar and a `QStackedWidget`.
Every page is registered in `_TOOLS` as `(icon_names, label, PageClass, tooltip)`.
**Adding a page:** append to `_TOOLS` + import + add i18n keys + add help content.

`nmlinux/core/` — shared utilities:
- `i18n.py` — `tr(key, **kwargs)`: 8 languages (fr/en/es/de/it/pt/ja/zh), ~720 keys each. Add new keys in ALL 8 blocks. `fr` is the reference (always complete).
- `theme.py` — `is_dark()`, `color_ok()`, `color_err()`: call at widget creation time, never at module load. Override `changeEvent(QEvent.Type.ApplicationPaletteChange)` + `update()` on any widget with custom painting.
- `cli_bar.py` — `get_cli_bar().set_cmd(cmd)`: call in `_update_cli()`, wired to input changes and `showEvent`.
- `settings.py` — `AppSettings` singleton (JSON at `~/.local/share/nmlinux/settings.json`). Access with `.language`, NOT `.get()`.
- `help_content.py` — `get_help(label)`: contextual help, 8 languages × 27 modules.
- `icons.py` — `themed_icon(*names)`: 21 bundled Lucide SVGs, colour `#60a5fa`, no system theme needed.

`nmlinux/pages/` — one `QWidget` subclass per page. Standard pattern:

```python
class FooPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        # layout.addWidget(table, 10) + layout.addStretch(1)
        # to avoid Qt centering the table when it's hidden

    def showEvent(self, event) -> None:
        self._update_cli()
        super().showEvent(event)
```

Heavy work runs in a `QThread` subclass with typed `Signal`s.
Column indices for `QTableWidget` are module-level constants: `_C_IP, _C_HOST = range(2)`.

## i18n — Quick Check

```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from nmlinux.core import i18n
fr = set(i18n._T['fr'].keys())
for lang in ['en','es','de','it','pt','ja','zh']:
    m = fr - set(i18n._T.get(lang,{}).keys())
    if m: print(f'{lang}: {sorted(m)}')
"
```

## Programmatic Injection in help_content.py

⚠️ Critical pattern — see `docs/Decisions-Techniques.md` DT-13 for the full explanation.

```python
# CORRECT: split PT_CLOSE and MOD_CLOSE
result += "        },"   # PT_CLOSE — closes last existing lang block
result += NEW_BLOCK      # new block (\n        "xx": {...},)
result += "\n    },"     # MOD_CLOSE — closes the module

# WRONG: result += NEW_BLOCK + PATTERN
# → new block ends up nested INSIDE the last block (valid Python, wrong semantics)
```

## System Dependencies

Required: `networkmanager` (nmcli), `iproute2` (ip), `iputils` (ping/tracepath)

Optional: `nmap`, `whois`, `net-snmp`, `bind` (dig), `traceroute`, `python-hwdata`,
`nm-connection-editor`, `samba` (smbclient), `nfs-utils` (showmount), `openssl`,
`xfreerdp`/`xfreerdp3`, `vncviewer` (TigerVNC), `mtr`, `curl`, `wakeonlan`,
`openssh` (ssh-keygen), `pkexec` (polkit)

## AUR Update Workflow

```bash
# 1. Get sha256 of the new source tarball
curl -sL "https://github.com/thongor77/nmlinux/archive/refs/tags/vX.Y.Z.tar.gz" \
  -o /tmp/src.tar.gz && sha256sum /tmp/src.tar.gz

# 2. Update aur/PKGBUILD: pkgver + sha256sums
# 3. Regenerate .SRCINFO
cd aur && makepkg --printsrcinfo > .SRCINFO

# 4. Push to AUR
git clone ssh://aur@aur.archlinux.org/nmlinux.git /tmp/aur-push
cp PKGBUILD .SRCINFO /tmp/aur-push/
cd /tmp/aur-push
git config user.email "magetriste@proton.me" && git config user.name "thongor77"
git add PKGBUILD .SRCINFO && git commit -m "vX.Y.Z" && git push

# SSH key: ~/.ssh/id_aur  |  AUR account: magetriste  |  GitHub: thongor77
```

## Persistence Files

- Settings (language): `~/.local/share/nmlinux/settings.json`
- SSH connections: `~/.local/share/nmlinux/ssh_connections.json` (format v2)
- RDP connections: `~/.local/share/nmlinux/rdp_connections.json` (format v2)
- VNC connections: `~/.local/share/nmlinux/vnc_connections.json` (format v2)
- WoL hosts: `~/.local/share/nmlinux/wol_hosts.json`
- Speed test history: `~/.local/share/nmlinux/speedtest_history.json` (last 5)
- Desktop entry: `~/.local/share/applications/nmlinux.desktop`
