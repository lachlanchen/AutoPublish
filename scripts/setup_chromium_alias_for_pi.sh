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

CHROMIUM_FLAGS="--disable-gpu --use-gl=swiftshader --disable-dev-shm-usage"

alias start_chromium_xhs='DISPLAY=:1 chromium-browser $CHROMIUM_FLAGS --hide-crash-restore-bubble --remote-debugging-port=5003 --user-data-dir="$HOME/chromium_dev_session_5003" https://creator.xiaohongshu.com/creator/post > "$HOME/chromium_dev_session_logs/chromium_xhs.log" 2>&1'
alias start_chromium_douyin='DISPLAY=:1 chromium-browser $CHROMIUM_FLAGS --hide-crash-restore-bubble --remote-debugging-port=5004 --user-data-dir="$HOME/chromium_dev_session_5004" https://creator.douyin.com/creator-micro/content/upload > "$HOME/chromium_dev_session_logs/chromium_douyin.log" 2>&1'
alias start_chromium_bilibili='DISPLAY=:1 chromium-browser $CHROMIUM_FLAGS --hide-crash-restore-bubble --remote-debugging-port=5005 --user-data-dir="$HOME/chromium_dev_session_5005" https://member.bilibili.com/platform/upload/video/frame > "$HOME/chromium_dev_session_logs/chromium_bilibili.log" 2>&1'
alias start_chromium_shipinhao='DISPLAY=:1 chromium-browser $CHROMIUM_FLAGS --hide-crash-restore-bubble --remote-debugging-port=5006 --user-data-dir="$HOME/chromium_dev_session_5006" https://channels.weixin.qq.com/post/create > "$HOME/chromium_dev_session_logs/chromium_shipinhao.log" 2>&1'
alias start_chromium_instagram='DISPLAY=:1 chromium-browser $CHROMIUM_FLAGS --hide-crash-restore-bubble --remote-debugging-port=5007 --user-data-dir="$HOME/chromium_dev_session_5007" https://www.instagram.com > "$HOME/chromium_dev_session_logs/chromium_instagram.log" 2>&1'
alias start_chromium_youtube='DISPLAY=:1 chromium-browser $CHROMIUM_FLAGS --hide-crash-restore-bubble --remote-debugging-port=9222 --user-data-dir="$HOME/chromium_dev_session_9222" https://youtube.com/upload > "$HOME/chromium_dev_session_logs/chromium_youtube.log" 2>&1'
alias start_chromium_without_y2b='start_chromium_xhs & start_chromium_douyin & start_chromium_bilibili'
alias start_chromium_all='start_chromium_xhs & start_chromium_douyin & start_chromium_bilibili & start_chromium_shipinhao & start_chromium_instagram & start_chromium_youtube'
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
