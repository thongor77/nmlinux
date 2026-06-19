#!/usr/bin/env bash
# Creates NMLinux.app in ~/Applications (or /Applications with --system).
# Installs NMLinux into a dedicated venv if not already installed.
# Run from the repo root: bash packaging/install_macos_app.sh

set -euo pipefail

APP_NAME="NMLinux"
BUNDLE_ID="com.thongor77.nmlinux"
VERSION="1.5.0"
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

# --- install nmlinux into a venv if not already importable ---
if ! python3 -c "import nmlinux" 2>/dev/null; then
    echo "NMLinux not found — installing into ${VENV_DIR} ..."
    python3 -m venv "${VENV_DIR}"
    "${VENV_DIR}/bin/pip" install --quiet PySide6 ptyprocess pyte tftpy

    # Install from local source if we are inside the repo, otherwise from PyPI wheel
    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
    REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
    if [[ -f "${REPO_ROOT}/pyproject.toml" ]]; then
        "${VENV_DIR}/bin/pip" install --quiet "${REPO_ROOT}"
    else
        echo "Error: run this script from the nmlinux repo root (pyproject.toml not found)."
        exit 1
    fi
    echo "NMLinux installed."
    PYTHON="${VENV_DIR}/bin/python3"
else
    # Already installed — find which interpreter has it
    if command -v nmlinux &>/dev/null; then
        PYTHON="$(head -1 "$(command -v nmlinux)" | sed 's|#!||')"
    else
        PYTHON="$(command -v python3)"
    fi
fi

# Prefer the venv python when it exists
if [[ -x "${VENV_DIR}/bin/python3" ]]; then
    PYTHON="${VENV_DIR}/bin/python3"
fi

echo "Using Python : ${PYTHON}"
echo "Installing to: ${APP}"

# --- build bundle structure ---
mkdir -p "${MACOS_DIR}" "${RES_DIR}"

# Launcher script — sources the venv if present so Qt libs are found
cat > "${MACOS_DIR}/${APP_NAME}" << LAUNCHER
#!/usr/bin/env bash
if [[ -f "${VENV_DIR}/bin/activate" ]]; then
    source "${VENV_DIR}/bin/activate"
fi
exec "${PYTHON}" -m nmlinux.main "\$@"
LAUNCHER
chmod +x "${MACOS_DIR}/${APP_NAME}"

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

# Copy app icon if an .icns exists next to this script
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [[ -f "${SCRIPT_DIR}/nmlinux.icns" ]]; then
    cp "${SCRIPT_DIR}/nmlinux.icns" "${RES_DIR}/AppIcon.icns"
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
