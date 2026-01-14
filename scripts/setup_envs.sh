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

BIN_DIR="/home/${TARGET_USER}/.local/bin"
WALLPAPER_SCRIPT="${BIN_DIR}/autopub-wallpaper.sh"
DESKTOP_SCRIPT="${BIN_DIR}/autopub-desktop.sh"
mkdir -p "$BIN_DIR"
cat > "$WALLPAPER_SCRIPT" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

if command -v feh >/dev/null 2>&1; then
  for wallpaper in \
    /usr/share/rpd-wallpaper/*.jpg \
    /usr/share/rpd-wallpaper/*.png \
    /usr/share/raspberrypi-artwork/*.jpg \
    /usr/share/raspberrypi-artwork/*.png \
    /usr/share/backgrounds/*.jpg \
    /usr/share/backgrounds/*.png; do
    if [ -f "$wallpaper" ]; then
      feh --bg-fill "$wallpaper"
      exit 0
    fi
  done
fi

command -v xsetroot >/dev/null 2>&1 && xsetroot -solid "#2e3440" || true
EOF

cat > "$DESKTOP_SCRIPT" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

PROFILE="LXDE"
if [ -d /etc/xdg/lxpanel/LXDE-pi ] || [ -d /etc/xdg/pcmanfm/LXDE-pi ]; then
  PROFILE="LXDE-pi"
fi

command -v pcmanfm >/dev/null 2>&1 && pcmanfm --desktop --profile "$PROFILE" &
command -v lxpanel >/dev/null 2>&1 && lxpanel --profile "$PROFILE" &
EOF

chmod +x "$WALLPAPER_SCRIPT" "$DESKTOP_SCRIPT"

OPENBOX_DIR="/home/${TARGET_USER}/.config/openbox"
mkdir -p "$OPENBOX_DIR"
cat > "$OPENBOX_DIR/autostart" <<EOF
# Openbox session helpers
"$WALLPAPER_SCRIPT" &
"$DESKTOP_SCRIPT" &
EOF

LXDE_DIR="/home/${TARGET_USER}/.config/lxsession/LXDE"
mkdir -p "$LXDE_DIR"
cat > "$LXDE_DIR/autostart" <<EOF
@$WALLPAPER_SCRIPT
@$DESKTOP_SCRIPT
EOF

LXDE_PI_DIR="/home/${TARGET_USER}/.config/lxsession/LXDE-pi"
mkdir -p "$LXDE_PI_DIR"
cat > "$LXDE_PI_DIR/autostart" <<EOF
@$WALLPAPER_SCRIPT
@$DESKTOP_SCRIPT
EOF

create_panel_config() {
  local panel_path="$1"
  if [[ -f "$panel_path" ]]; then
    return
  fi
  mkdir -p "$(dirname "$panel_path")"
  cat > "$panel_path" <<'EOF'
Global {
  edge=top
  allign=left
  margin=0
  widthtype=percent
  width=100
  height=28
  transparent=0
  tintcolor=#000000
  alpha=0
  autohide=0
  heightwhenhidden=2
  setdocktype=1
  setpartialstrut=1
  usefontcolor=1
  fontcolor=#ffffff
}

Plugin {
  type = menu
}

Plugin {
  type = taskbar
}

Plugin {
  type = tray
}

Plugin {
  type = clock
  Config {
    ClockFmt=%R
  }
}
EOF
}

create_panel_config "/home/${TARGET_USER}/.config/lxpanel/LXDE/panels/panel"
create_panel_config "/home/${TARGET_USER}/.config/lxpanel/LXDE-pi/panels/panel"

chown -R "${TARGET_USER}:${TARGET_USER}" "/home/${TARGET_USER}/.config" "/home/${TARGET_USER}/.local"

chown -R "${TARGET_USER}:${TARGET_USER}" "/home/${TARGET_USER}/venvs"

VNC_DIR="/home/${TARGET_USER}/.vnc"
mkdir -p "$VNC_DIR"
cat > "$VNC_DIR/xstartup" <<'EOF'
#!/bin/sh
unset SESSION_MANAGER
unset DBUS_SESSION_BUS_ADDRESS
exec dbus-launch --exit-with-session openbox-session
EOF
chmod 755 "$VNC_DIR/xstartup"
chown -R "${TARGET_USER}:${TARGET_USER}" "$VNC_DIR"

echo "Virtual env created at $VENV_DIR"
