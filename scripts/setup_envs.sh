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
  vim \
  xfce4 \
  xfce4-terminal \
  dbus-x11 \
  xdotool \
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
  unzip \
  zip \
  chromium \
  chromium-driver \
  python3-venv \
  python3-pip

if command -v chromium >/dev/null 2>&1 && ! command -v chromium-browser >/dev/null 2>&1; then
  ln -sf "$(command -v chromium)" /usr/local/bin/chromium-browser
fi

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

BASHRC_FILE="/home/${TARGET_USER}/.bashrc"
EXT_FILE="/home/${TARGET_USER}/scripts/sourced_bashrc_extension.sh"
if [[ ! -f "$BASHRC_FILE" ]]; then
  touch "$BASHRC_FILE"
  chown "${TARGET_USER}:${TARGET_USER}" "$BASHRC_FILE"
  chmod 644 "$BASHRC_FILE"
fi

mkdir -p "/home/${TARGET_USER}/scripts"
if [[ ! -f "$EXT_FILE" ]]; then
  cat > "$EXT_FILE" <<'EOF'
# AutoPublish bashrc extensions
alias tl="tmux list-sessions"
alias ta="tmux attach -t"
alias tn="tmux new-session -s"
EOF
else
  if ! grep -q 'alias tl="tmux list-sessions"' "$EXT_FILE"; then
    echo 'alias tl="tmux list-sessions"' >> "$EXT_FILE"
  fi
  if ! grep -q 'alias ta="tmux attach -t"' "$EXT_FILE"; then
    echo 'alias ta="tmux attach -t"' >> "$EXT_FILE"
  fi
  if ! grep -q 'alias tn="tmux new-session -s"' "$EXT_FILE"; then
    echo 'alias tn="tmux new-session -s"' >> "$EXT_FILE"
  fi
fi

tmp_file="$(mktemp)"
sed -e '/^# AutoPublish tmux aliases$/d' \
    -e '/^alias tl="tmux list-sessions"$/d' \
    -e '/^alias ta="tmux attach -t"$/d' \
    -e '/^alias tn="tmux new-session -s"$/d' \
    "$BASHRC_FILE" > "$tmp_file"
mv "$tmp_file" "$BASHRC_FILE"

if ! grep -q "sourced_bashrc_extension.sh" "$BASHRC_FILE"; then
  {
    echo ""
    echo "# AutoPublish bashrc extensions"
    echo ". \"${EXT_FILE}\""
  } >> "$BASHRC_FILE"
fi

chown "${TARGET_USER}:${TARGET_USER}" "$BASHRC_FILE"
chown "${TARGET_USER}:${TARGET_USER}" "$EXT_FILE"

ENV_FILE="${REPO_DIR}/.env"
if [[ ! -f "$ENV_FILE" ]]; then
  touch "$ENV_FILE"
fi

for key in \
  FROM_EMAIL \
  TO_EMAIL \
  SENDGRID_API_KEY \
  APP_PASSWORD \
  SMTP_TEST_FROM_EMAIL \
  SMTP_TEST_TO_EMAIL \
  SMTP_TEST_APP_PASSWORD \
  APIKEY_2CAPTCHA \
  TULING_USERNAME \
  TULING_PASSWORD \
  TULING_ID; do
  if ! grep -q "^${key}=" "$ENV_FILE"; then
    echo "${key}=" >> "$ENV_FILE"
  fi
done

chown "${TARGET_USER}:${TARGET_USER}" "$ENV_FILE"
chmod 600 "$ENV_FILE"

echo "Virtual env created at $VENV_DIR"
