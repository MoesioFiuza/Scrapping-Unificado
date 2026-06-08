#!/usr/bin/env bash
# Instalação no servidor Linux (212.47.68.222)
# Executar a partir da raiz do repositório: sudo bash deploy/install-server.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP_DIR="${APP_DIR:-/opt/scraper-unificado}"
APP_USER="${APP_USER:-www-data}"

echo "==> Instalação: origem ${ROOT} → ${APP_DIR}"

if [ "$ROOT" != "$APP_DIR" ]; then
    mkdir -p "$APP_DIR"
    rsync -a --exclude venv --exclude node_modules --exclude '.git' --exclude 'data/output' \
        "$ROOT/" "$APP_DIR/"
fi

cd "$APP_DIR"

apt-get update
apt-get install -y python3 python3-venv python3-pip nginx \
    google-chrome-stable chromium-chromedriver \
    postgresql postgresql-contrib \
    curl git

# PostgreSQL — base e utilizador (ajuste a senha)
sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname='scraper'" | grep -q 1 || \
    sudo -u postgres psql -c "CREATE USER scraper WITH PASSWORD 'ALTERAR_SENHA';"
sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='scraper_unificado'" | grep -q 1 || \
    sudo -u postgres psql -c "CREATE DATABASE scraper_unificado OWNER scraper;"

mkdir -p "$APP_DIR"/{data/input,data/output,logs}
if [ ! -f "$APP_DIR/.env" ]; then
    cp deploy/env.production.example "$APP_DIR/.env"
    echo "!! Edite $APP_DIR/.env (SECRET_KEY, DATABASE_URL, senhas)"
fi

python3 -m venv "$APP_DIR/venv"
"$APP_DIR/venv/bin/pip" install --upgrade pip
"$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt"

# Frontend
if [ -d "$APP_DIR/frontend/dist" ] && [ -f "$APP_DIR/frontend/dist/index.html" ]; then
    echo "frontend/dist já presente"
elif command -v npm >/dev/null 2>&1; then
    bash "$APP_DIR/deploy/build-prod.sh"
else
    echo "AVISO: npm não encontrado — faça build local e envie frontend/dist"
fi

"$APP_DIR/venv/bin/python" "$APP_DIR/scripts/migrate_json_to_db.py" 2>/dev/null || true

chown -R "$APP_USER:$APP_USER" "$APP_DIR"

# Systemd
cp deploy/scraper.service /etc/systemd/system/scraper.service
systemctl daemon-reload
systemctl enable scraper
systemctl restart scraper

# Nginx
cp deploy/nginx-scraper.conf /etc/nginx/snippets/scraper.conf
if ! grep -q 'snippets/scraper.conf' /etc/nginx/sites-enabled/default 2>/dev/null; then
    echo "Adicione manualmente ao server block: include /etc/nginx/snippets/scraper.conf;"
fi
nginx -t && systemctl reload nginx

echo ""
echo "Deploy concluído."
echo "  App:    http://212.47.68.222/scraper/"
echo "  Health: http://212.47.68.222/scraper/api/health"
echo "  Logs:   journalctl -u scraper -f"
echo ""
echo "Próximos passos:"
echo "  1. Editar $APP_DIR/.env"
echo "  2. python scripts/migrate_json_to_db.py  (se migrar JSON legado)"
echo "  3. systemctl restart scraper"
