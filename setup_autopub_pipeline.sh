#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export AUTOPUB_USER="${AUTOPUB_USER:-lachlan}"
export AUTOPUB_REPO="${AUTOPUB_REPO:-$SCRIPT_DIR}"

if [[ "$EUID" -ne 0 ]]; then
  echo "Run with: sudo -E $SCRIPT_DIR/$(basename "$0")"
  exit 1
fi

"$SCRIPT_DIR/setup_envs.sh"
"$SCRIPT_DIR/setup_virtual_desktop_service.sh"
"$SCRIPT_DIR/download_and_setup_driver.sh"
"$SCRIPT_DIR/setup_autopub_service.sh"

echo "AutoPublish pipeline setup complete."
