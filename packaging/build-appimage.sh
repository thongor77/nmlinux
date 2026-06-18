#!/usr/bin/env bash
# Build NMLinux-x.y.z-x86_64.AppImage
# Requires: python3, pip, (optionally) rsvg-convert or inkscape for icon generation
# appimagetool is downloaded automatically on first run.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VERSION=$(grep '^version' "$PROJECT_DIR/pyproject.toml" | sed 's/.*"\(.*\)".*/\1/')
APPIMAGE_OUT="$PROJECT_DIR/dist/NMLinux-${VERSION}-x86_64.AppImage"
APPDIR="$SCRIPT_DIR/AppDir"
APPIMAGETOOL="$SCRIPT_DIR/appimagetool-x86_64.AppImage"

echo "==> Building NMLinux ${VERSION} AppImage"

# ── 1. Python build env ───────────────────────────────────────────────────────
VENV="$SCRIPT_DIR/.venv-build"
if [ ! -d "$VENV" ]; then
    python3 -m venv "$VENV"
fi
source "$VENV/bin/activate"
pip install --quiet --upgrade pip
pip install --quiet pyinstaller PySide6 ptyprocess tftpy
pip install --quiet -e "$PROJECT_DIR"

# ── 2. PyInstaller bundle ─────────────────────────────────────────────────────
echo "==> Running PyInstaller..."
pyinstaller --clean --noconfirm \
    "$SCRIPT_DIR/nmlinux.spec" \
    --distpath "$SCRIPT_DIR/dist" \
    --workpath "$SCRIPT_DIR/build"
deactivate

# ── 3. AppDir structure ───────────────────────────────────────────────────────
echo "==> Preparing AppDir..."
rm -rf "$APPDIR"
mkdir -p \
    "$APPDIR/usr/share/applications" \
    "$APPDIR/usr/share/icons/hicolor/256x256/apps"

# Copy entire PyInstaller onedir output
cp -r "$SCRIPT_DIR/dist/nmlinux" "$APPDIR/_app"

# Desktop file (Exec adjusted to bare binary name for AppImage spec)
cp "$PROJECT_DIR/data/nmlinux.desktop" "$APPDIR/usr/share/applications/nmlinux.desktop"
sed -i 's|^Exec=.*|Exec=nmlinux|; s|^Icon=.*|Icon=nmlinux|' \
    "$APPDIR/usr/share/applications/nmlinux.desktop"

# ── 4. Icon (256×256 PNG required by AppImage spec) ───────────────────────────
ICON_DST="$APPDIR/usr/share/icons/hicolor/256x256/apps/nmlinux.png"
ICON_SRC="$PROJECT_DIR/data/nmlinux.png"
SVG_SRC="$PROJECT_DIR/nmlinux/assets/icons/globe.svg"

if [ -f "$ICON_SRC" ]; then
    cp "$ICON_SRC" "$ICON_DST"
elif command -v rsvg-convert &>/dev/null; then
    rsvg-convert -w 256 -h 256 "$SVG_SRC" -o "$ICON_DST"
elif command -v inkscape &>/dev/null; then
    inkscape --export-type=png --export-width=256 --export-height=256 \
        --export-filename="$ICON_DST" "$SVG_SRC"
elif command -v convert &>/dev/null; then
    convert -background none -resize 256x256 "$SVG_SRC" "$ICON_DST"
else
    echo "WARNING: No icon tool found (rsvg-convert/inkscape/convert)."
    echo "         AppImage will work but show no icon. Place a 256x256 PNG at data/nmlinux.png to fix."
fi

# Root-level symlinks required by AppImage spec
ln -sf "usr/share/applications/nmlinux.desktop" "$APPDIR/nmlinux.desktop"
[ -f "$ICON_DST" ] && ln -sf "usr/share/icons/hicolor/256x256/apps/nmlinux.png" "$APPDIR/nmlinux.png"

# ── 5. AppRun ─────────────────────────────────────────────────────────────────
cat > "$APPDIR/AppRun" << 'EOF'
#!/bin/bash
SELF="$(readlink -f "$0")"
HERE="${SELF%/*}"
export QT_PLUGIN_PATH="$HERE/_app/PySide6/Qt/plugins${QT_PLUGIN_PATH:+:$QT_PLUGIN_PATH}"
exec "$HERE/_app/nmlinux" "$@"
EOF
chmod +x "$APPDIR/AppRun"

# ── 6. appimagetool ───────────────────────────────────────────────────────────
if [ ! -f "$APPIMAGETOOL" ]; then
    echo "==> Downloading appimagetool..."
    wget -q \
        "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage" \
        -O "$APPIMAGETOOL"
    chmod +x "$APPIMAGETOOL"
fi

# ── 7. Pack ───────────────────────────────────────────────────────────────────
echo "==> Packing AppImage..."
mkdir -p "$PROJECT_DIR/dist"
ARCH=x86_64 "$APPIMAGETOOL" "$APPDIR" "$APPIMAGE_OUT"

echo ""
echo "Done: $APPIMAGE_OUT"
echo "sha256: $(sha256sum "$APPIMAGE_OUT" | cut -d' ' -f1)"
