#!/usr/bin/env bash
# Build NMLinux-x.y.z-x86_64.flatpak — single-file bundle for GitHub Releases.
# Requires: flatpak, flatpak-builder, and these installed from flathub:
#   org.kde.Platform//6.11  org.kde.Sdk//6.11  io.qt.PySide.BaseApp//6.11
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
VERSION=$(grep '^version' "$PROJECT_DIR/pyproject.toml" | sed 's/.*"\(.*\)".*/\1/')
APP_ID="io.github.thongor77.NMLinux"
MANIFEST="$SCRIPT_DIR/${APP_ID}.yml"
REPO_DIR="$SCRIPT_DIR/repo"
BUILD_DIR="$SCRIPT_DIR/build-dir"
BUNDLE_OUT="$PROJECT_DIR/dist/NMLinux-${VERSION}-x86_64.flatpak"

echo "==> Building ${APP_ID} ${VERSION} Flatpak bundle"

flatpak-builder --repo="$REPO_DIR" --force-clean "$BUILD_DIR" "$MANIFEST"

mkdir -p "$PROJECT_DIR/dist"
# --runtime-repo lets `flatpak install NMLinux-*.flatpak` fetch org.kde.Platform
# from Flathub automatically if the user doesn't already have it.
flatpak build-bundle \
    --runtime-repo=https://flathub.org/repo/flathub.flatpakrepo \
    "$REPO_DIR" "$BUNDLE_OUT" "$APP_ID"

echo ""
echo "Done: $BUNDLE_OUT"
echo "sha256: $(sha256sum "$BUNDLE_OUT" | cut -d' ' -f1)"
