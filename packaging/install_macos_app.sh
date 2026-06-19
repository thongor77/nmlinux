#!/usr/bin/env bash
# Creates NMLinux.app in ~/Applications (or /Applications with --system).
# Run from the repo root or after pip install nmlinux.

set -euo pipefail

APP_NAME="NMLinux"
BUNDLE_ID="com.thongor77.nmlinux"
VERSION="1.5.0"
DEST="${HOME}/Applications"

if [[ "${1:-}" == "--system" ]]; then
    DEST="/Applications"
fi

APP="${DEST}/${APP_NAME}.app"
MACOS_DIR="${APP}/Contents/MacOS"
RES_DIR="${APP}/Contents/Resources"

# Resolve the python interpreter: prefer the one that has nmlinux installed.
PYTHON="$(command -v python3)"
if python3 -c "import nmlinux" 2>/dev/null; then
    PYTHON="$(command -v python3)"
elif command -v nmlinux &>/dev/null; then
    # Installed via pip — find the interpreter from the entry-point shebang.
    PYTHON="$(head -1 "$(command -v nmlinux)" | sed 's/#\!//')"
fi

echo "Using Python: ${PYTHON}"
echo "Installing to: ${APP}"

# --- build bundle structure ---
mkdir -p "${MACOS_DIR}" "${RES_DIR}"

# Launcher script
cat > "${MACOS_DIR}/${APP_NAME}" << LAUNCHER
#!/usr/bin/env bash
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
    # Add icon key to plist (append before closing dict)
    sed -i '' 's|</dict>|    <key>CFBundleIconFile</key>  <string>AppIcon</string>\n</dict>|' \
        "${APP}/Contents/Info.plist"
    echo "Icon installed."
fi

# Flush Finder/LaunchServices cache so the icon appears immediately
if command -v /System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister &>/dev/null; then
    /System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister \
        -f "${APP}" 2>/dev/null || true
fi

echo ""
echo "Done. NMLinux.app created in ${DEST}."
echo "Double-click it in Finder, or run: open \"${APP}\""
