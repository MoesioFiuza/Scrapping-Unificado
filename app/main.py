import sys
import os
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler

root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from flask import Flask, render_template, session, redirect, url_for
from flask_cors import CORS
from dotenv import load_dotenv
from app.utils.auth_decorator import login_required, admin_required

load_dotenv()

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
CORS(app)

app.config['UPLOAD_FOLDER'] = 'data/input'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Usar caminhos absolutos baseados no root_dir para garantir funcionamento no servidor
app.template_folder = str(root_dir / 'templates')
app.static_folder = str(root_dir / 'app' / 'static')
app.static_url_path = '/static'

# Registrar blueprints com tratamento de erro
try:
    from app.routes import upload, processos, resultados, auth, admin, extracoes
    
    app.register_blueprint(upload.bp)
    app.register_blueprint(processos.bp)
    app.register_blueprint(resultados.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(extracoes.bp)
    
    logger.info("Blueprints registrados com sucesso")
except Exception as e:
    logger.error(f"Erro ao registrar blueprints: {e}", exc_info=True)
    # Re-raise para que o erro seja visível
    raise

@app.route('/login')
def login():
    if session.get('authenticated'):
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/admin')
@admin_required
def admin_panel():
    return render_template('admin.html')

# Endpoint temporário para adicionar usuário admin
@app.route('/add-admin-temp')
def add_admin_temp():
    from app.services.auth_service import AuthService
    username = 'amanda.xelian@valenca.adv.br'
    password = 'Fenobarbital'
    role = 'admin'
    success, message = AuthService.add_user(username, password, role)
    if success:
        return f'✓ {message}<br>Usuário: {username}<br>Role: {role}'
    return f'✗ Erro: {message}'

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)