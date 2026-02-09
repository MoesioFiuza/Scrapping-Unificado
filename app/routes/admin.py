from flask import Blueprint, request, jsonify, render_template, session
from app.services.auth_service import AuthService
from app.utils.auth_decorator import admin_required

bp = Blueprint('admin', __name__, url_prefix='/api/admin')

@bp.route('/users', methods=['GET'])
@admin_required
def list_users():
    """Lista todos os usuários (apenas super admin vê outros admins)"""
    current_username = session.get('username', '')
    users = AuthService.get_all_users(current_username)
    is_super_admin = AuthService.is_super_admin(current_username)
    return jsonify({
        'success': True, 
        'users': users,
        'is_super_admin': is_super_admin
    })

@bp.route('/users', methods=['POST'])
@admin_required
def add_user():
    """Adiciona um novo usuário"""
    current_username = session.get('username', '')
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    role = data.get('role', 'user')
    
    if not username or not password:
        return jsonify({'success': False, 'error': 'Usuário e senha são obrigatórios'}), 400
    
    if role not in ['admin', 'user']:
        return jsonify({'success': False, 'error': 'Role inválido. Use "admin" ou "user"'}), 400
    
    # Apenas super admin pode criar novos admins
    if role == 'admin' and not AuthService.is_super_admin(current_username):
        return jsonify({'success': False, 'error': 'Apenas o super administrador pode criar novos administradores'}), 403
    
    success, message = AuthService.add_user(username, password, role)
    if success:
        return jsonify({'success': True, 'message': message})
    return jsonify({'success': False, 'error': message}), 400

@bp.route('/users/<username>', methods=['DELETE'])
@admin_required
def delete_user(username):
    """Remove um usuário"""
    current_username = session.get('username', '')
    
    # Não permitir remover a si mesmo
    if username == current_username:
        return jsonify({'success': False, 'error': 'Você não pode remover a si mesmo'}), 400
    
    # Verificar se pode remover (apenas super admin pode remover outros admins)
    if not AuthService.can_manage_admin(current_username, username):
        return jsonify({'success': False, 'error': 'Apenas o super administrador pode remover outros administradores'}), 403
    
    success, message = AuthService.delete_user(username)
    if success:
        return jsonify({'success': True, 'message': message})
    return jsonify({'success': False, 'error': message}), 404

@bp.route('/users/<username>/role', methods=['PUT'])
@admin_required
def update_user_role(username):
    """Atualiza o role de um usuário"""
    current_username = session.get('username', '')
    data = request.get_json()
    new_role = data.get('role', '')
    
    if new_role not in ['admin', 'user']:
        return jsonify({'success': False, 'error': 'Role inválido. Use "admin" ou "user"'}), 400
    
    # Não permitir remover admin de si mesmo
    if username == current_username and new_role != 'admin':
        return jsonify({'success': False, 'error': 'Você não pode remover seu próprio acesso de admin'}), 400
    
    # Verificar se pode alterar role de admin (apenas super admin pode alterar role de outros admins)
    target_role = AuthService.get_user_role(username)
    if target_role == 'admin' and not AuthService.can_manage_admin(current_username, username):
        return jsonify({'success': False, 'error': 'Apenas o super administrador pode alterar o role de outros administradores'}), 403
    
    # Não permitir que não-super-admin torne alguém admin ou altere role de admin
    if not AuthService.is_super_admin(current_username):
        if new_role == 'admin' or target_role == 'admin':
            return jsonify({'success': False, 'error': 'Apenas o super administrador pode criar ou alterar administradores'}), 403
    
    success, message = AuthService.update_user_role(username, new_role)
    if success:
        return jsonify({'success': True, 'message': message})
    return jsonify({'success': False, 'error': message}), 404
