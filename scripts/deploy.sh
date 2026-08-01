#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="${APP_DIR:-/opt/sportsintel-ai}"
BRANCH="${BRANCH:-main}"

cd "$APP_DIR"
git fetch origin "$BRANCH"
git checkout "$BRANCH"
git pull --ff-only origin "$BRANCH"

docker compose config >/dev/null
docker compose up -d --build --remove-orphans
docker compose ps

curl --fail --silent http://127.0.0.1:${API_PORT:-8300}/health
echo
echo "SportsIntel AI deployment completed."
