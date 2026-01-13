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
TARGET_FILE="${TARGET_DIR}/sourced_chrome_aliases.sh"

mkdir -p "${TARGET_DIR}"

mkdir -p "${HOME}/chrome_dev_session_logs"
mkdir -p "${HOME}/chrome_dev_session_5003"
mkdir -p "${HOME}/chrome_dev_session_5004"
mkdir -p "${HOME}/chrome_dev_session_5005"
mkdir -p "${HOME}/chrome_dev_session_5006"
mkdir -p "${HOME}/chrome_dev_session_5007"
mkdir -p "${HOME}/chrome_dev_session_9222"

chmod 755 "${HOME}/chrome_dev_session_logs"
chmod 700 "${HOME}/chrome_dev_session_5003"
chmod 700 "${HOME}/chrome_dev_session_5004"
chmod 700 "${HOME}/chrome_dev_session_5005"
chmod 700 "${HOME}/chrome_dev_session_5006"
chmod 700 "${HOME}/chrome_dev_session_5007"
chmod 700 "${HOME}/chrome_dev_session_9222"

if [ -f "${TARGET_FILE}" ]; then
  backup_name="sourced_chrome_aliases.sh.bak.$(date +%Y%m%d_%H%M%S)"
  cp "${TARGET_FILE}" "${TARGET_DIR}/${backup_name}"
fi

cat > "${TARGET_FILE}" <<'EOF'
# Chrome aliases for various platforms
# Created: April 19, 2025

mkdir -p "$HOME/chrome_dev_session_logs" "$HOME/chrome_dev_session_5003" "$HOME/chrome_dev_session_5004" \
  "$HOME/chrome_dev_session_5005" "$HOME/chrome_dev_session_5006" "$HOME/chrome_dev_session_5007" \
  "$HOME/chrome_dev_session_9222" 2>/dev/null || true

alias start_chrome_xhs='DISPLAY=:0 google-chrome --hide-crash-restore-bubble --remote-debugging-port=5003 --user-data-dir="$HOME/chrome_dev_session_5003" https://creator.xiaohongshu.com/creator/post > "$HOME/chrome_dev_session_logs/chrome_xhs.log" 2>&1'
alias start_chrome_douyin='DISPLAY=:0 google-chrome --hide-crash-restore-bubble --remote-debugging-port=5004 --user-data-dir="$HOME/chrome_dev_session_5004" https://creator.douyin.com/creator-micro/content/upload > "$HOME/chrome_dev_session_logs/chrome_douyin.log" 2>&1'
alias start_chrome_bilibili='DISPLAY=:0 google-chrome --hide-crash-restore-bubble --remote-debugging-port=5005 --user-data-dir="$HOME/chrome_dev_session_5005" https://member.bilibili.com/platform/upload/video/frame > "$HOME/chrome_dev_session_logs/chrome_bilibili.log" 2>&1'
alias start_chrome_shipinhao='DISPLAY=:0 google-chrome --hide-crash-restore-bubble --remote-debugging-port=5006 --user-data-dir="$HOME/chrome_dev_session_5006" https://channels.weixin.qq.com/post/create > "$HOME/chrome_dev_session_logs/chrome_shipinhao.log" 2>&1'
alias start_chrome_instagram='DISPLAY=:0 google-chrome --hide-crash-restore-bubble --remote-debugging-port=5007 --user-data-dir="$HOME/chrome_dev_session_5007" https://www.instagram.com > "$HOME/chrome_dev_session_logs/chrome_instagram.log" 2>&1'
alias start_chrome_youtube='DISPLAY=:0 google-chrome --hide-crash-restore-bubble --remote-debugging-port=9222 --user-data-dir="$HOME/chrome_dev_session_9222" https://youtube.com/upload > "$HOME/chrome_dev_session_logs/chrome_youtube.log" 2>&1'
alias start_chrome_without_y2b='start_chrome_xhs & start_chrome_douyin & start_chrome_bilibili'
alias start_chrome_all='start_chrome_xhs & start_chrome_douyin & start_chrome_bilibili & start_chrome_shipinhao & start_chrome_instagram & start_chrome_youtube'
EOF

chmod 644 "${TARGET_FILE}"
echo "Updated ${TARGET_FILE}"
