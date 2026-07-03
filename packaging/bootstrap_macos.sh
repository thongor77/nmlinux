#!/usr/bin/env bash
# One-shot macOS installer for NMLinux — installs everything from a bare
# system: Xcode Command Line Tools, Homebrew, system tools, then NMLinux
# itself via install_macos_app.sh.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/thongor77/nmlinux/main/packaging/bootstrap_macos.sh | bash
#
# Re-running is safe: each step is skipped if already satisfied, and the
# NMLinux checkout is updated (git pull) instead of re-cloned.
#
# Pass --system to install NMLinux.app into /Applications instead of
# ~/Applications, e.g.:
#   curl -fsSL .../bootstrap_macos.sh | bash -s -- --system

set -euo pipefail

REPO_URL="https://github.com/thongor77/nmlinux.git"
SRC_DIR="${HOME}/.local/share/nmlinux/src"

echo "== NMLinux macOS bootstrap =="

# --- 1. Xcode Command Line Tools (provides git + cc) ---
if ! xcode-select -p &>/dev/null; then
    echo "Xcode Command Line Tools not found — requesting install (a system dialog will appear)..."
    xcode-select --install
    echo "Waiting for the Xcode Command Line Tools install to finish (accept the dialog)..."
    until xcode-select -p &>/dev/null; do
        sleep 5
    done
    echo "Xcode Command Line Tools installed."
else
    echo "Xcode Command Line Tools already present."
fi

# --- 2. Homebrew ---
if ! command -v brew &>/dev/null; then
    echo "Homebrew not found — installing (you will be asked for your password)..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    if [[ -x /opt/homebrew/bin/brew ]]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
    elif [[ -x /usr/local/bin/brew ]]; then
        eval "$(/usr/local/bin/brew shellenv)"
    fi
else
    echo "Homebrew already present."
fi

# --- 3. System tools ---
echo "Installing system tools via Homebrew (nmap, mtr, curl, whois, net-snmp, samba)..."
brew install nmap mtr curl whois net-snmp samba

# --- 4. Clone or update NMLinux ---
if [[ -d "${SRC_DIR}/.git" ]]; then
    echo "Updating existing NMLinux checkout in ${SRC_DIR}..."
    git -C "${SRC_DIR}" pull
else
    echo "Cloning NMLinux into ${SRC_DIR}..."
    mkdir -p "$(dirname "${SRC_DIR}")"
    git clone "${REPO_URL}" "${SRC_DIR}"
fi

# --- 5. Install the app (venv + NMLinux.app) ---
bash "${SRC_DIR}/packaging/install_macos_app.sh" "$@"

echo ""
echo "Done. Launch NMLinux with: open ~/Applications/NMLinux.app"
