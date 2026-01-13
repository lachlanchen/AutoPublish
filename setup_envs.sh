#!/usr/bin/env bash
set -euo pipefail

TARGET_USER="${AUTOPUB_USER:-lachlan}"
REPO_DIR="${AUTOPUB_REPO:-/home/lachlan/ProjectsLFS/LazyEdit/AutoPublish}"
VENV_DIR="/home/${TARGET_USER}/venvs/autopub"

if [[ "$EUID" -ne 0 ]]; then
  echo "Please run as root: sudo $0"
  exit 1
fi

apt-get update
apt-get install -y \
  tmux \
  feh \
  openbox \
  xvfb \
  x11vnc \
  xauth \
  x11-xserver-utils \
  unzip \
  zip \
  chromium \
  chromium-driver \
  python3-venv \
  python3-pip

mkdir -p "/home/${TARGET_USER}/venvs"
python3 -m venv "$VENV_DIR"

"$VENV_DIR/bin/pip" install --upgrade pip wheel
"$VENV_DIR/bin/pip" install -r "$REPO_DIR/requirements.txt"

chown -R "${TARGET_USER}:${TARGET_USER}" "/home/${TARGET_USER}/venvs"

echo "Virtual env created at $VENV_DIR"
