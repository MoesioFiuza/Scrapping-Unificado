import sys
import os
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler

root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from flask import Flask, render_template, session, redirect, url_for, send_from_directory, abort, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix

load_dotenv()

from config.settings import (
    APPLICATION_ROOT,
    DATABASE_URL,
    DATA_DIR,
    IS_PRODUCTION,
)
from app.extensions import db, migrate
from app.db.bootstrap import init_database


def public_url(path: str = '/') -> str:
    """URL pública com prefixo APPLICATION_ROOT (ex.: /scraper/login)."""
    p = path if path.startswith('/') else f'/{path}'
    if APPLICATION_ROOT:
        if p == '/':
            return f'{APPLICATION_ROOT}/'
        return f'{APPLICATION_ROOT}{p}'
    return p

FRONTEND_DIST = root_dir / 'frontend' / 'dist'
USE_SPA = FRONTEND_DIST.is_dir() and (FRONTEND_DIST / 'index.html').is_file()

# Criar diretório de logs se não existir (com tratamento de erro)
logs_dir = root_dir / 'logs'
try:
    logs_dir.mkdir(exist_ok=True)
except (OSError, PermissionError) as e:
    # Se não conseguir criar o diretório, usar apenas console handler
    print(f"Aviso: Não foi possível criar diretório de logs: {e}")
    logs_dir = None

# Configurar logging estruturado
handlers = [logging.StreamHandler(sys.stdout)]

if logs_dir:
    try:
        handlers.append(
            RotatingFileHandler(
                logs_dir / 'app.log',
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
        )
    except (OSError, PermissionError) as e:
        print(f"Aviso: Não foi possível criar arquivo de log: {e}")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=handlers
)

# Suprimir logs muito verbosos de bibliotecas externas
logging.getLogger('selenium').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('webdriver_manager').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
logger.info("Aplicação iniciando...")

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
CORS(app)

app.config['UPLOAD_FOLDER'] = 'data/input'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

if APPLICATION_ROOT:
    app.config['APPLICATION_ROOT'] = APPLICATION_ROOT
    app.config['SESSION_COOKIE_PATH'] = APPLICATION_ROOT

if IS_PRODUCTION:
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    # Ativar SESSION_COOKIE_SECURE=True quando HTTPS estiver activo
    if os.getenv('SESSION_COOKIE_SECURE', '').lower() == 'true':
        app.config['SESSION_COOKIE_SECURE'] = True

DATA_DIR.mkdir(parents=True, exist_ok=True)
db.init_app(app)
migrate.init_app(app, db)

# Usar caminhos absolutos baseados no root_dir para garantir funcionamento no servidor
app.template_folder = str(root_dir / 'templates')
app.static_folder = str(root_dir / 'app' / 'static')
app.static_url_path = '/static'

# Registrar blueprints com tratamento de erro
try:
    from app.routes import upload, processos, resultados, auth, admin, extracoes, dataweb
    
    app.register_blueprint(upload.bp)
    app.register_blueprint(processos.bp)
    app.register_blueprint(resultados.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(extracoes.bp)
    app.register_blueprint(dataweb.bp)
    
    logger.info("Blueprints registrados com sucesso")
except Exception as e:
    logger.error(f"Erro ao registrar blueprints: {e}", exc_info=True)
    raise

init_database(app)

if USE_SPA:
    logger.info("Frontend React detectado em frontend/dist — modo SPA ativo")
if APPLICATION_ROOT:
    logger.info("Subpath activo: %s", APPLICATION_ROOT)


@app.route('/api/health')
def api_health():
    return jsonify({'status': 'ok', 'service': 'scraper-unificado'})


def _serve_spa(path: str = ""):
    """Entrega assets do build Vite ou index.html para rotas client-side."""
    if path.startswith("api/"):
        abort(404)
    if path:
        asset = FRONTEND_DIST / path
        if asset.is_file():
            return send_from_directory(FRONTEND_DIST, path)
    return send_from_directory(FRONTEND_DIST, "index.html")


@app.route("/login")
def login():
    if USE_SPA:
        if session.get("authenticated"):
            return redirect(public_url("/"))
        return _serve_spa()
    if session.get("authenticated"):
        return redirect(url_for("index"))
    return render_template("login.html")


@app.route("/")
def index():
    if USE_SPA:
        return _serve_spa()
    if not session.get("authenticated"):
        return redirect(url_for("login"))
    return render_template("index.html")


@app.route("/admin")
def admin_panel():
    if USE_SPA:
        return _serve_spa()
    if not session.get("authenticated"):
        return redirect(url_for("login"))
    if session.get("role") != "admin":
        return redirect(url_for("index"))
    return render_template("admin.html")


@app.route("/extracoes")
def extracoes_page():
    if USE_SPA:
        return _serve_spa()
    return redirect(url_for("index"))


@app.route("/assets/<path:path>")
def spa_assets(path):
    if USE_SPA:
        return send_from_directory(FRONTEND_DIST / "assets", path)
    abort(404)


@app.route("/<path:path>")
def spa_catch_all(path):
    """Rotas React (ex.: /extracoes) — registado por último."""
    if USE_SPA and not path.startswith("api/"):
        return _serve_spa(path)
    abort(404)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)