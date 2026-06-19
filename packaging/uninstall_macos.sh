#!/usr/bin/env bash
# Removes NMLinux.app and its venv from macOS.

set -euo pipefail

VENV_DIR="${HOME}/.local/share/nmlinux"

removed=0

for app in "/Applications/NMLinux.app" "${HOME}/Applications/NMLinux.app"; do
    if [[ -d "${app}" ]]; then
        echo "Removing ${app} ..."
        rm -rf "${app}"
        removed=1
    fi
done

if [[ -d "${VENV_DIR}" ]]; then
    echo "Removing ${VENV_DIR} ..."
    rm -rf "${VENV_DIR}"
    removed=1
fi

if [[ $removed -eq 0 ]]; then
    echo "Nothing to remove."
else
    echo "Done."
fi
