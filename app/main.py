import sys
import os
from pathlib import Path

root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from flask import Flask, render_template, session, redirect, url_for
from flask_cors import CORS
from dotenv import load_dotenv
from app.utils.auth_decorator import login_required, admin_required

load_dotenv()

app = Flask(__name__)
CORS(app)

app.config['UPLOAD_FOLDER'] = 'data/input'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

app.template_folder = '../templates'
app.static_folder = 'static'

from app.routes import upload, processos, resultados, auth, admin, extracoes

app.register_blueprint(upload.bp)
app.register_blueprint(processos.bp)
app.register_blueprint(resultados.bp)
app.register_blueprint(auth.bp)
app.register_blueprint(admin.bp)
app.register_blueprint(extracoes.bp)

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