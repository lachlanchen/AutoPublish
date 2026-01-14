#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR_DEFAULT="$(cd "$SCRIPT_DIR/.." && pwd)"
TARGET_USER="${AUTOPUB_USER:-lachlan}"
REPO_DIR="${AUTOPUB_REPO:-$REPO_DIR_DEFAULT}"
VENV_DIR="/home/${TARGET_USER}/venvs/autopub"
SESSION_NAME="autopub"
ENV_FILE="${REPO_DIR}/.env"

APP_CMD=("$VENV_DIR/bin/python" "$REPO_DIR/app.py" --refresh-time 1800 --port 8081)

export DISPLAY=":${AUTOPUB_DISPLAY:-1}"

if ! command -v tmux >/dev/null 2>&1; then
  echo "tmux is not installed. Run scripts/setup_envs.sh first."
  exit 1
fi

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  echo "Virtual env not found at $VENV_DIR. Run scripts/setup_envs.sh first."
  exit 1
fi

if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  . "$ENV_FILE"
  set +a
elif [[ -f "$HOME/.bashrc" ]]; then
  while IFS='=' read -r key value; do
    export "$key=$value"
  done < <(bash -c "source \"$HOME/.bashrc\" >/dev/null 2>&1; env")
fi

if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
  tmux kill-session -t "$SESSION_NAME"
fi

tmux new-session -d -s "$SESSION_NAME" "${APP_CMD[*]}"

echo "Started tmux session '$SESSION_NAME' running: ${APP_CMD[*]}"
