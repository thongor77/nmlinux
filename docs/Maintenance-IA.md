# Règles de Maintenance pour Claude Code

Ce fichier décrit les patterns à suivre lors de modifications assistées par IA.

---

## Ajouter un nouveau module

### 1 — Créer `nmlinux/pages/foo.py`

```python
from __future__ import annotations
from PySide6.QtWidgets import QWidget, QVBoxLayout
from nmlinux.core.i18n import tr
from nmlinux.core.cli_bar import get_cli_bar

_C_COL1, _C_COL2 = range(2)   # constantes de colonnes au niveau module

class FooPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._worker = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        # layout.addWidget(table, 10)  ← stretch 10 sur la table
        # layout.addStretch(1)          ← stretch 1 en bas (évite centrage Qt)

    def showEvent(self, event) -> None:
        self._update_cli()
        super().showEvent(event)

    def _update_cli(self) -> None:
        if bar := get_cli_bar():
            bar.set_cmd("cmd ...")
```

### 2 — Enregistrer dans `window.py`

```python
from nmlinux.pages.foo import FooPage

_TOOLS = [
    ...
    (
        ("icon-name-1", "icon-name-2"),
        "Foo", FooPage,
        tr("nav_hint_foo"),
    ),
]
```

### 3 — Ajouter les clés i18n dans `core/i18n.py`

Ajouter dans **les 8 blocs** (`fr`, `en`, `es`, `de`, `it`, `pt`, `ja`, `zh`) :
- `"nav_foo": "Foo"` — label sidebar
- `"nav_hint_foo": "Description courte..."` — tooltip badge `?`
- Toutes les clés propres au module (`foo_*`)

Le bloc `fr` est la référence. Si une clé manque dans une autre langue, `tr()` retombe sur `fr`.

### 4 — Ajouter le contenu aide dans `core/help_content.py`

```python
"Foo": {
    "fr": {"desc": "...", "examples": [...], "cli": [...]},
    "en": {"desc": "...", "examples": [...], "cli": [...]},
    "es": {"desc": "...", "examples": [...], "cli": [...]},
    "de": {"desc": "...", "examples": [...], "cli": [...]},
    "it": {"desc": "...", "examples": [...], "cli": [...]},
    "pt": {"desc": "...", "examples": [...], "cli": [...]},
    "ja": {"desc": "...", "examples": [...], "cli": [...]},
    "zh": {"desc": "...", "examples": [...], "cli": [...]},
},
```

Le label `"Foo"` doit correspondre exactement à la chaîne dans `_TOOLS`.

### 5 — Ajouter une icône si nécessaire

Si le nom d'icône n'est pas dans `_NAME_MAP` de `core/icons.py`, ajouter le mapping ou déposer un SVG Lucide dans `assets/icons/`. La couleur `#60a5fa` est appliquée automatiquement.

---

## Pattern Worker (QThread)

```python
class FooWorker(QThread):
    result = Signal(dict)
    finished = Signal()
    error = Signal(str)

    def __init__(self, param: str) -> None:
        super().__init__()
        self._param = param
        self._stop = False

    def run(self) -> None:
        try:
            # ... travail bloquant ...
            if self._stop:
                return
            self.result.emit(data)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()

    def stop(self) -> None:
        self._stop = True
        self.wait(2000)
```

**Règle :** Ne jamais bloquer le thread principal. Tout `subprocess`, `socket`, lecture fichier lente → QThread.

---

## Thème clair/sombre

```python
from nmlinux.core.theme import color_ok, color_err, is_dark

class MyWidget(QWidget):
    def _build_ui(self) -> None:
        self._lbl_ok = QLabel()
        self._lbl_ok.setStyleSheet(f"color: {color_ok()};")  # OK : lecture à la création

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        color = QColor(color_ok())  # OK : lecture à chaque paint
        ...

    def changeEvent(self, event) -> None:
        if event.type() == QEvent.Type.ApplicationPaletteChange:
            self._lbl_ok.setStyleSheet(f"color: {color_ok()};")
            self.update()
        super().changeEvent(event)
```

**Règle :** Ne jamais stocker `color_ok()` / `color_err()` comme constante de module.

---

## Ajouter une clé i18n

1. Trouver la position dans le bloc `fr` (ordre thématique par module).
2. Ajouter dans **tous les blocs** dans le même ordre.
3. Si une langue n'a pas de traduction disponible, copier la valeur anglaise.
4. Pour `ja` et `zh` : garder les termes techniques en latin (SSH, DNS, IP, MAC, CIDR, VPN, NAS…).

**Vérification rapide :**
```python
python3 -c "
import sys; sys.path.insert(0, '.')
from nmlinux.core import i18n
fr_keys = set(i18n._T['fr'].keys())
for lang in ['en','es','de','it','pt','ja','zh']:
    missing = fr_keys - set(i18n._T.get(lang, {}).keys())
    if missing: print(f'{lang}: {sorted(missing)}')
"
```

---

## Injection programmatique dans help_content.py

Si vous devez ajouter une nouvelle langue à `help_content.py` par script :

```python
PATTERN = "        },\n    },"   # pattern de fin de module
PT_CLOSE = "        },"          # ferme le DERNIER bloc langue existant
MOD_CLOSE = "\n    },"           # ferme le module

with open(TARGET) as f:
    content = f.read()

parts = content.split(PATTERN)
result = parts[0]
for i in range(len(parts) - 1):
    if i < N_MODULES_TO_UPDATE:
        result += PT_CLOSE          # ferme le bloc précédent
        result += NEW_LANG_BLOCK    # ajoute le nouveau bloc
        result += MOD_CLOSE         # ferme le module
    else:
        result += PATTERN
    result += parts[i + 1]
```

⚠️ **Ne pas** faire `result += NEW_LANG_BLOCK + PATTERN` — cela place le nouveau bloc **dans** le dernier bloc existant (voir DT-13 dans Decisions-Techniques.md).

**Vérification post-injection :**
```python
import ast
ast.parse(result)  # vérifie la syntaxe Python
# Puis vérifier que chaque module a bien le bloc au bon niveau (pas imbriqué)
```

---

## Release

```bash
# 1. Bumper la version
#    nmlinux/__init__.py : __version__ = "X.Y.Z"
#    pyproject.toml     : version = "X.Y.Z"

# 2. Mettre à jour README.md (titre + section Changelog)

# 3. Commit + tag
git add nmlinux/__init__.py pyproject.toml README.md
git commit -m "chore: bump version to X.Y.Z"
git tag -a vX.Y.Z -m "vX.Y.Z — résumé"

# 4. Build wheel
python -m build --wheel --no-isolation
# (le sdist échoue à cause d'un symlink dans aur/ — wheel uniquement)

# 4b. Build AppImage (NE PAS OUBLIER — asset de chaque release Linux)
#     lit la version depuis pyproject.toml → dist/NMLinux-X.Y.Z-x86_64.AppImage
bash packaging/build-appimage.sh

# 5. Push + GitHub Release (joindre wheel ET AppImage)
git push origin main --tags
gh release create vX.Y.Z \
  dist/nmlinux-X.Y.Z-py3-none-any.whl \
  dist/NMLinux-X.Y.Z-x86_64.AppImage \
  --title "vX.Y.Z — titre" --notes "..."

# 6. AUR
curl -sL "https://github.com/thongor77/nmlinux/archive/refs/tags/vX.Y.Z.tar.gz" \
  -o /tmp/src.tar.gz && sha256sum /tmp/src.tar.gz
# Éditer aur/PKGBUILD : pkgver + sha256sums
cd aur && makepkg --printsrcinfo > .SRCINFO
git clone ssh://aur@aur.archlinux.org/nmlinux.git /tmp/aur-push
cp PKGBUILD .SRCINFO /tmp/aur-push/
cd /tmp/aur-push
git config user.email "magetriste@proton.me" && git config user.name "thongor77"
git add PKGBUILD .SRCINFO && git commit -m "vX.Y.Z — ..." && git push
```

---

## Tests

Les tests couvrent uniquement la logique pure (sans Qt) :

```bash
pytest tests/ -v
```

| Fichier | Sujet | Tests |
|---------|-------|-------|
| `test_rdp_core.py` | `build_rdp_args()`, `RdpStore`, `RdpConnection` | 14 |
| `test_vnc_core.py` | `build_vnc_args()`, `VncStore`, `VncConnection` | 13 |
| `test_ssh_keys.py` | `_parse_keygen_line()`, `_scan_keys()`, `_keygen_args()` | 10 |
| `test_command_palette.py` | Fuzzy search, navigation clavier | 10 |
| `test_export_manager.py` | `ExportDialog`, formats JSON/MD/TXT/PDF | 12 |
| `test_file_transfer_core.py` | Serveur HTTP GET/POST, helper TFTP | 16 |
| `test_smb_mount.py` | `mount()`/`unmount()` Linux + macOS | 21 |
| `test_smb_mount_helper.py` | Détection montage, points de montage | 6 |
| `test_smb_mount_i18n.py` | Clés i18n montage SMB (8 langues) | 9 |
| `test_smb_nfs_mount_ui.py` | Menu contextuel clic droit `SmbNfsPage` | 11 |
| `test_asset_collectors.py` | `_collect_ssh`/`_collect_winrm`/`_collect_snmp`, détection Nmap | 10 |
| `test_asset_inventory.py` | `AssetInventoryPage` : dédoublonnage, menu contextuel rescan | 11 |
| `test_asset_inventory_i18n.py` | Clés i18n Asset Inventory (8 langues) | 8 |
| `test_host_actions.py` | `HostActionMenu`, détection port ouvert | 4 |
| `test_ping_targets.py` | `PingTarget`, `_PingTargetStore` | 7 |

**162 tests au total.** Logique pure pour la majorité ; `test_asset_inventory.py`, `test_host_actions.py` et `test_smb_nfs_mount_ui.py` instancient une `QApplication` de session (fixture `qapp`) pour exercer de vrais widgets Qt (menus contextuels, tables). Le CLAUDE.md disait "No test suite exists" — c'était vrai avant v1.3.0.

---

## Comptes et accès

| Service | Compte | Clé |
|---------|--------|-----|
| GitHub | thongor77 | — |
| AUR | magetriste | `~/.ssh/id_aur` (ed25519) |
| Email | magetriste@proton.me | — |

SSH config AUR (`~/.ssh/config`) :
```
Host aur.archlinux.org
    IdentityFile ~/.ssh/id_aur
```
