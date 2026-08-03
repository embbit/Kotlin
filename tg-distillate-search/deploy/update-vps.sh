#!/bin/bash
# Run this ON the VPS to pull latest bot code and restart.
# Usage (on VPS): bash /opt/distillate/tg-distillate-search/deploy/update-vps.sh
set -euo pipefail

DEST="/opt/distillate/tg-distillate-search"
BRANCH="cursor/tg-distillate-import-e619"
REPO="https://github.com/embbit/Kotlin.git"
WORKDIR="$(mktemp -d)"

cleanup() { rm -rf "$WORKDIR"; }
trap cleanup EXIT

echo "→ Cloning ${REPO} (${BRANCH})"
git clone -b "$BRANCH" --depth 1 "$REPO" "$WORKDIR/repo"

echo "→ Updating ${DEST}"
rsync -av \
  --exclude '.venv' \
  --exclude '__pycache__' \
  --exclude '*.db' \
  --exclude '.env' \
  "$WORKDIR/repo/tg-distillate-search/" "$DEST/"

echo "→ Restarting distillate-bot"
systemctl restart distillate-bot
sleep 1
systemctl is-active distillate-bot
echo "✓ Bot updated and running"
