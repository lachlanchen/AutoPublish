#!/usr/bin/env bash
set -euo pipefail

detect_target_user() {
  if [[ -n "${AUTOPUB_USER:-}" ]]; then
    echo "$AUTOPUB_USER"
    return
  fi
  if [[ -n "${SUDO_USER:-}" && "${SUDO_USER}" != "root" ]]; then
    echo "$SUDO_USER"
    return
  fi
  id -un
}

TARGET_USER="$(detect_target_user)"

if [[ "$EUID" -eq 0 ]]; then
  if [[ "$TARGET_USER" == "root" ]]; then
    echo "Refusing to write aliases into /root. Set AUTOPUB_USER to a non-root user."
    exit 1
  fi
  if command -v sudo >/dev/null 2>&1; then
    exec sudo -u "$TARGET_USER" -H AUTOPUB_USER="$TARGET_USER" bash "$0" "$@"
  fi
  exec runuser -u "$TARGET_USER" -- env AUTOPUB_USER="$TARGET_USER" HOME="/home/$TARGET_USER" bash "$0" "$@"
fi

TARGET_DIR="${HOME}/scripts"
TARGET_FILE="${TARGET_DIR}/sourced_chromium_aliases.sh"
BASHRC_FILE="${HOME}/.bashrc"

mkdir -p "${TARGET_DIR}"

mkdir -p "${HOME}/chromium_dev_session_logs"
mkdir -p "${HOME}/chromium_dev_session_5003"
mkdir -p "${HOME}/chromium_dev_session_5004"
mkdir -p "${HOME}/chromium_dev_session_5005"
mkdir -p "${HOME}/chromium_dev_session_5006"
mkdir -p "${HOME}/chromium_dev_session_5007"
mkdir -p "${HOME}/chromium_dev_session_9222"

chmod 755 "${HOME}/chromium_dev_session_logs"
chmod 700 "${HOME}/chromium_dev_session_5003"
chmod 700 "${HOME}/chromium_dev_session_5004"
chmod 700 "${HOME}/chromium_dev_session_5005"
chmod 700 "${HOME}/chromium_dev_session_5006"
chmod 700 "${HOME}/chromium_dev_session_5007"
chmod 700 "${HOME}/chromium_dev_session_9222"

if [ -f "${TARGET_FILE}" ]; then
  backup_name="sourced_chromium_aliases.sh.bak.$(date +%Y%m%d_%H%M%S)"
  cp "${TARGET_FILE}" "${TARGET_DIR}/${backup_name}"
fi

cat > "${TARGET_FILE}" <<'EOF'
# Chromium aliases for Raspberry Pi
# Created: April 19, 2025

mkdir -p "$HOME/chromium_dev_session_logs" "$HOME/chromium_dev_session_5003" "$HOME/chromium_dev_session_5004" \
  "$HOME/chromium_dev_session_5005" "$HOME/chromium_dev_session_5006" "$HOME/chromium_dev_session_5007" \
  "$HOME/chromium_dev_session_9222" 2>/dev/null || true

CHROMIUM_BIN="${CHROMIUM_BIN:-$(command -v chromium-browser 2>/dev/null || command -v chromium 2>/dev/null)}"
CHROMIUM_FLAGS="--disable-gpu --use-gl=swiftshader --disable-dev-shm-usage"

if [ -z "$CHROMIUM_BIN" ]; then
  echo "Chromium not found. Install with: sudo apt-get install -y chromium" >&2
else
  _chromium_port_open() {
    python3 - "$1" <<'PY' >/dev/null 2>&1
import socket
import sys
with socket.create_connection(("127.0.0.1", int(sys.argv[1])), timeout=1):
    pass
PY
  }

  _start_chromium_session() {
    local name="$1"
    local port="$2"
    local url="$3"
    local profile_dir="$HOME/chromium_dev_session_${port}"
    local log_file="$HOME/chromium_dev_session_logs/chromium_${name}.log"
    mkdir -p "$HOME/chromium_dev_session_logs" "$profile_dir"
    if _chromium_port_open "$port"; then
      echo "Reusing existing Chromium session for ${name} on port ${port} (${profile_dir})."
      return 0
    fi
    DISPLAY=:1 "$CHROMIUM_BIN" $CHROMIUM_FLAGS --hide-crash-restore-bubble \
      --remote-debugging-port="$port" --user-data-dir="$profile_dir" "$url" \
      > "$log_file" 2>&1 &
  }

  start_chromium_xhs() { _start_chromium_session xhs 5003 https://creator.xiaohongshu.com/creator/post; }
  start_chromium_douyin() { _start_chromium_session douyin 5004 https://creator.douyin.com/creator-micro/content/upload; }
  start_chromium_bilibili() { _start_chromium_session bilibili 5005 https://member.bilibili.com/platform/upload/video/frame; }
  start_chromium_shipinhao() { _start_chromium_session shipinhao 5006 https://channels.weixin.qq.com/platform/post/create; }
  start_chromium_instagram() { _start_chromium_session instagram 5007 https://www.instagram.com; }
  start_chromium_youtube() { _start_chromium_session youtube 9222 https://youtube.com/upload; }
fi
start_chromium_without_y2b() {
  start_chromium_xhs
  start_chromium_douyin
  start_chromium_bilibili
}
start_chromium_all() {
  start_chromium_xhs
  start_chromium_douyin
  start_chromium_bilibili
  start_chromium_shipinhao
  start_chromium_instagram
  start_chromium_youtube
}
EOF

chmod 644 "${TARGET_FILE}"

touch "${BASHRC_FILE}"
backup_name=".bashrc.bak.$(date +%Y%m%d_%H%M%S)"
cp "${BASHRC_FILE}" "${HOME}/${backup_name}"
tmp_file="$(mktemp)"
sed -E 's/^([[:space:]]*)alias start_chromium_/\1# alias start_chromium_/' "${BASHRC_FILE}" > "${tmp_file}"
mv "${tmp_file}" "${BASHRC_FILE}"
if ! grep -q "sourced_chromium_aliases.sh" "${BASHRC_FILE}"; then
  {
    echo ""
    echo "# Chromium aliases (AutoPublish)"
    echo ". \"${TARGET_FILE}\""
  } >> "${BASHRC_FILE}"
fi
chmod 644 "${BASHRC_FILE}" || true

echo "Updated ${TARGET_FILE}"
