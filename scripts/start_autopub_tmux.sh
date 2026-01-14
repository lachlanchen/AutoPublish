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

DISPLAY_NUM="${AUTOPUB_DISPLAY:-1}"
export DISPLAY=":${DISPLAY_NUM}"

if ! command -v tmux >/dev/null 2>&1; then
  echo "tmux is not installed. Run scripts/setup_envs.sh first."
  exit 1
fi

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  echo "Virtual env not found at $VENV_DIR. Run scripts/setup_envs.sh first."
  exit 1
fi

ENV_SETUP_CMD=""
if [[ -f "$ENV_FILE" ]]; then
  ENV_SETUP_CMD="set -a; . \"$ENV_FILE\"; set +a;"
elif [[ -f "$HOME/.bashrc" ]]; then
  ENV_SETUP_CMD="source \"$HOME/.bashrc\" >/dev/null 2>&1;"
fi

if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
  tmux kill-session -t "$SESSION_NAME"
fi

tmux new-session -d -s "$SESSION_NAME" "bash"

SESSION_CMD="export DISPLAY=\":${DISPLAY_NUM}\"; cd \"$REPO_DIR\"; "
if [[ -n "$ENV_SETUP_CMD" ]]; then
  SESSION_CMD+="$ENV_SETUP_CMD "
fi
SESSION_CMD+="${APP_CMD[*]}"

tmux send-keys -t "$SESSION_NAME" "$SESSION_CMD" C-m

echo "Started tmux session '$SESSION_NAME' running: ${APP_CMD[*]}"
