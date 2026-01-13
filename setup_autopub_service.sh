#!/usr/bin/env bash
set -euo pipefail

USER_NAME="${AUTOPUB_USER:-lachlan}"
REPO_DIR="${AUTOPUB_REPO:-/home/lachlan/ProjectsLFS/LazyEdit/AutoPublish}"
ENV_FILE="/etc/default/autopub"
SERVICE_PATH="/etc/systemd/system/autopub.service"
START_SCRIPT="$REPO_DIR/start_autopub_tmux.sh"

if [[ "$EUID" -ne 0 ]]; then
  echo "Please run as root: sudo $0"
  exit 1
fi

if [[ ! -x "$START_SCRIPT" ]]; then
  chmod +x "$START_SCRIPT"
fi

cat > "$SERVICE_PATH" <<SERVICE
[Unit]
Description=AutoPublish tmux service
After=network.target virtual-desktop.service
Wants=virtual-desktop.service

[Service]
Type=simple
User=${USER_NAME}
WorkingDirectory=${REPO_DIR}
EnvironmentFile=-${ENV_FILE}
Environment=AUTOPUB_USER=${USER_NAME}
Environment=AUTOPUB_REPO=${REPO_DIR}
Environment=AUTOPUB_DISPLAY=1
ExecStart=${START_SCRIPT}
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable --now autopub.service

echo "autopub.service installed and started."
