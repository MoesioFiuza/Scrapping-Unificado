from flask import Blueprint, request, jsonify, session
from app.services.auth_service import AuthService
from app.services.audit_service import AuditService
from app.utils.auth_decorator import login_required

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
        AuditService.log('auth.login.success', username=username)
        return jsonify({
            'success': True, 
            'message': 'Login realizado com sucesso',
            'role': user_role
        })

    AuditService.log('auth.login.failed', username=username, details={'reason': 'invalid_credentials'})
    return jsonify({'success': False, 'error': 'Usuário ou senha inválidos'}), 401

@bp.route('/logout', methods=['POST'])
def logout():
    username = session.get('username')
    session.clear()
    if username:
        AuditService.log('auth.logout', username=username)
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


@bp.route('/password', methods=['POST'])
@login_required
def change_password():
    username = session.get('username', '')
    data = request.get_json(silent=True) or {}
    current_password = data.get('current_password') or ''
    new_password = data.get('new_password') or ''
    confirm_password = data.get('confirm_password') or ''

    if not current_password or not new_password:
        return jsonify({'success': False, 'error': 'Preencha a senha actual e a nova senha'}), 400
    if new_password != confirm_password:
        return jsonify({'success': False, 'error': 'A confirmação não coincide com a nova senha'}), 400

    success, message = AuthService.change_password(username, current_password, new_password)
    if success:
        AuditService.log('auth.password.change', username=username)
        return jsonify({'success': True, 'message': message})
    return jsonify({'success': False, 'error': message}), 400
