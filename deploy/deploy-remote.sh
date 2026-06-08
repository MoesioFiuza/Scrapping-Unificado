#!/usr/bin/env bash
# Sincroniza código para o servidor e reinicia o serviço
# Uso: bash deploy/deploy-remote.sh [user@212.47.68.222]
set -euo pipefail

REMOTE="${1:-root@212.47.68.222}"
APP_DIR="/opt/apps/scraper/repo"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "==> Build frontend (produção /scraper/)"
bash "$ROOT/deploy/build-prod.sh"

echo "==> Enviar ficheiros para ${REMOTE}:${APP_DIR}"
rsync -avz --delete \
    --exclude '.git' \
    --exclude 'venv' \
    --exclude '.venv' \
    --exclude 'node_modules' \
    --exclude 'data/output/*' \
    --exclude 'data/input/*' \
    --exclude '.env' \
    --exclude '__pycache__' \
    --exclude '.vs' \
    "$ROOT/" "${REMOTE}:${APP_DIR}/"

echo "==> Atualizar no servidor (git pull development)"
ssh "$REMOTE" "cd ${APP_DIR} && \
    git fetch origin && git checkout development && git pull origin development && \
    ./venv/bin/pip install -r requirements.txt -q && \
    systemctl restart scraper && \
    systemctl status scraper --no-pager && \
    curl -sf http://127.0.0.1:8001/api/health"

echo "OK — http://212.47.68.222/scraper/"
