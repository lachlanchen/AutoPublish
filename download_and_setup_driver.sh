#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${AUTOPUB_REPO:-/home/lachlan/ProjectsLFS/LazyEdit/AutoPublish}"

if [[ "$EUID" -ne 0 ]]; then
  echo "Please run as root: sudo $0"
  exit 1
fi

chmod +x "$REPO_DIR/setup_chrome_aliases.sh" "$REPO_DIR/setup_chromium_alias_for_pi.sh"

"$REPO_DIR/setup_chrome_aliases.sh"
"$REPO_DIR/setup_chromium_alias_for_pi.sh"

echo "Chromium driver aliases configured."
