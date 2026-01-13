#!/usr/bin/env bash
set -euo pipefail

USER_NAME="${AUTOPUB_USER:-lachlan}"
DISPLAY_NUM="${AUTOPUB_DISPLAY:-1}"
RESOLUTION="${AUTOPUB_RESOLUTION:-1280x720x24}"
VNC_PORT_DEFAULT="$((5900 + DISPLAY_NUM))"
VNC_PORT="${AUTOPUB_VNC_PORT:-$VNC_PORT_DEFAULT}"
VNC_EXTRA_PORT="${AUTOPUB_VNC_EXTRA_PORT:-5900}"
VNC_AUTH_MODE="${AUTOPUB_VNC_AUTH:-password}"
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
AUTOPUB_VNC_EXTRA_PORT=${VNC_EXTRA_PORT}
AUTOPUB_VNC_AUTH=${VNC_AUTH_MODE}
AUTOPUB_DESKTOP=${DESKTOP_MODE}
# AUTOPUB_VNC_PASSWORD=change_me
ENV
  chmod 600 "$ENV_FILE"
else
  for entry in \
    "AUTOPUB_DISPLAY=${DISPLAY_NUM}" \
    "AUTOPUB_RESOLUTION=${RESOLUTION}" \
    "AUTOPUB_VNC_PORT=${VNC_PORT}" \
    "AUTOPUB_VNC_EXTRA_PORT=${VNC_EXTRA_PORT}" \
    "AUTOPUB_VNC_AUTH=${VNC_AUTH_MODE}" \
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
VNC_PORT_DEFAULT="$((5900 + DISPLAY_NUM))"
VNC_PORT="${AUTOPUB_VNC_PORT:-$VNC_PORT_DEFAULT}"
VNC_EXTRA_PORT="${AUTOPUB_VNC_EXTRA_PORT:-}"
VNC_PASSWORD="${AUTOPUB_VNC_PASSWORD:-}"
VNC_AUTH_MODE="${AUTOPUB_VNC_AUTH:-password}"
DESKTOP_MODE="${AUTOPUB_DESKTOP:-openbox}"
export HOME="${HOME:-/home/$(id -un)}"
export DISPLAY=":${DISPLAY_NUM}"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"

mkdir -p "$XDG_RUNTIME_DIR" "$HOME/.cache" "$HOME/.config" "$HOME/.local/share" "$HOME/.local/state"
chmod 700 "$XDG_RUNTIME_DIR" || true

/usr/bin/Xvfb "$DISPLAY" -screen 0 "$RESOLUTION" -ac -nolisten tcp &
sleep 0.5

for _ in $(seq 1 50); do
  if DISPLAY="$DISPLAY" xset q >/dev/null 2>&1; then
    break
  fi
  sleep 0.1
done

DISPLAY="$DISPLAY" xsetroot -solid "#2e3440" >/dev/null 2>&1 || true

if command -v dbus-launch >/dev/null 2>&1; then
  eval "$(dbus-launch --sh-syntax)" || true
fi

if command -v openbox-session >/dev/null 2>&1; then
  openbox-session &
elif command -v openbox >/dev/null 2>&1; then
  openbox &
fi

AUTH_MODE="$(printf '%s' "$VNC_AUTH_MODE" | tr '[:upper:]' '[:lower:]')"
VNC_AUTH_ARGS=()
case "$AUTH_MODE" in
	  password|pass|pw|1|true|yes|*)
	    if [[ -n "$VNC_PASSWORD" && "$VNC_PASSWORD" != "change_me" ]]; then
	      mkdir -p "$HOME/.vnc"
	      chmod 700 "$HOME/.vnc" || true
	      if ! command -v x11vnc >/dev/null 2>&1; then
	        echo "ERROR: x11vnc is not installed. Run scripts/setup_envs.sh first." >&2
	        exit 1
	      fi
	      x11vnc -storepasswd "$VNC_PASSWORD" "$HOME/.vnc/passwd" >/dev/null
	      chmod 600 "$HOME/.vnc/passwd" || true
	      VNC_AUTH_ARGS+=(-rfbauth "$HOME/.vnc/passwd")
	    else
	      echo "WARN: AUTOPUB_VNC_PASSWORD not set; starting VNC with no password." >&2
      VNC_AUTH_ARGS+=(-nopw)
    fi
    ;;
esac

COMMON_ARGS=(-display "$DISPLAY" -forever -shared -noxdamage -repeat)

if command -v x11vnc >/dev/null 2>&1 && [[ -n "$VNC_EXTRA_PORT" && "$VNC_EXTRA_PORT" != "$VNC_PORT" ]]; then
  /usr/bin/x11vnc "${COMMON_ARGS[@]}" -rfbport "$VNC_EXTRA_PORT" "${VNC_AUTH_ARGS[@]}" &
fi

exec /usr/bin/x11vnc "${COMMON_ARGS[@]}" -rfbport "$VNC_PORT" "${VNC_AUTH_ARGS[@]}"
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
Environment=AUTOPUB_VNC_EXTRA_PORT=${VNC_EXTRA_PORT}
ExecStart=${START_SCRIPT}
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl reset-failed virtual-desktop.service || true
systemctl enable --now virtual-desktop.service

echo "virtual-desktop.service installed and started."
if [[ "$VNC_EXTRA_PORT" == "5900" ]] && systemctl is-active --quiet vncserver-x11-serviced.service 2>/dev/null; then
  echo "NOTE: vncserver-x11-serviced.service is active and may already use port 5900."
  echo "If you want AutoPublish to also listen on 5900, disable it: sudo systemctl disable --now vncserver-x11-serviced.service"
fi
