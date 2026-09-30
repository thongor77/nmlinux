#!/usr/bin/env bash
# Build NMLinux-x.y.z-x86_64.AppImage
# Requires: podman, (optionally) rsvg-convert or inkscape for icon generation
# appimagetool is downloaded automatically on first run.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VERSION=$(grep '^version' "$PROJECT_DIR/pyproject.toml" | sed 's/.*"\(.*\)".*/\1/')
APPIMAGE_OUT="$PROJECT_DIR/dist/NMLinux-${VERSION}-x86_64.AppImage"
APPDIR="$SCRIPT_DIR/AppDir"
APPIMAGETOOL="$SCRIPT_DIR/appimagetool-x86_64.AppImage"

echo "==> Building NMLinux ${VERSION} AppImage"

# ── 1-2. PyInstaller bundle, built inside an old-glibc container ──────────────
# The AppImage must run on distros older than this machine (Arch, rolling
# release). Building locally links the Python interpreter and native
# extensions against glibc symbols newer than what target systems have (e.g.
# the AppImageHub catalog's test machine, Ubuntu 22.04 / glibc 2.35) -- see
# DT-23/DT-24 in docs/Decisions-Techniques.md. Building inside ubuntu:22.04
# itself (Python 3.11 from the deadsnakes PPA, since jammy ships 3.10) matches
# the oldest still-supported Ubuntu LTS, as AppImageHub's own test recommends.
BUILD_IMAGE="docker.io/library/ubuntu:22.04"
echo "==> Running PyInstaller inside $BUILD_IMAGE (podman)..."
podman run --rm \
    -v "$PROJECT_DIR:/work" \
    -w /work \
    -e DEBIAN_FRONTEND=noninteractive \
    "$BUILD_IMAGE" \
    bash -c '
        set -euo pipefail
        apt-get update -qq
        apt-get install -y -qq --no-install-recommends \
            software-properties-common ca-certificates gnupg >/dev/null
        add-apt-repository -y ppa:deadsnakes/ppa >/dev/null
        apt-get update -qq
        apt-get install -y -qq --no-install-recommends \
            python3.11 python3.11-venv python3.11-dev libpython3.11 binutils \
            libgl1 libegl1 libxkbcommon0 libfontconfig1 libdbus-1-3 >/dev/null
        python3.11 -m venv /tmp/venv-build
        . /tmp/venv-build/bin/activate
        pip install --quiet --upgrade pip
        pip install --quiet pyinstaller
        pip install --quiet -e .
        pyinstaller --clean --noconfirm \
            packaging/nmlinux.spec \
            --distpath packaging/dist \
            --workpath packaging/build
    '

# ── 3. AppDir structure ───────────────────────────────────────────────────────
echo "==> Preparing AppDir..."
rm -rf "$APPDIR"
mkdir -p \
    "$APPDIR/usr/share/applications" \
    "$APPDIR/usr/share/icons/hicolor/256x256/apps"

# Copy entire PyInstaller onedir output
cp -r "$SCRIPT_DIR/dist/nmlinux" "$APPDIR/_app"

# Drop shared libs that must come from the host, not be bundled. PyInstaller
# collects whatever .so the build machine has; building on Arch (rolling
# release, very recent glibc) ships copies that need glibc symbols (e.g.
# GLIBC_ABI_DT_RELR) newer than older distros have, so the AppImage crashes
# on startup elsewhere even though it links fine locally. These are part of
# every desktop Linux's base X11/fontconfig stack that Qt already links
# against at runtime, so removing the bundled copies just makes the AppImage
# fall back to the host's own — standard practice for AppImages.
BLACKLISTED_LIBS=(
    libstdc++.so.6 libgcc_s.so.1
    libX11.so.6 libX11-xcb.so.1
    libfontconfig.so.1 libfreetype.so.6 libharfbuzz.so.0 libfribidi.so.0
    libexpat.so.1 libuuid.so.1 libcom_err.so.2 libgmp.so.10 libz.so.1
)
for lib in "${BLACKLISTED_LIBS[@]}"; do
    rm -f "$APPDIR/_app/_internal/$lib"
done

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
