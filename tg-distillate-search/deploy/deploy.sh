#!/bin/bash
# Deploy tg-distillate-search to VPS and restart the bot.
# Usage: ./deploy/deploy.sh user@89.125.75.11
set -euo pipefail

TARGET="${1:?Usage: $0 user@host}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REMOTE_DIR="/opt/distillate/tg-distillate-search"

echo "→ Syncing code to ${TARGET}:${REMOTE_DIR}"
rsync -avz --delete \
  --exclude '.venv' \
  --exclude '__pycache__' \
  --exclude '*.db' \
  --exclude '.env' \
  "${ROOT}/" "${TARGET}:${REMOTE_DIR}/"

echo "→ Restarting distillate-bot"
ssh "${TARGET}" "sudo systemctl restart distillate-bot && sleep 1 && sudo systemctl is-active distillate-bot"
echo "✓ Done"
