#!/usr/bin/env bash
set -e

# ── NMLinux installer ─────────────────────────────────────────────────────────
# Supports: Debian / Ubuntu / Linux Mint / Arch / Fedora / openSUSE
# Creates a venv in ~/.local/share/nmlinux/venv and installs a .desktop entry
# ─────────────────────────────────────────────────────────────────────────────

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$HOME/.local/share/nmlinux/venv"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons/hicolor/256x256/apps"
LAUNCHER="$BIN_DIR/nmlinux"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info()    { echo -e "${CYAN}[nmlinux]${NC} $*"; }
success() { echo -e "${GREEN}[nmlinux]${NC} $*"; }
warn()    { echo -e "${YELLOW}[nmlinux]${NC} $*"; }
die()     { echo -e "${RED}[nmlinux] ERROR:${NC} $*" >&2; exit 1; }

# ── Detect package manager ────────────────────────────────────────────────────
install_sys_deps() {
    if command -v apt-get &>/dev/null; then
        info "Detected apt — installing system dependencies..."
        sudo apt-get update -qq
        sudo apt-get install -y python3-full python3-venv libgl1 libglib2.0-0 \
            libdbus-1-3 libxkbcommon0 libxkbcommon-x11-0 \
            freerdp2-x11 tigervnc-viewer nmap net-tools iputils-ping traceroute
    elif command -v pacman &>/dev/null; then
        info "Detected pacman — use the AUR package instead: yay -S nmlinux"
        warn "Continuing anyway with pip install..."
    elif command -v dnf &>/dev/null; then
        info "Detected dnf — installing system dependencies..."
        sudo dnf install -y python3 python3-virtualenv mesa-libGL dbus-libs \
            freerdp tigervnc nmap net-tools iputils traceroute
    elif command -v zypper &>/dev/null; then
        info "Detected zypper — installing system dependencies..."
        sudo zypper install -y python3 python3-virtualenv libGL1 dbus-1 \
            freerdp tigervnc nmap net-tools iputils traceroute
    else
        warn "Unknown package manager — skipping system dependencies."
        warn "Make sure python3-venv and OpenGL libs are installed."
    fi
}

# ── Reinstall guard ───────────────────────────────────────────────────────────
if [[ -d "$VENV_DIR" ]]; then
    warn "NMLinux is already installed."
    read -rp "Reinstall / update? [y/N] " answer
    [[ "$answer" =~ ^[Yy]$ ]] || { info "Aborted."; exit 0; }
    info "Removing existing venv..."
    rm -rf "$VENV_DIR"
fi

# ── System deps ───────────────────────────────────────────────────────────────
install_sys_deps

# ── Create venv ───────────────────────────────────────────────────────────────
info "Creating virtual environment at $VENV_DIR ..."
mkdir -p "$VENV_DIR"
python3 -m venv "$VENV_DIR"

info "Upgrading pip..."
"$VENV_DIR/bin/pip" install --quiet --upgrade pip

# ── Install nmlinux ───────────────────────────────────────────────────────────
info "Installing NMLinux..."
"$VENV_DIR/bin/pip" install --quiet "$REPO_DIR"

success "NMLinux installed in venv."

# ── Launcher script ───────────────────────────────────────────────────────────
mkdir -p "$BIN_DIR"
cat > "$LAUNCHER" <<EOF
#!/usr/bin/env bash
exec "$VENV_DIR/bin/python" -m nmlinux.main "\$@"
EOF
chmod +x "$LAUNCHER"
info "Launcher created: $LAUNCHER"

# ── .desktop entry ────────────────────────────────────────────────────────────
mkdir -p "$DESKTOP_DIR"

# Copy icon if available in the repo
ICON_NAME="network-wired"
if [[ -f "$REPO_DIR/nmlinux/icons/nmlinux.png" ]]; then
    mkdir -p "$ICON_DIR"
    cp "$REPO_DIR/nmlinux/icons/nmlinux.png" "$ICON_DIR/nmlinux.png"
    ICON_NAME="nmlinux"
fi

cat > "$DESKTOP_DIR/nmlinux.desktop" <<EOF
[Desktop Entry]
Name=NMLinux
GenericName=Network Manager
Comment=Network management tool for Linux
Exec=$LAUNCHER
Icon=$ICON_NAME
Terminal=false
Type=Application
Categories=Network;System;
Keywords=network;wifi;ssh;scan;dns;ping;nmap;
StartupNotify=true
StartupWMClass=nmlinux
EOF

# Ensure ~/.local/bin is in PATH
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    warn "$BIN_DIR is not in your PATH."
    warn "Add this line to your ~/.bashrc or ~/.zshrc:"
    warn "  export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true

echo ""
success "Installation complete!"
echo -e "  Run from terminal : ${CYAN}nmlinux${NC}"
echo -e "  Or launch from    : Applications menu → Network → NMLinux"
echo ""
