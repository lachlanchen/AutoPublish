#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR_DEFAULT="$(cd "$SCRIPT_DIR/.." && pwd)"
USER_NAME="${AUTOPUB_USER:-lachlan}"
REPO_DIR="${AUTOPUB_REPO:-$REPO_DIR_DEFAULT}"
ENV_FILE="/etc/default/autopub"
SERVICE_PATH="/etc/systemd/system/autopub.service"
START_SCRIPT="$REPO_DIR/scripts/start_autopub_tmux.sh"
HOME_PATH="/home/${USER_NAME}"
DISKMECH_PATH="${HOME_PATH}/DiskMech"
AUTOPUB_DATA_PATH="${HOME_PATH}/AutoPublishDATA"
HOME_MOUNT_UNIT="home-${USER_NAME}.mount"
DISKMECH_MOUNT_UNIT="home-${USER_NAME}-DiskMech.mount"
AUTOPUB_DATA_MOUNT_UNIT="home-${USER_NAME}-AutoPublishDATA.mount"

if [[ "$EUID" -ne 0 ]]; then
  echo "Please run as root: sudo -E $0"
  exit 1
fi

if [[ ! -x "$START_SCRIPT" ]]; then
  chmod +x "$START_SCRIPT"
fi

cat > "$SERVICE_PATH" <<SERVICE
[Unit]
Description=AutoPublish tmux service
Wants=network-online.target
After=network-online.target ${HOME_MOUNT_UNIT} ${DISKMECH_MOUNT_UNIT} ${AUTOPUB_DATA_MOUNT_UNIT}
RequiresMountsFor=${HOME_PATH} ${DISKMECH_PATH} ${AUTOPUB_DATA_PATH}

[Service]
Type=oneshot
RemainAfterExit=yes
User=${USER_NAME}
WorkingDirectory=${REPO_DIR}
EnvironmentFile=-${ENV_FILE}
Environment=AUTOPUB_USER=${USER_NAME}
Environment=AUTOPUB_REPO=${REPO_DIR}
Environment=AUTOPUB_DISPLAY=1
ExecStart=${START_SCRIPT}

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable --now autopub.service

echo "autopub.service installed and started."
