#!/usr/bin/env bash
# Instalação no servidor Linux (212.47.68.222)
# Executar como root ou com sudo: bash deploy/install-server.sh
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/scraper-unificado}"
APP_USER="${APP_USER:-www-data}"

echo "==> Instalação em ${APP_DIR}"

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
"$APP_DIR/venv/bin/pip" install -r requirements.txt

# Frontend (se node estiver instalado no servidor)
if command -v npm >/dev/null 2>&1; then
    bash deploy/build-prod.sh
else
    echo "npm não encontrado — copie frontend/dist do build local (deploy/build-prod.sh)"
fi

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
