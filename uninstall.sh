#!/usr/bin/env bash
# Remove only the managed launcher and native plugin. Personal data stays intact.
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
python3 "$ROOT/generate-theme-wallpaper.py" --remove-launcher
omarchy plugin remove mikelon797.omachroma "$@"
