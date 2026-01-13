#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR_DEFAULT="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_DIR="${AUTOPUB_REPO:-$REPO_DIR_DEFAULT}"
TARGET_USER="${AUTOPUB_USER:-${SUDO_USER:-lachlan}}"

run_as_target_user() {
  if [[ "$EUID" -eq 0 ]]; then
    if command -v sudo >/dev/null 2>&1; then
      sudo -u "$TARGET_USER" -H bash "$@"
    else
      runuser -u "$TARGET_USER" -- bash "$@"
    fi
  else
    bash "$@"
  fi
}

run_as_target_user "$REPO_DIR/scripts/setup_chrome_aliases.sh"
run_as_target_user "$REPO_DIR/scripts/setup_chromium_alias_for_pi.sh"

if [[ "$EUID" -eq 0 ]]; then
  bash "$REPO_DIR/scripts/fix_user_home_permissions.sh"
fi

echo "Chromium driver aliases configured."
