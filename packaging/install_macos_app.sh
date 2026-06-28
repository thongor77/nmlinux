#!/usr/bin/env bash
# Creates NMLinux.app in ~/Applications (or /Applications with --system).
# Installs NMLinux into a dedicated venv if not already installed.
# Run from the repo root: bash packaging/install_macos_app.sh

set -euo pipefail

APP_NAME="NMLinux"
BUNDLE_ID="com.thongor77.nmlinux"
VERSION="1.6.4"
DEST="${HOME}/Applications"
VENV_DIR="${HOME}/.local/share/nmlinux/venv"

if [[ "${1:-}" == "--system" ]]; then
    DEST="/Applications"
fi

APP="${DEST}/${APP_NAME}.app"
MACOS_DIR="${APP}/Contents/MacOS"
RES_DIR="${APP}/Contents/Resources"

# --- ensure python3 is available ---
if ! command -v python3 &>/dev/null; then
    echo "Error: python3 not found. Install it with: brew install python3"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

if [[ ! -f "${REPO_ROOT}/pyproject.toml" ]]; then
    echo "Error: run this script from the nmlinux repo root (pyproject.toml not found)."
    exit 1
fi

# Always use the venv python as the authoritative interpreter.
python3 -m venv "${VENV_DIR}"
PYTHON="${VENV_DIR}/bin/python3"

# Install/upgrade nmlinux and its dependencies into the venv unconditionally.
echo "Installing NMLinux into ${VENV_DIR} ..."
"${VENV_DIR}/bin/pip" install --quiet --upgrade PySide6 ptyprocess pyte tftpy
"${VENV_DIR}/bin/pip" install --upgrade pyobjc-framework-Cocoa
"${VENV_DIR}/bin/pip" install --quiet --upgrade "${REPO_ROOT}"
echo "NMLinux installed."

echo "Using Python : ${PYTHON}"
echo "Installing to: ${APP}"

# --- build bundle structure ---
mkdir -p "${MACOS_DIR}" "${RES_DIR}"

# Compile a native launcher stub so macOS associates the bundle with the process.
# A bash script as CFBundleExecutable causes the menu bar to show "Python" because
# macOS tracks the interpreter (not the script) as the running application.
# A compiled binary that exec()s into Python preserves the bundle association.
LAUNCHER_SRC="$(mktemp /tmp/nmlinux_launcher_XXXXXX.c)"
cat > "${LAUNCHER_SRC}" << C_EOF
#include <unistd.h>
#include <stdio.h>
int main(void) {
    char *python = "${PYTHON}";
    char *args[] = {"NMLinux", "-m", "nmlinux.main", (char*)0};
    execv(python, args);
    perror("NMLinux: exec failed");
    return 1;
}
C_EOF

if command -v cc &>/dev/null && cc -o "${MACOS_DIR}/${APP_NAME}" "${LAUNCHER_SRC}" 2>/dev/null; then
    rm -f "${LAUNCHER_SRC}"
    echo "Compiled native launcher (menu bar will show NMLinux)."
else
    # Fallback: bash script — menu bar may show Python instead of NMLinux
    rm -f "${LAUNCHER_SRC}"
    cat > "${MACOS_DIR}/${APP_NAME}" << LAUNCHER
#!/usr/bin/env bash
exec "${PYTHON}" -m nmlinux.main "\$@"
LAUNCHER
    chmod +x "${MACOS_DIR}/${APP_NAME}"
    echo "Warning: cc not found — using shell launcher (menu bar may show Python)."
fi

# Info.plist
cat > "${APP}/Contents/Info.plist" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>              <string>${APP_NAME}</string>
    <key>CFBundleDisplayName</key>       <string>${APP_NAME}</string>
    <key>CFBundleExecutable</key>        <string>${APP_NAME}</string>
    <key>CFBundleIdentifier</key>        <string>${BUNDLE_ID}</string>
    <key>CFBundleVersion</key>           <string>${VERSION}</string>
    <key>CFBundleShortVersionString</key><string>${VERSION}</string>
    <key>CFBundlePackageType</key>       <string>APPL</string>
    <key>CFBundleSignature</key>         <string>????</string>
    <key>NSHighResolutionCapable</key>   <true/>
    <key>LSMinimumSystemVersion</key>    <string>12.0</string>
    <key>NSHumanReadableCopyright</key>  <string>GPL-2.0 — thongor77</string>
</dict>
</plist>
PLIST

# --- generate .icns from SVG using macOS built-in tools ---
ICNS_SRC="${SCRIPT_DIR}/nmlinux_icon.svg"
ICNS_OUT="${SCRIPT_DIR}/nmlinux.icns"

if [[ -f "${ICNS_SRC}" ]] && command -v sips &>/dev/null && command -v iconutil &>/dev/null; then
    echo "Generating app icon ..."
    ICONSET="$(mktemp -d)/nmlinux.iconset"
    mkdir -p "${ICONSET}"

    for size in 16 32 64 128 256 512 1024; do
        sips -z "${size}" "${size}" "${ICNS_SRC}" \
             --out "${ICONSET}/icon_${size}x${size}.png" &>/dev/null
    done

    # iconutil expects @2x variants (each is the double-res of the previous slot)
    cp "${ICONSET}/icon_32x32.png"   "${ICONSET}/icon_16x16@2x.png"
    cp "${ICONSET}/icon_64x64.png"   "${ICONSET}/icon_32x32@2x.png"
    cp "${ICONSET}/icon_256x256.png" "${ICONSET}/icon_128x128@2x.png"
    cp "${ICONSET}/icon_512x512.png" "${ICONSET}/icon_256x256@2x.png"
    cp "${ICONSET}/icon_1024x1024.png" "${ICONSET}/icon_512x512@2x.png"
    rm -f "${ICONSET}/icon_64x64.png" "${ICONSET}/icon_1024x1024.png"

    iconutil -c icns "${ICONSET}" -o "${ICNS_OUT}"
    rm -rf "$(dirname "${ICONSET}")"
    echo "Icon generated."
fi

# Install .icns into the bundle
if [[ -f "${ICNS_OUT}" ]]; then
    cp "${ICNS_OUT}" "${RES_DIR}/AppIcon.icns"
    sed -i '' 's|</dict>|    <key>CFBundleIconFile</key>  <string>AppIcon</string>\n</dict>|' \
        "${APP}/Contents/Info.plist"
    echo "Icon installed."
fi

# Flush Finder/LaunchServices cache so the icon appears immediately
LSREGISTER="/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister"
if [[ -x "${LSREGISTER}" ]]; then
    "${LSREGISTER}" -f "${APP}" 2>/dev/null || true
fi

echo ""
echo "Done. NMLinux.app created in ${DEST}."
echo "Double-click it in Finder, or run: open \"${APP}\""
echo ""
echo "To update later: git pull && bash packaging/install_macos_app.sh"
