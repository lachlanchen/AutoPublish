#!/usr/bin/env bash
set -euo pipefail

TARGET_USER="${AUTOPUB_USER:-lachlan}"
REPO_DIR="${AUTOPUB_REPO:-/home/lachlan/ProjectsLFS/LazyEdit/AutoPublish}"
VENV_DIR="/home/${TARGET_USER}/venvs/autopub"
SESSION_NAME="autopub"

APP_CMD=("$VENV_DIR/bin/python" "$REPO_DIR/app.py" --refresh-time 1800 --port 8081)

export DISPLAY=":${AUTOPUB_DISPLAY:-1}"

if ! command -v tmux >/dev/null 2>&1; then
  echo "tmux is not installed. Run setup_envs.sh first."
  exit 1
fi

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  echo "Virtual env not found at $VENV_DIR. Run setup_envs.sh first."
  exit 1
fi

if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
  tmux kill-session -t "$SESSION_NAME"
fi

tmux new-session -d -s "$SESSION_NAME" "${APP_CMD[*]}"

echo "Started tmux session '$SESSION_NAME' running: ${APP_CMD[*]}"
