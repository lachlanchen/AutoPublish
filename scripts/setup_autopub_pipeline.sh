#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR_DEFAULT="$(cd "$SCRIPT_DIR/.." && pwd)"

export AUTOPUB_USER="${AUTOPUB_USER:-lachlan}"
export AUTOPUB_REPO="${AUTOPUB_REPO:-$REPO_DIR_DEFAULT}"

if [[ "$EUID" -ne 0 ]]; then
  echo "Run with: sudo -E $0"
  exit 1
fi

"$SCRIPT_DIR/setup_envs.sh"
"$SCRIPT_DIR/setup_virtual_desktop_service.sh"
"$SCRIPT_DIR/download_and_setup_driver.sh"
"$SCRIPT_DIR/setup_autopub_service.sh"

echo "AutoPublish pipeline setup complete."
echo ""
echo "Next steps:"
echo "- Set a VNC password in /etc/default/autopub (AUTOPUB_VNC_PASSWORD=...), then: sudo systemctl restart virtual-desktop.service"
echo "- Check services: systemctl status virtual-desktop.service autopub.service"
echo "- Check ports: sudo ss -ltnp | grep 590"
