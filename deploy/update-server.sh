#!/usr/bin/env bash
# Atualização no servidor (branch development — igual ao fluxo DataWeb)
# cd /opt/apps/scraper/repo && bash deploy/update-server.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

BRANCH="${BRANCH:-development}"

echo "==> git pull ($BRANCH)"
git fetch origin
git checkout "$BRANCH"
git pull origin "$BRANCH"

echo "==> dependências Python"
./venv/bin/pip install -r requirements.txt -q

echo "==> frontend"
if [ -d frontend/dist ] && [ -f frontend/dist/index.html ]; then
  echo "frontend/dist OK"
elif command -v npm >/dev/null 2>&1; then
  bash deploy/build-prod.sh
else
  echo "AVISO: faça npm run build no PC e git push (branch $BRANCH)"
fi

echo "==> reiniciar serviço"
systemctl restart scraper
sleep 2
systemctl status scraper --no-pager || true

echo "==> health"
curl -sf http://127.0.0.1:8001/api/health && echo ""
curl -sf http://127.0.0.1/scraper/api/health && echo "" || true

echo "OK — http://212.47.68.222/scraper/"
