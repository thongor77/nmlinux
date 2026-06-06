# NMLinux Custom Skin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create `/home/luust/claude-projects/nmlinux-theme/` — an isolated copy of nmlinux with a custom dark skin (green gradient, Inter + JetBrains Mono fonts, full QSS stylesheet) and a stubbed light theme.

**Architecture:** Full copy of `nmlinux/` source into `nmlinux-theme/`, with a new `skin/` module that loads fonts and applies a QSS stylesheet. The window's gradient is painted via a `GradientWidget` subclass (QSS cannot reliably cover the full window). The app palette is also updated so `is_dark()` / `_dark_mode()` return `True` without requiring a KDE/GNOME dark session.

**Tech Stack:** Python 3.11+, PySide6 ≥ 6.6, Inter (TTF), JetBrains Mono (TTF), pytest

---

## File Map

| Action | Path | Responsibility |
|---|---|---|
| Create (copy) | `nmlinux-theme/nmlinux/` | Full copy of original source |
| Create | `nmlinux-theme/nmlinux/skin/__init__.py` | Package marker |
| Create | `nmlinux-theme/nmlinux/skin/skin.py` | `load_fonts()` + `apply()` |
| Create | `nmlinux-theme/nmlinux/skin/dark.qss` | Complete dark stylesheet |
| Create | `nmlinux-theme/nmlinux/skin/light.qss` | Placeholder with TODO comments |
| Create | `nmlinux-theme/nmlinux/skin/fonts/Inter/` | Inter TTF files |
| Create | `nmlinux-theme/nmlinux/skin/fonts/JetBrainsMono/` | JetBrains Mono TTF files |
| Modify | `nmlinux-theme/nmlinux/window.py` | Add `GradientWidget`, use it as central widget |
| Modify | `nmlinux-theme/nmlinux/main.py` | Call `skin.load_fonts()` + `skin.apply()` |
| Create | `nmlinux-theme/pyproject.toml` | Project config (name: nmlinux-theme) |
| Create | `nmlinux-theme/run.sh` | `python -m nmlinux.main` launcher |
| Create | `nmlinux-theme/tests/test_skin.py` | Smoke tests (no display needed) |

---

## Task 1: Copy nmlinux source into nmlinux-theme

**Files:**
- Create: `/home/luust/claude-projects/nmlinux-theme/` (from copy of nmlinux)

- [ ] **Step 1: Copy the source**

```bash
cp -r /home/luust/claude-projects/nmlinux /home/luust/claude-projects/nmlinux-theme
```

- [ ] **Step 2: Remove build artifacts and dist from the copy**

```bash
rm -rf /home/luust/claude-projects/nmlinux-theme/dist
rm -rf /home/luust/claude-projects/nmlinux-theme/nmlinux/__pycache__
find /home/luust/claude-projects/nmlinux-theme -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find /home/luust/claude-projects/nmlinux-theme -name "*.pyc" -delete 2>/dev/null || true
```

- [ ] **Step 3: Verify structure**

```bash
ls /home/luust/claude-projects/nmlinux-theme/nmlinux/
```

Expected output includes: `core/  pages/  main.py  window.py  __init__.py`

- [ ] **Step 4: Commit**

```bash
cd /home/luust/claude-projects/nmlinux-theme
git init
git add -A
git commit -m "chore: initial copy of nmlinux source for theme experiment"
```

---

## Task 2: Download font files

**Files:**
- Create: `nmlinux-theme/nmlinux/skin/fonts/Inter/` — Inter-Regular.ttf, Inter-Bold.ttf, Inter-Medium.ttf
- Create: `nmlinux-theme/nmlinux/skin/fonts/JetBrainsMono/` — JetBrainsMono-Regular.ttf, JetBrainsMono-Bold.ttf

- [ ] **Step 1: Create font directories**

```bash
mkdir -p /home/luust/claude-projects/nmlinux-theme/nmlinux/skin/fonts/Inter
mkdir -p /home/luust/claude-projects/nmlinux-theme/nmlinux/skin/fonts/JetBrainsMono
```

- [ ] **Step 2: Download Inter static TTF files**

```bash
BASE="https://github.com/rsms/inter/raw/main/docs/font-files"
cd /home/luust/claude-projects/nmlinux-theme/nmlinux/skin/fonts/Inter
curl -fLO "${BASE}/Inter-Regular.ttf"
curl -fLO "${BASE}/Inter-Bold.ttf"
curl -fLO "${BASE}/Inter-Medium.ttf"
```

Expected: 3 `.ttf` files, each > 100 KB.

- [ ] **Step 3: Download JetBrains Mono static TTF files**

```bash
BASE="https://github.com/JetBrains/JetBrainsMono/raw/main/fonts/ttf"
cd /home/luust/claude-projects/nmlinux-theme/nmlinux/skin/fonts/JetBrainsMono
curl -fLO "${BASE}/JetBrainsMono-Regular.ttf"
curl -fLO "${BASE}/JetBrainsMono-Bold.ttf"
```

Expected: 2 `.ttf` files, each > 100 KB.

- [ ] **Step 4: Verify font files**

```bash
ls -lh /home/luust/claude-projects/nmlinux-theme/nmlinux/skin/fonts/Inter/
ls -lh /home/luust/claude-projects/nmlinux-theme/nmlinux/skin/fonts/JetBrainsMono/
```

Expected: 5 files total, none zero-size.

- [ ] **Step 5: Commit**

```bash
cd /home/luust/claude-projects/nmlinux-theme
git add nmlinux/skin/fonts/
git commit -m "chore: add Inter and JetBrains Mono font files"
```

---

## Task 3: Create skin module

**Files:**
- Create: `nmlinux-theme/nmlinux/skin/__init__.py`
- Create: `nmlinux-theme/nmlinux/skin/skin.py`

- [ ] **Step 1: Write the failing test**

Create `nmlinux-theme/tests/__init__.py` (empty) and `nmlinux-theme/tests/test_skin.py`:

```python
"""Smoke tests for the skin module — no display required."""
import importlib
import sys
from pathlib import Path

SKIN_DIR = Path(__file__).parent.parent / "nmlinux" / "skin"


def test_skin_module_importable():
    sys.path.insert(0, str(Path(__file__).parent.parent))
    mod = importlib.import_module("nmlinux.skin.skin")
    assert hasattr(mod, "load_fonts")
    assert hasattr(mod, "apply")


def test_dark_qss_exists_and_nonempty():
    qss = SKIN_DIR / "dark.qss"
    assert qss.exists(), "dark.qss missing"
    assert qss.stat().st_size > 100, "dark.qss seems empty"


def test_light_qss_exists():
    qss = SKIN_DIR / "light.qss"
    assert qss.exists(), "light.qss missing"


def test_inter_fonts_present():
    fonts_dir = SKIN_DIR / "fonts" / "Inter"
    ttfs = list(fonts_dir.glob("*.ttf"))
    assert len(ttfs) >= 2, f"Expected ≥2 Inter TTFs, found {len(ttfs)}"


def test_jetbrains_fonts_present():
    fonts_dir = SKIN_DIR / "fonts" / "JetBrainsMono"
    ttfs = list(fonts_dir.glob("*.ttf"))
    assert len(ttfs) >= 1, f"Expected ≥1 JetBrainsMono TTF, found {len(ttfs)}"
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd /home/luust/claude-projects/nmlinux-theme
python -m pytest tests/test_skin.py -v 2>&1 | head -30
```

Expected: `test_skin_module_importable` FAILS with `ModuleNotFoundError`.

- [ ] **Step 3: Create `nmlinux/skin/__init__.py`**

```python
```

(empty file — just a package marker)

- [ ] **Step 4: Create `nmlinux/skin/skin.py`**

```python
from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import QApplication

_SKIN_DIR = Path(__file__).parent
_FONTS_DIR = _SKIN_DIR / "fonts"


def load_fonts() -> None:
    from PySide6.QtGui import QFontDatabase
    for ttf in _FONTS_DIR.rglob("*.ttf"):
        QFontDatabase.addApplicationFont(str(ttf))


def apply(app: QApplication, theme: str = "dark") -> None:
    qss_file = _SKIN_DIR / f"{theme}.qss"
    if qss_file.exists():
        app.setStyleSheet(qss_file.read_text(encoding="utf-8"))
    app.setFont(QFont("Inter", 10))
    _apply_palette(app, theme)


def _apply_palette(app: QApplication, theme: str) -> None:
    """Update QPalette so is_dark() / _dark_mode() return the right value."""
    palette = app.palette()
    if theme == "dark":
        dark = QColor("#0d1117")
        light_text = QColor("#e6edf3")
        green = QColor("#238636")
        for group in (QPalette.ColorGroup.All,):
            palette.setColor(group, QPalette.ColorRole.Window, dark)
            palette.setColor(group, QPalette.ColorRole.WindowText, light_text)
            palette.setColor(group, QPalette.ColorRole.Base, dark)
            palette.setColor(group, QPalette.ColorRole.Text, light_text)
            palette.setColor(group, QPalette.ColorRole.Button, green)
            palette.setColor(group, QPalette.ColorRole.ButtonText, QColor("#ffffff"))
            palette.setColor(group, QPalette.ColorRole.Highlight, green)
            palette.setColor(group, QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)
```

- [ ] **Step 5: Run `test_skin_module_importable` (it needs no display)**

```bash
cd /home/luust/claude-projects/nmlinux-theme
python -m pytest tests/test_skin.py::test_skin_module_importable -v
```

Expected: PASS

- [ ] **Step 6: Commit**

```bash
cd /home/luust/claude-projects/nmlinux-theme
git add nmlinux/skin/__init__.py nmlinux/skin/skin.py tests/
git commit -m "feat: add skin module with load_fonts() and apply()"
```

---

## Task 4: Create dark.qss

**Files:**
- Create: `nmlinux-theme/nmlinux/skin/dark.qss`

- [ ] **Step 1: Create `nmlinux/skin/dark.qss`**

```css
/* dark.qss — NMLinux Custom Dark Theme */

/* ── Global ─────────────────────────────────────────────────────── */
QWidget {
    background-color: transparent;
    color: #e6edf3;
    font-family: "Inter";
    font-size: 10pt;
    selection-background-color: #238636;
    selection-color: #ffffff;
}

QMainWindow, QDialog {
    background-color: transparent;
}

/* ── Sidebar nav lists ───────────────────────────────────────────── */
QListWidget {
    background-color: #111718;
    border: none;
    outline: none;
}

QListWidget::item {
    padding: 6px 8px;
    border-radius: 4px;
    color: #c9d1d9;
}

QListWidget::item:hover {
    background-color: #1c2a1c;
}

QListWidget::item:selected {
    background-color: #1a3a1a;
    color: #3fb950;
}

/* ── Frames / separators ─────────────────────────────────────────── */
QFrame[frameShape="4"],
QFrame[frameShape="5"] {
    color: #21262d;
    background-color: #21262d;
}

/* ── Text inputs ─────────────────────────────────────────────────── */
QLineEdit,
QSpinBox,
QDoubleSpinBox,
QComboBox {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 4px;
    padding: 4px 8px;
    color: #e6edf3;
}

QLineEdit:focus,
QSpinBox:focus,
QDoubleSpinBox:focus,
QComboBox:focus {
    border-color: #3fb950;
}

QTextEdit,
QPlainTextEdit {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 4px;
    padding: 4px;
    color: #e6edf3;
    font-family: "JetBrains Mono";
    font-size: 9pt;
}

QTextEdit:focus,
QPlainTextEdit:focus {
    border-color: #3fb950;
}

/* ── Buttons ─────────────────────────────────────────────────────── */
QPushButton {
    background-color: #238636;
    color: #ffffff;
    border: none;
    border-radius: 4px;
    padding: 5px 14px;
    font-family: "Inter";
    font-weight: bold;
}

QPushButton:hover {
    background-color: #2ea043;
}

QPushButton:pressed {
    background-color: #1a7f37;
}

QPushButton:disabled {
    background-color: #21262d;
    color: #8b949e;
}

/* ── Tables ──────────────────────────────────────────────────────── */
QTableWidget,
QTableView {
    background-color: #0d1117;
    alternate-background-color: #111718;
    gridline-color: #21262d;
    border: 1px solid #21262d;
    border-radius: 4px;
}

QHeaderView::section {
    background-color: #161b22;
    color: #8b949e;
    border: none;
    border-bottom: 1px solid #21262d;
    padding: 4px 8px;
    font-weight: bold;
}

QTableWidget::item:selected,
QTableView::item:selected {
    background-color: #1a3a1a;
    color: #3fb950;
}

/* ── Scrollbars ──────────────────────────────────────────────────── */
QScrollBar:vertical {
    background: #0d1117;
    width: 8px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #30363d;
    border-radius: 4px;
    min-height: 24px;
}

QScrollBar::handle:vertical:hover {
    background: #3fb950;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background: #0d1117;
    height: 8px;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background: #30363d;
    border-radius: 4px;
    min-width: 24px;
}

QScrollBar::handle:horizontal:hover {
    background: #3fb950;
}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
    width: 0;
}

/* ── Labels ──────────────────────────────────────────────────────── */
QLabel {
    background-color: transparent;
    color: #e6edf3;
}

/* ── GroupBox ────────────────────────────────────────────────────── */
QGroupBox {
    border: 1px solid #21262d;
    border-radius: 6px;
    margin-top: 14px;
    padding-top: 8px;
    color: #8b949e;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    color: #8b949e;
}

/* ── ComboBox dropdown ───────────────────────────────────────────── */
QComboBox::drop-down {
    border: none;
    width: 22px;
}

QComboBox QAbstractItemView {
    background-color: #161b22;
    border: 1px solid #30363d;
    selection-background-color: #1a3a1a;
    selection-color: #3fb950;
    color: #e6edf3;
}

/* ── CheckBox / RadioButton ──────────────────────────────────────── */
QCheckBox,
QRadioButton {
    color: #c9d1d9;
    spacing: 6px;
    background-color: transparent;
}

QCheckBox::indicator,
QRadioButton::indicator {
    width: 14px;
    height: 14px;
    border: 1px solid #30363d;
    border-radius: 3px;
    background-color: #0d1117;
}

QCheckBox::indicator:checked {
    background-color: #238636;
    border-color: #3fb950;
}

QRadioButton::indicator {
    border-radius: 7px;
}

QRadioButton::indicator:checked {
    background-color: #238636;
    border-color: #3fb950;
}

/* ── TabWidget ───────────────────────────────────────────────────── */
QTabWidget::pane {
    border: 1px solid #21262d;
    background-color: transparent;
}

QTabBar::tab {
    background-color: #111718;
    color: #8b949e;
    padding: 6px 14px;
    border: 1px solid #21262d;
    border-bottom: none;
}

QTabBar::tab:selected {
    background-color: #1a3a1a;
    color: #3fb950;
    border-bottom: 2px solid #3fb950;
}

QTabBar::tab:hover:!selected {
    background-color: #1c2a1c;
    color: #c9d1d9;
}

/* ── ToolTip ─────────────────────────────────────────────────────── */
QToolTip {
    background-color: #161b22;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 4px;
    padding: 4px 8px;
    font-family: "Inter";
    font-size: 9pt;
}

/* ── ProgressBar ─────────────────────────────────────────────────── */
QProgressBar {
    background-color: #0d1117;
    border: 1px solid #21262d;
    border-radius: 4px;
    text-align: center;
    color: #e6edf3;
}

QProgressBar::chunk {
    background-color: #238636;
    border-radius: 4px;
}

/* ── Splitter ────────────────────────────────────────────────────── */
QSplitter::handle {
    background-color: #21262d;
}

/* ── SpinBox arrows ──────────────────────────────────────────────── */
QSpinBox::up-button,
QDoubleSpinBox::up-button,
QSpinBox::down-button,
QDoubleSpinBox::down-button {
    background-color: #21262d;
    border: none;
    width: 16px;
}

QSpinBox::up-button:hover,
QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover,
QDoubleSpinBox::down-button:hover {
    background-color: #30363d;
}

/* ── TreeView (topology page) ────────────────────────────────────── */
QTreeView {
    background-color: #0d1117;
    border: 1px solid #21262d;
    color: #e6edf3;
}

QTreeView::item:selected {
    background-color: #1a3a1a;
    color: #3fb950;
}

QTreeView::item:hover {
    background-color: #1c2a1c;
}
```

- [ ] **Step 2: Run the QSS size check test**

```bash
cd /home/luust/claude-projects/nmlinux-theme
python -m pytest tests/test_skin.py::test_dark_qss_exists_and_nonempty -v
```

Expected: PASS

- [ ] **Step 3: Commit**

```bash
cd /home/luust/claude-projects/nmlinux-theme
git add nmlinux/skin/dark.qss
git commit -m "feat: add full dark QSS stylesheet"
```

---

## Task 5: Create light.qss placeholder

**Files:**
- Create: `nmlinux-theme/nmlinux/skin/light.qss`

- [ ] **Step 1: Create `nmlinux/skin/light.qss`**

```css
/* light.qss — NMLinux Light Theme (placeholder)
 *
 * Colors to decide in a future session.
 * Mirror dark.qss structure — replace each color with a light equivalent.
 *
 * Suggested palette variables (not yet decided):
 *   Window background:        /* TODO */
 *   Primary text:             /* TODO */
 *   Secondary text:           /* TODO */
 *   Sidebar background:       /* TODO */
 *   Sidebar item selected bg: /* TODO */
 *   Sidebar item selected fg: /* TODO */
 *   Input background:         /* TODO */
 *   Input border:             /* TODO */
 *   Input border focus:       /* TODO */
 *   Button background:        /* TODO */
 *   Button hover:             /* TODO */
 *   Accent green:             /* TODO */
 *   Border / separator:       /* TODO */
 */

/* Once colors are decided, copy dark.qss here and replace every hex value. */
```

- [ ] **Step 2: Run the light.qss existence test**

```bash
cd /home/luust/claude-projects/nmlinux-theme
python -m pytest tests/test_skin.py::test_light_qss_exists -v
```

Expected: PASS

- [ ] **Step 3: Commit**

```bash
cd /home/luust/claude-projects/nmlinux-theme
git add nmlinux/skin/light.qss
git commit -m "chore: add light.qss placeholder"
```

---

## Task 6: Modify window.py — add GradientWidget

**Files:**
- Modify: `nmlinux-theme/nmlinux/window.py`

The current `MainWindow.__init__` creates `central = QWidget()` and calls `self.setCentralWidget(central)`. We replace `QWidget` with `GradientWidget` that paints the diagonal gradient.

- [ ] **Step 1: Open `nmlinux-theme/nmlinux/window.py` and add the import at the top**

Find the existing imports block (lines 1–8):
```python
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QListWidgetItem, QStackedWidget, QFrame, QSizePolicy,
    QStyledItemDelegate, QStyle,
)
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPainter, QColor, QFont
```

Replace with:
```python
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QListWidgetItem, QStackedWidget, QFrame, QSizePolicy,
    QStyledItemDelegate, QStyle,
)
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPainter, QColor, QFont, QLinearGradient
```

- [ ] **Step 2: Add the `GradientWidget` class just before `class MainWindow`**

Find `class MainWindow(QMainWindow):` and insert before it:

```python
class GradientWidget(QWidget):
    """Central widget that paints a diagonal dark-green gradient behind all content."""

    _START = QColor("#0d1117")
    _END   = QColor("#0a1a0a")

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0.0, self._START)
        gradient.setColorAt(1.0, self._END)
        painter.fillRect(self.rect(), gradient)


```

- [ ] **Step 3: Replace the central QWidget with GradientWidget inside `MainWindow.__init__`**

Find:
```python
        central = QWidget()
        self.setCentralWidget(central)
```

Replace with:
```python
        central = GradientWidget()
        central.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setCentralWidget(central)
```

- [ ] **Step 4: Verify syntax**

```bash
cd /home/luust/claude-projects/nmlinux-theme
python -c "from nmlinux.window import MainWindow, GradientWidget; print('OK')"
```

Expected: `OK`

- [ ] **Step 5: Commit**

```bash
cd /home/luust/claude-projects/nmlinux-theme
git add nmlinux/window.py
git commit -m "feat: add GradientWidget for diagonal dark-green background"
```

---

## Task 7: Modify main.py — apply the skin

**Files:**
- Modify: `nmlinux-theme/nmlinux/main.py`

- [ ] **Step 1: Open `nmlinux-theme/nmlinux/main.py` and add the skin import after the existing imports**

Find:
```python
def main() -> None:
    app = QApplication(sys.argv)
    _ensure_icon_theme()
```

Replace with:
```python
def main() -> None:
    app = QApplication(sys.argv)
    from nmlinux.skin import skin as _skin
    _skin.load_fonts()
    _skin.apply(app, theme="dark")
    _ensure_icon_theme()
```

- [ ] **Step 2: Verify syntax**

```bash
cd /home/luust/claude-projects/nmlinux-theme
python -c "import nmlinux.main; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Run all smoke tests**

```bash
cd /home/luust/claude-projects/nmlinux-theme
python -m pytest tests/ -v
```

Expected: all 5 tests PASS.

- [ ] **Step 4: Commit**

```bash
cd /home/luust/claude-projects/nmlinux-theme
git add nmlinux/main.py
git commit -m "feat: apply custom skin at startup (dark theme, Inter + JetBrains Mono)"
```

---

## Task 8: Create pyproject.toml and run.sh

**Files:**
- Create: `nmlinux-theme/pyproject.toml`
- Create: `nmlinux-theme/run.sh`

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "nmlinux-theme"
version = "0.1.0"
description = "NMLinux — custom skin experiment (dark green theme)"
requires-python = ">=3.11"
dependencies = [
    "PySide6>=6.6",
    "ptyprocess>=0.7",
]

[project.scripts]
nmlinux-theme = "nmlinux.main:main"

[tool.hatch.build.targets.wheel]
packages = ["nmlinux"]
```

- [ ] **Step 2: Create `run.sh`**

```bash
#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
exec python -m nmlinux.main "$@"
```

- [ ] **Step 3: Make run.sh executable**

```bash
chmod +x /home/luust/claude-projects/nmlinux-theme/run.sh
```

- [ ] **Step 4: Commit**

```bash
cd /home/luust/claude-projects/nmlinux-theme
git add pyproject.toml run.sh
git commit -m "chore: add pyproject.toml and run.sh launcher"
```

---

## Task 9: Visual verification

- [ ] **Step 1: Launch the themed app**

```bash
cd /home/luust/claude-projects/nmlinux-theme
./run.sh
```

- [ ] **Step 2: Verify the following visually**

Checklist:
- [ ] Window background shows a dark gradient (near-black top-left, slight green tint bottom-right)
- [ ] Sidebar text uses Inter font, items highlight green on selection
- [ ] Inputs have dark background with green focus border
- [ ] Buttons are green (`#238636`) with white text
- [ ] SSH terminal and CLI bar at the bottom use JetBrains Mono
- [ ] Scrollbars are slim (8px) and turn green on hover
- [ ] ToolTips appear dark with light text
- [ ] `is_dark()` returns True (CLI bar shows green prompt — confirms palette is correctly set)

- [ ] **Step 3: If visual issues found — adjust `dark.qss` and re-run**

`dark.qss` can be edited and reloaded by restarting `./run.sh`. No recompilation needed.

- [ ] **Step 4: Final commit**

```bash
cd /home/luust/claude-projects/nmlinux-theme
git add -A
git commit -m "chore: theme experiment ready for visual review"
```
