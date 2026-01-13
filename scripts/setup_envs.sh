#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR_DEFAULT="$(cd "$SCRIPT_DIR/.." && pwd)"
TARGET_USER="${AUTOPUB_USER:-lachlan}"
REPO_DIR="${AUTOPUB_REPO:-$REPO_DIR_DEFAULT}"
VENV_DIR="/home/${TARGET_USER}/venvs/autopub"

if [[ "$EUID" -ne 0 ]]; then
  echo "Please run as root: sudo -E $0"
  exit 1
fi

apt-get update
apt-get install -y \
  build-essential \
  python3-dev \
  tmux \
  feh \
  openbox \
  xvfb \
  x11vnc \
  xauth \
  x11-xserver-utils \
  pkg-config \
  ffmpeg \
  libavcodec-dev \
  libavdevice-dev \
  libavfilter-dev \
  libavformat-dev \
  libavutil-dev \
  libswresample-dev \
  libswscale-dev \
  libzbar0 \
  dbus-x11 \
  lxpanel \
  lxsession \
  pcmanfm \
  unzip \
  zip \
  chromium \
  chromium-driver \
  python3-venv \
  python3-pip

mkdir -p "/home/${TARGET_USER}/venvs"
python3 -m venv "$VENV_DIR"

export PIP_CACHE_DIR="/root/.cache/pip"
mkdir -p "$PIP_CACHE_DIR"

"$VENV_DIR/bin/pip" install --upgrade pip wheel

REQ_MODE="${AUTOPUB_REQUIREMENTS:-minimal}"
REQ_FILE_MIN="$REPO_DIR/requirements.autopub.txt"
REQ_FILE_FULL="$REPO_DIR/requirements.txt"

if [[ "$REQ_MODE" == "full" ]]; then
  SKIP_LIST="${AUTOPUB_PIP_EXCLUDE:-arandr==0.1.11 av==10.0.0 cupshelpers==1.0 dbus-python==1.3.2 gpg==1.18.0}"
  TMP_REQ="$(mktemp)"
  trap 'rm -f "$TMP_REQ"' EXIT

  export REQ_FILE="$REQ_FILE_FULL" TMP_REQ SKIP_LIST
  python3 - <<'PY'
import os

req = os.environ["REQ_FILE"]
tmp = os.environ["TMP_REQ"]
skip = {item.strip() for item in os.environ.get("SKIP_LIST", "").split() if item.strip()}

with open(req, "r", encoding="utf-8") as handle:
    lines = handle.readlines()

with open(tmp, "w", encoding="utf-8") as handle:
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            handle.write(line)
            continue
        if stripped in skip:
            continue
        handle.write(line)
PY

  "$VENV_DIR/bin/pip" install -r "$TMP_REQ"
elif [[ -f "$REQ_MODE" ]]; then
  "$VENV_DIR/bin/pip" install -r "$REQ_MODE"
elif [[ -f "$REQ_FILE_MIN" ]]; then
  "$VENV_DIR/bin/pip" install -r "$REQ_FILE_MIN"
else
  echo "No requirements file found. Set AUTOPUB_REQUIREMENTS=full or provide a file path."
  exit 1
fi

chown -R "${TARGET_USER}:${TARGET_USER}" "/home/${TARGET_USER}/venvs"

echo "Virtual env created at $VENV_DIR"
