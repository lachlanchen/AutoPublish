#!/usr/bin/env bash
set -euo pipefail

TARGET_USER="${AUTOPUB_USER:-${SUDO_USER:-lachlan}}"

if [[ "$EUID" -ne 0 ]]; then
  echo "Please run as root: sudo -E $0"
  exit 1
fi

HOME_DIR="$(getent passwd "$TARGET_USER" | cut -d: -f6 || true)"
if [[ -z "$HOME_DIR" || ! -d "$HOME_DIR" ]]; then
  echo "Could not resolve home directory for user: $TARGET_USER"
  exit 1
fi

fix_file() {
  local path="$1"
  local mode="$2"
  if [[ -f "$path" ]]; then
    chown "${TARGET_USER}:${TARGET_USER}" "$path" || true
    chmod "$mode" "$path" || true
  fi
}

fix_dir() {
  local path="$1"
  local mode="$2"
  if [[ -d "$path" ]]; then
    chown -R "${TARGET_USER}:${TARGET_USER}" "$path" || true
    chmod "$mode" "$path" || true
  fi
}

fix_file "${HOME_DIR}/.bashrc" 644
fix_dir "${HOME_DIR}/scripts" 755
fix_file "${HOME_DIR}/scripts/sourced_chromium_aliases.sh" 644
fix_file "${HOME_DIR}/scripts/sourced_chrome_aliases.sh" 644
fix_dir "${HOME_DIR}/.vnc" 700
fix_file "${HOME_DIR}/.vnc/passwd" 600

if [[ -d "${HOME_DIR}/chromium_dev_session_logs" ]]; then
  chown -R "${TARGET_USER}:${TARGET_USER}" "${HOME_DIR}/chromium_dev_session_logs" || true
  chmod 755 "${HOME_DIR}/chromium_dev_session_logs" || true
fi

for dir in "${HOME_DIR}"/chromium_dev_session_*; do
  [[ -d "$dir" ]] || continue
  chown -R "${TARGET_USER}:${TARGET_USER}" "$dir" || true
  chmod 700 "$dir" || true
done

if [[ -d "${HOME_DIR}/chrome_dev_session_logs" ]]; then
  chown -R "${TARGET_USER}:${TARGET_USER}" "${HOME_DIR}/chrome_dev_session_logs" || true
  chmod 755 "${HOME_DIR}/chrome_dev_session_logs" || true
fi

for dir in "${HOME_DIR}"/chrome_dev_session_*; do
  [[ -d "$dir" ]] || continue
  chown -R "${TARGET_USER}:${TARGET_USER}" "$dir" || true
  chmod 700 "$dir" || true
done

echo "Fixed ownership/permissions for ${TARGET_USER} under ${HOME_DIR}"

