# app/main.py
import sys
import os
from pathlib import Path

root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from flask import Flask, render_template
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

app.config['UPLOAD_FOLDER'] = 'data/input'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

app.template_folder = '../templates'
app.static_folder = 'static'

from app.routes import upload, processos, resultados

app.register_blueprint(upload.bp)
app.register_blueprint(processos.bp)
app.register_blueprint(resultados.bp)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)