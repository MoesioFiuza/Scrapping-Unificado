from flask import Blueprint, request, jsonify, session
from app.services.auth_service import AuthService

bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({'success': False, 'error': 'Usuário e senha são obrigatórios'}), 400
    
    user_role = AuthService.verify_user(username, password)
    if user_role:
        session['authenticated'] = True
        session['username'] = username
        session['role'] = user_role
        return jsonify({
            'success': True, 
            'message': 'Login realizado com sucesso',
            'role': user_role
        })
    
    return jsonify({'success': False, 'error': 'Usuário ou senha inválidos'}), 401

@bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logout realizado com sucesso'})

@bp.route('/check', methods=['GET'])
def check_auth():
    if session.get('authenticated'):
        return jsonify({
            'authenticated': True, 
            'username': session.get('username'),
            'role': session.get('role', 'user')
        })
    return jsonify({'authenticated': False}), 401