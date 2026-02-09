from flask import Blueprint, request, jsonify
import pandas as pd
import os
from werkzeug.utils import secure_filename
from config.tribunais import identificar_tribunal_por_processo
from app.utils.auth_decorator import login_required

bp = Blueprint('upload', __name__, url_prefix='/api')

ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Arquivo não selecionado'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join('data/input', filename)
        os.makedirs('data/input', exist_ok=True)
        file.save(filepath)
        
        try:
            if filename.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(filepath)
            else:
                df = pd.read_csv(filepath)
            
            processos = []
            for idx, row in df.iterrows():
                numero_processo = None
                for col in ['numero_processo', 'processo', 'num_processo', 'Número do Processo']:
                    if col in row:
                        numero_processo = str(row[col])
                        break
                
                if not numero_processo:
                    numero_processo = str(row.iloc[0]) if len(row) > 0 else ''
                
                tribunal = identificar_tribunal_por_processo(numero_processo)
                
                processos.append({
                    'id': idx + 1,
                    'numero_processo': numero_processo,
                    'tribunal': tribunal,
                    'status': 'pendente',
                    'dados': None
                })
            
            return jsonify({
                'success': True,
                'filename': filename,
                'total_processos': len(processos),
                'processos': processos
            })
        except Exception as e:
            return jsonify({'error': f'Erro ao processar arquivo: {str(e)}'}), 500
    
    return jsonify({'error': 'Tipo de arquivo não permitido'}), 400

@bp.route('/tribunais', methods=['GET'])
@login_required
def get_tribunais():
    from config.tribunais import TRIBUNAIS_MAP
    
    tribunais = [
        {
            'codigo': codigo,
            'nome': info['nome'],
            'ramo_justica': info.get('ramo_justica', ''),
            'tribunal_cnj': info.get('tribunal_cnj', '')
        }
        for codigo, info in TRIBUNAIS_MAP.items()
    ]
    
    return jsonify({
        'success': True,
        'tribunais': tribunais,
        'total': len(tribunais)
    })