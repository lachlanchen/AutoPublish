#!/usr/bin/env bash
set -euo pipefail

USER_NAME="${AUTOPUB_USER:-lachlan}"
DISPLAY_NUM="${AUTOPUB_DISPLAY:-1}"
RESOLUTION="${AUTOPUB_RESOLUTION:-1280x720x24}"
VNC_PORT="${AUTOPUB_VNC_PORT:-5901}"
VNC_AUTH_MODE="${AUTOPUB_VNC_AUTH:-unix}"
ENV_FILE="/etc/default/autopub"
SERVICE_PATH="/etc/systemd/system/virtual-desktop.service"
START_SCRIPT="/usr/local/bin/start_virtual_desktop.sh"

if [[ "$EUID" -ne 0 ]]; then
  echo "Please run as root: sudo -E $0"
  exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
  cat > "$ENV_FILE" <<ENV
# AutoPublish service environment
AUTOPUB_DISPLAY=${DISPLAY_NUM}
AUTOPUB_RESOLUTION=${RESOLUTION}
AUTOPUB_VNC_PORT=${VNC_PORT}
AUTOPUB_VNC_AUTH=${VNC_AUTH_MODE}
# AUTOPUB_VNC_PASSWORD=change_me
ENV
  chmod 600 "$ENV_FILE"
fi

cat > "$START_SCRIPT" <<'SCRIPT'
#!/usr/bin/env bash
set -euo pipefail

DISPLAY_NUM="${AUTOPUB_DISPLAY:-1}"
RESOLUTION="${AUTOPUB_RESOLUTION:-1280x720x24}"
VNC_PORT="${AUTOPUB_VNC_PORT:-5901}"
VNC_PASSWORD="${AUTOPUB_VNC_PASSWORD:-}"
VNC_AUTH_MODE="${AUTOPUB_VNC_AUTH:-unix}"
XAUTHORITY_FILE="${XAUTHORITY:-$HOME/.Xauthority}"

export DISPLAY=":${DISPLAY_NUM}"
export XAUTHORITY="$XAUTHORITY_FILE"

/usr/bin/Xvfb "$DISPLAY" -screen 0 "$RESOLUTION" -ac -nolisten tcp &
XVFB_PID=$!

sleep 1

touch "$XAUTHORITY_FILE"
if command -v xauth >/dev/null 2>&1; then
  xauth -f "$XAUTHORITY_FILE" generate "$DISPLAY" . trusted >/dev/null 2>&1 || true
fi

VNC_ARGS=(-display "$DISPLAY" -forever -shared -rfbport "$VNC_PORT" -auth "$XAUTHORITY_FILE" -noxdamage)

AUTH_MODE="$(printf '%s' "$VNC_AUTH_MODE" | tr '[:upper:]' '[:lower:]')"
case "$AUTH_MODE" in
  unix|user|system)
    VNC_ARGS+=(-unixpw)
    ;;
  password|pass|pw|1|true|yes)
    if [[ -n "$VNC_PASSWORD" ]]; then
      mkdir -p "$HOME/.vnc"
      x11vnc -storepasswd "$VNC_PASSWORD" "$HOME/.vnc/passwd"
      VNC_ARGS+=(-rfbauth "$HOME/.vnc/passwd")
    else
      VNC_ARGS+=(-nopw)
    fi
    ;;
  none|nopw|0|false|no|"")
    VNC_ARGS+=(-nopw)
    ;;
  *)
    VNC_ARGS+=(-nopw)
    ;;
esac

if command -v x11vnc >/dev/null 2>&1; then
  /usr/bin/x11vnc "${VNC_ARGS[@]}" &
fi

if command -v startlxde >/dev/null 2>&1; then
  exec startlxde
fi

if command -v lxsession >/dev/null 2>&1; then
  exec lxsession -s LXDE -e LXDE
fi

if command -v openbox-session >/dev/null 2>&1; then
  if command -v pcmanfm >/dev/null 2>&1; then
    pcmanfm --desktop --profile LXDE &
  fi
  if command -v lxpanel >/dev/null 2>&1; then
    lxpanel --profile LXDE &
  fi
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
