#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR_DEFAULT="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_DIR="${AUTOPUB_REPO:-$REPO_DIR_DEFAULT}"

if [[ "$EUID" -ne 0 ]]; then
  echo "Please run as root: sudo -E $0"
  exit 1
fi

chmod +x "$REPO_DIR/scripts/setup_chrome_aliases.sh" "$REPO_DIR/scripts/setup_chromium_alias_for_pi.sh"

"$REPO_DIR/scripts/setup_chrome_aliases.sh"
"$REPO_DIR/scripts/setup_chromium_alias_for_pi.sh"

echo "Chromium driver aliases configured."
