from flask import Blueprint, request, jsonify, render_template, session
from app.services.auth_service import AuthService
from app.services.audit_service import AuditService
from app.services.dashboard_escritorio_service import DashboardEscritorioService
from app.services.job_service import JobService
from app.utils.auth_decorator import admin_required
from app.routes.processos import get_scraping_sessions_snapshot

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
        AuditService.log(
            'admin.user.create',
            username=current_username,
            details={'target': username, 'role': role},
        )
        return jsonify({'success': True, 'message': message})
    return jsonify({'success': False, 'error': message}), 400

@bp.route('/users/<username>', methods=['DELETE'])
@admin_required
def delete_user(username):
    """Remove um usuário"""
    current_username = session.get('username', '')
    
    if username == current_username:
        return jsonify({'success': False, 'error': 'Você não pode remover a si mesmo'}), 400
    
    if not AuthService.can_manage_admin(current_username, username):
        return jsonify({'success': False, 'error': 'Apenas o super administrador pode remover outros administradores'}), 403
    
    success, message = AuthService.delete_user(username)
    if success:
        AuditService.log(
            'admin.user.delete',
            username=current_username,
            details={'target': username},
        )
        return jsonify({'success': True, 'message': message})
    return jsonify({'success': False, 'error': message}), 404

@bp.route('/users/<username>/role', methods=['PUT'])
@admin_required
def update_user_role(username):
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
        AuditService.log(
            'admin.user.role',
            username=current_username,
            details={'target': username, 'role': new_role},
        )
        return jsonify({'success': True, 'message': message})
    return jsonify({'success': False, 'error': message}), 404

@bp.route('/dashboard-escritorio', methods=['GET'])
@admin_required
def dashboard_escritorio():
    """Painel de métricas do escritório (todos os admins)."""
    dias = int(request.args.get('dias_taxa', 30))
    payload = DashboardEscritorioService.build(dias_taxa=dias)
    return jsonify({'success': True, **payload})


@bp.route('/scraping-status', methods=['GET'])
@admin_required
def scraping_status():
    """Retorna status das extrações em andamento (apenas super admin)"""
    current_username = session.get('username', '')
    
    # Apenas super admin pode ver
    if not AuthService.is_super_admin(current_username):
        return jsonify({'error': 'Acesso negado'}), 403
    
    # Obter snapshot das sessões (cópia, não referencia)
    scraping_sessions = get_scraping_sessions_snapshot()
    cli_ativos = JobService.list_active_cli_jobs()
    
    # Contar sessões ativas
    sessoes_ativas = []
    total_processos_em_fila = 0
    total_processos_processando = 0
    total_processos_concluidos = 0
    
    for session_id, session_data in scraping_sessions.items():
        status = session_data.get('status', 'unknown')
        
        # Sessões ativas são as que estão starting ou processing
        if status in ['starting', 'processing']:
            resultados_parciais = session_data.get('resultados_parciais', {})
            
            # Contar processos por status nos resultados parciais
            processos_em_fila = 0
            processos_processando = 0
            processos_concluidos = 0
            
            for resultado in resultados_parciais.values():
                resultado_status = resultado.get('status', 'pendente')
                if resultado_status == 'pendente':
                    processos_em_fila += 1
                elif resultado_status == 'processando':
                    processos_processando += 1
                elif resultado_status == 'sucesso' or resultado_status == 'erro':
                    processos_concluidos += 1
            
            # Se não há resultados parciais ainda e está starting, pode estar iniciando
            # Nesse caso, não sabemos quantos processos há, então não contamos na fila
            # mas ainda mostramos a sessão como ativa
            
            total_processos_em_fila += processos_em_fila
            total_processos_processando += processos_processando
            total_processos_concluidos += processos_concluidos
            
            # Obter total de processos da sessão (se disponível)
            total_processos_sessao = session_data.get('total_processos')
            total_processos = processos_em_fila + processos_processando + processos_concluidos
            
            # Se temos o total da sessão, calcular processos em fila corretamente
            if total_processos_sessao is not None:
                processos_em_fila = max(0, total_processos_sessao - processos_processando - processos_concluidos)
                total_processos = total_processos_sessao
            
            total_processos_em_fila += processos_em_fila
            total_processos_processando += processos_processando
            total_processos_concluidos += processos_concluidos
            
            sessoes_ativas.append({
                'session_id': session_id,
                'status': status,
                'processos_em_fila': processos_em_fila,
                'processos_processando': processos_processando,
                'processos_concluidos': processos_concluidos,
                'total_processos': total_processos
            })
    
    return jsonify({
        'success': True,
        'tem_extracao_ativa': len(sessoes_ativas) > 0 or len(cli_ativos) > 0,
        'total_sessoes_ativas': len(sessoes_ativas) + len(cli_ativos),
        'sessoes_ativas': sessoes_ativas,
        'jobs_cli_ativos': cli_ativos,
        'resumo': {
            'total_processos_em_fila': total_processos_em_fila,
            'total_processos_processando': total_processos_processando,
            'total_processos_concluidos': total_processos_concluidos,
            'total_processos': total_processos_em_fila + total_processos_processando + total_processos_concluidos
        }
    })


@bp.route('/audit-logs', methods=['GET'])
@admin_required
def audit_logs():
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))
    logs, total = AuditService.list_logs(limit=limit, offset=offset)
    return jsonify({'success': True, 'logs': logs, 'total': total})
