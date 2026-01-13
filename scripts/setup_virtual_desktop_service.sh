#!/usr/bin/env bash
set -euo pipefail

USER_NAME="${AUTOPUB_USER:-lachlan}"
DISPLAY_NUM="${AUTOPUB_DISPLAY:-1}"
RESOLUTION="${AUTOPUB_RESOLUTION:-1280x720x24}"
VNC_PORT="${AUTOPUB_VNC_PORT:-5901}"
VNC_AUTH_MODE="${AUTOPUB_VNC_AUTH:-unix}"
DESKTOP_MODE="${AUTOPUB_DESKTOP:-openbox}"
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
AUTOPUB_DESKTOP=${DESKTOP_MODE}
# AUTOPUB_VNC_PASSWORD=change_me
ENV
  chmod 600 "$ENV_FILE"
else
  for entry in \\
    "AUTOPUB_DISPLAY=${DISPLAY_NUM}" \\
    "AUTOPUB_RESOLUTION=${RESOLUTION}" \\
    "AUTOPUB_VNC_PORT=${VNC_PORT}" \\
    "AUTOPUB_VNC_AUTH=${VNC_AUTH_MODE}" \\
    "AUTOPUB_DESKTOP=${DESKTOP_MODE}"; do
    key="${entry%%=*}"
    if ! grep -q "^${key}=" "$ENV_FILE"; then
      echo "$entry" >> "$ENV_FILE"
    fi
  done
fi

cat > "$START_SCRIPT" <<'SCRIPT'
#!/usr/bin/env bash
set -euo pipefail

DISPLAY_NUM="${AUTOPUB_DISPLAY:-1}"
RESOLUTION="${AUTOPUB_RESOLUTION:-1280x720x24}"
VNC_PORT="${AUTOPUB_VNC_PORT:-5901}"
VNC_PASSWORD="${AUTOPUB_VNC_PASSWORD:-}"
VNC_AUTH_MODE="${AUTOPUB_VNC_AUTH:-unix}"
DESKTOP_MODE="${AUTOPUB_DESKTOP:-openbox}"
XAUTHORITY_FILE="${XAUTHORITY:-$HOME/.Xauthority}"
RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
USER_NAME="$(id -un)"
HOME_DIR="${HOME:-/home/${USER_NAME}}"
CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME_DIR/.config}"
CACHE_HOME="${XDG_CACHE_HOME:-$HOME_DIR/.cache}"
DATA_HOME="${XDG_DATA_HOME:-$HOME_DIR/.local/share}"
STATE_HOME="${XDG_STATE_HOME:-$HOME_DIR/.local/state}"

export HOME="$HOME_DIR"
export DISPLAY=":${DISPLAY_NUM}"
export XAUTHORITY="$XAUTHORITY_FILE"
export XDG_RUNTIME_DIR="$RUNTIME_DIR"
export XDG_CONFIG_HOME="$CONFIG_HOME"
export XDG_CACHE_HOME="$CACHE_HOME"
export XDG_DATA_HOME="$DATA_HOME"
export XDG_STATE_HOME="$STATE_HOME"

/usr/bin/Xvfb "$DISPLAY" -screen 0 "$RESOLUTION" -ac -nolisten tcp &
XVFB_PID=$!

sleep 1

mkdir -p "$RUNTIME_DIR" "$CONFIG_HOME" "$CACHE_HOME" "$DATA_HOME" "$STATE_HOME"
chmod 700 "$RUNTIME_DIR"

touch "$XAUTHORITY_FILE"
if command -v xauth >/dev/null 2>&1; then
  xauth -f "$XAUTHORITY_FILE" generate "$DISPLAY" . trusted >/dev/null 2>&1 || true
fi

if command -v xsetroot >/dev/null 2>&1; then
  xsetroot -solid "#2e3440" || true
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

if command -v dbus-run-session >/dev/null 2>&1; then
  if [[ "$(printf '%s' "$DESKTOP_MODE" | tr '[:upper:]' '[:lower:]')" == "lxde" ]] && command -v startlxde >/dev/null 2>&1; then
    exec dbus-run-session startlxde
  fi

  if command -v openbox-session >/dev/null 2>&1; then
    exec dbus-run-session bash -lc 'pcmanfm --desktop --profile LXDE & lxpanel --profile LXDE & exec openbox-session'
  fi
elif command -v dbus-launch >/dev/null 2>&1; then
  eval "$(dbus-launch --sh-syntax)"
  if [[ "$(printf '%s' "$DESKTOP_MODE" | tr '[:upper:]' '[:lower:]')" == "lxde" ]] && command -v startlxde >/dev/null 2>&1; then
    exec startlxde
  fi
  if command -v openbox-session >/dev/null 2>&1; then
    pcmanfm --desktop --profile LXDE &
    lxpanel --profile LXDE &
    exec openbox-session
  fi
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
systemctl reset-failed virtual-desktop.service || true
systemctl enable --now virtual-desktop.service

echo "virtual-desktop.service installed and started."
