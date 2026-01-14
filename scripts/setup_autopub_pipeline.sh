#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR_DEFAULT="$(cd "$SCRIPT_DIR/.." && pwd)"

export AUTOPUB_USER="${AUTOPUB_USER:-lachlan}"
export AUTOPUB_REPO="${AUTOPUB_REPO:-$REPO_DIR_DEFAULT}"
export AUTOPUB_VNC_MODE="${AUTOPUB_VNC_MODE:-auto}"

if [[ "$EUID" -ne 0 ]]; then
  echo "Run with: sudo -E $0"
  exit 1
fi

"$SCRIPT_DIR/setup_envs.sh"

VNC_MODE_NORM="$(printf '%s' "$AUTOPUB_VNC_MODE" | tr '[:upper:]' '[:lower:]')"
case "$VNC_MODE_NORM" in
  x11vnc)
    "$SCRIPT_DIR/setup_virtual_desktop_service.sh"
    ;;
  realvnc)
    echo "RealVNC mode selected; skipping x11vnc virtual desktop service."
    if systemctl list-unit-files 2>/dev/null | grep -q '^virtual-desktop\.service'; then
      echo "If you previously installed the x11vnc service, disable it: sudo systemctl disable --now virtual-desktop.service"
    fi
    ;;
  auto|*)
    if command -v vncserver-virtual >/dev/null 2>&1; then
      echo "Detected RealVNC (vncserver-virtual); skipping x11vnc virtual desktop service."
      if systemctl list-unit-files 2>/dev/null | grep -q '^virtual-desktop\.service'; then
        echo "If you previously installed the x11vnc service, disable it: sudo systemctl disable --now virtual-desktop.service"
      fi
    else
      "$SCRIPT_DIR/setup_virtual_desktop_service.sh"
    fi
    ;;
esac

"$SCRIPT_DIR/download_and_setup_driver.sh"
"$SCRIPT_DIR/setup_autopub_service.sh"

echo "AutoPublish pipeline setup complete."
echo ""
echo "Next steps:"
if command -v vncserver-virtual >/dev/null 2>&1; then
  echo "- Start an encrypted RealVNC virtual desktop: vncserver-virtual :1  (port 5901)"
else
  echo "- Set a VNC password in /etc/default/autopub (AUTOPUB_VNC_PASSWORD=...), then: sudo systemctl restart virtual-desktop.service"
  echo "- Check services: systemctl status virtual-desktop.service autopub.service"
  echo "- Check ports: sudo ss -ltnp | grep 590"
fi
