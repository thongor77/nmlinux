#!/usr/bin/env bash
set -e
cd "$(dirname "${BASH_SOURCE[0]}")"
exec python3 -m nmlinux.main "$@"
