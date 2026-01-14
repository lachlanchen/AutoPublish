#!/usr/bin/env bash
set -euo pipefail

USER_NAME="${AUTOPUB_USER:-lachlan}"
DISPLAY_NUM="${AUTOPUB_DISPLAY:-1}"
ENV_FILE="/etc/default/autopub"
SERVICE_PATH="/etc/systemd/system/autopub-vnc.service"
START_SCRIPT="/usr/local/bin/autopub_start_vnc_virtual.sh"
STOP_SCRIPT="/usr/local/bin/autopub_stop_vnc_virtual.sh"

if [[ "$EUID" -ne 0 ]]; then
  echo "Please run as root: sudo -E $0"
  exit 1
fi

if ! command -v vncserver-virtual >/dev/null 2>&1; then
  echo "RealVNC is not installed. Enable it with: sudo raspi-config -> Interface Options -> VNC"
  exit 1
fi

HOME_DIR="$(getent passwd "$USER_NAME" | cut -d: -f6 || true)"
if [[ -z "$HOME_DIR" || ! -d "$HOME_DIR" ]]; then
  echo "Could not resolve home directory for user: $USER_NAME"
  exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
  cat > "$ENV_FILE" <<ENV
# AutoPublish service environment
AUTOPUB_DISPLAY=${DISPLAY_NUM}
ENV
  chmod 600 "$ENV_FILE"
elif ! grep -q "^AUTOPUB_DISPLAY=" "$ENV_FILE"; then
  echo "AUTOPUB_DISPLAY=${DISPLAY_NUM}" >> "$ENV_FILE"
fi

VNC_DIR="${HOME_DIR}/.vnc"
XSTARTUP_PATH="${VNC_DIR}/xstartup"
mkdir -p "$VNC_DIR"

if [[ -f "$XSTARTUP_PATH" ]]; then
  backup_name="xstartup.bak.$(date +%Y%m%d_%H%M%S)"
  cp "$XSTARTUP_PATH" "${VNC_DIR}/${backup_name}"
fi

cat > "$XSTARTUP_PATH" <<'EOF'
#!/bin/sh

unset SESSION_MANAGER
unset DBUS_SESSION_BUS_ADDRESS

eval "$(dbus-launch --sh-syntax)"

export XDG_RUNTIME_DIR="/tmp/xdg-$USER"
mkdir -p "$XDG_RUNTIME_DIR"
chmod 700 "$XDG_RUNTIME_DIR"

xfsettingsd &
xfce4-panel &
xfdesktop &
exec xfwm4
EOF

chmod 755 "$XSTARTUP_PATH"
chown -R "${USER_NAME}:${USER_NAME}" "$VNC_DIR"

cat > "$START_SCRIPT" <<'SCRIPT'
#!/usr/bin/env bash
set -euo pipefail

DISPLAY_NUM="${AUTOPUB_DISPLAY:-1}"
PORT="$((5900 + DISPLAY_NUM))"

if command -v ss >/dev/null 2>&1; then
  if ss -ltn "sport = :$PORT" | awk 'NR>1 {found=1} END{exit !found}'; then
    exit 0
  fi
fi

exec vncserver-virtual ":${DISPLAY_NUM}"
SCRIPT

cat > "$STOP_SCRIPT" <<'SCRIPT'
#!/usr/bin/env bash
set -euo pipefail

DISPLAY_NUM="${AUTOPUB_DISPLAY:-1}"
vncserver-virtual -kill ":${DISPLAY_NUM}" 2>/dev/null || true
SCRIPT

chmod 755 "$START_SCRIPT" "$STOP_SCRIPT"

cat > "$SERVICE_PATH" <<SERVICE
[Unit]
Description=AutoPublish RealVNC virtual desktop
After=network.target

[Service]
Type=oneshot
User=${USER_NAME}
EnvironmentFile=-${ENV_FILE}
Environment=AUTOPUB_DISPLAY=${DISPLAY_NUM}
ExecStart=${START_SCRIPT}
ExecStop=${STOP_SCRIPT}
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl disable --now virtual-desktop.service 2>/dev/null || true
systemctl enable --now autopub-vnc.service

echo "autopub-vnc.service installed and started."
