#!/usr/bin/env bash
set -euo pipefail

USER_NAME="${AUTOPUB_USER:-lachlan}"
DISPLAY_NUM="${AUTOPUB_DISPLAY:-1}"
RESOLUTION="${AUTOPUB_RESOLUTION:-1280x720x24}"
VNC_PORT="${AUTOPUB_VNC_PORT:-5901}"
ENV_FILE="/etc/default/autopub"
SERVICE_PATH="/etc/systemd/system/virtual-desktop.service"
START_SCRIPT="/usr/local/bin/start_virtual_desktop.sh"

if [[ "$EUID" -ne 0 ]]; then
  echo "Please run as root: sudo -E $0"
  exit 1
fi

cat > "$START_SCRIPT" <<'SCRIPT'
#!/usr/bin/env bash
set -euo pipefail

DISPLAY_NUM="${AUTOPUB_DISPLAY:-1}"
RESOLUTION="${AUTOPUB_RESOLUTION:-1280x720x24}"
VNC_PORT="${AUTOPUB_VNC_PORT:-5901}"
VNC_PASSWORD="${AUTOPUB_VNC_PASSWORD:-}"

export DISPLAY=":${DISPLAY_NUM}"

/usr/bin/Xvfb "$DISPLAY" -screen 0 "$RESOLUTION" -ac -nolisten tcp &
XVFB_PID=$!

sleep 1

VNC_ARGS=(-display "$DISPLAY" -forever -shared -rfbport "$VNC_PORT" -auth guess)
if [[ -n "$VNC_PASSWORD" ]]; then
  mkdir -p "$HOME/.vnc"
  x11vnc -storepasswd "$VNC_PASSWORD" "$HOME/.vnc/passwd"
  VNC_ARGS+=(-rfbauth "$HOME/.vnc/passwd")
else
  VNC_ARGS+=(-nopw)
fi

if command -v x11vnc >/dev/null 2>&1; then
  /usr/bin/x11vnc "${VNC_ARGS[@]}" &
fi

if command -v openbox-session >/dev/null 2>&1; then
  exec openbox-session
fi

wait "$XVFB_PID"
SCRIPT

chmod +x "$START_SCRIPT"

cat > "$SERVICE_PATH" <<SERVICE
[Unit]
Description=Virtual Desktop (Xvfb) for AutoPublish
After=network.target

[Service]
Type=simple
User=${USER_NAME}
EnvironmentFile=-${ENV_FILE}
Environment=AUTOPUB_DISPLAY=${DISPLAY_NUM}
Environment=AUTOPUB_RESOLUTION=${RESOLUTION}
Environment=AUTOPUB_VNC_PORT=${VNC_PORT}
ExecStart=${START_SCRIPT}
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable --now virtual-desktop.service

echo "virtual-desktop.service installed and started."
