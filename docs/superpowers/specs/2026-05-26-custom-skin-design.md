# NMLinux Custom Skin — Design Spec
Date: 2026-05-26

## Objective

Create `nmlinux-theme/` — a separate, isolated copy of the nmlinux app with a fully custom visual skin. The original `nmlinux/` is not modified. Goal: experiment with a proprietary dark theme (green gradient, custom fonts) and stub a light theme for future use.

## Approach

**Option chosen: Full copy + QSS overlay**

Copy `nmlinux/` to `nmlinux-theme/`, add a `skin/` module inside it. The skin loads fonts, applies a QSS stylesheet, and paints a gradient on the window background. Zero risk to the production codebase; divergence is acceptable for a theme experiment.

## Structure

```
nmlinux-theme/
├── nmlinux/
│   ├── core/              # copied as-is from nmlinux
│   ├── pages/             # copied as-is from nmlinux
│   ├── skin/
│   │   ├── __init__.py
│   │   ├── skin.py        # load_fonts() + apply(app, theme)
│   │   ├── dark.qss       # full dark stylesheet
│   │   ├── light.qss      # placeholder with TODO comments
│   │   └── fonts/
│   │       ├── Inter/     # Inter TTF files
│   │       └── JetBrainsMono/  # JetBrains Mono TTF files
│   ├── main.py            # calls skin.load_fonts() + skin.apply()
│   └── window.py          # GradientWidget central widget
├── pyproject.toml
└── run.sh
```

## Theme — Dark

### Gradient (full window)
- Direction: diagonal top-left → bottom-right
- Start: `#0d1117` (near-black)
- End: `#0a1a0a` (near-black with deep forest green tint)
- Implemented via `paintEvent` on `GradientWidget` (QSS cannot reliably cover the full window)

### Sidebar
| Element | Color |
|---|---|
| Background | `#111718` |
| Item hover | `#1c2a1c` |
| Item selected (background) | `#1a3a1a` |
| Item selected (text) | `#3fb950` |
| Normal text | `#c9d1d9` |

### Content area
| Element | Color |
|---|---|
| Primary text | `#e6edf3` |
| Secondary text | `#8b949e` |
| Borders / separators | `#21262d` |
| Input background | `#0d1117` |
| Input border | `#30363d` |
| Input border (focus) | `#3fb950` |

### Accents
| Element | Color |
|---|---|
| Primary green (CTA buttons, selection) | `#3fb950` |
| Button background | `#238636` |
| Button hover | `#2ea043` |

### CLI bar (bottom strip)
- Background: `#0d1117`
- Text: `#3fb950`
- Style: terminal aesthetic

## Theme — Light

Placeholder only. `light.qss` contains commented-out color variables. Colors to be decided in a future session. Structure mirrors `dark.qss` for easy completion.

## Typography

| Use | Font | Size |
|---|---|---|
| UI labels, buttons, lists | Inter | 10pt |
| Page section titles | Inter Bold | 11pt |
| SSH terminal | JetBrains Mono | 9pt |
| CLI bar | JetBrains Mono | 9pt |
| Tous les `QPlainTextEdit` / `QTextEdit` (ping, MTR, traceroute…) | JetBrains Mono | 9pt |

Fonts bundled in `skin/fonts/`, loaded via `QFontDatabase.addApplicationFont()`. `QApplication.setFont(QFont("Inter", 10))` set globally. Mono font applied to `QPlainTextEdit` widgets via QSS.

## Implementation Details

### `skin/skin.py`
```python
def load_fonts() -> None:
    # QFontDatabase.addApplicationFont() for all TTF files in skin/fonts/

def apply(app: QApplication, theme: str = "dark") -> None:
    # Load dark.qss or light.qss
    # app.setStyleSheet(qss_content)
    # app.setFont(QFont("Inter", 10))
```

### `window.py` — GradientWidget
- Central widget subclasses `QWidget`
- Overrides `paintEvent` to draw `QLinearGradient(topLeft, bottomRight)`
- `setAttribute(Qt.WA_StyledBackground, True)` preserved so QSS still applies on top

### `main.py`
```python
app = QApplication(sys.argv)
skin.load_fonts()
skin.apply(app, theme="dark")
# ... rest of startup unchanged
win = MainWindow()
win.show()
```

### `run.sh`
```bash
#!/usr/bin/env bash
cd "$(dirname "$0")"
python -m nmlinux.main
```

## Out of Scope

- Light theme colors (deferred)
- Packaging / AUR / Nix for the theme variant
- Merging the skin back into the production `nmlinux/` (separate task once approved)
- Custom window decorations or titlebar
