from flask import Blueprint, request, jsonify, send_file, session
from app.services.extracoes_service import ExtracoesService
from app.services.audit_service import AuditService
from app.utils.auth_decorator import login_required

bp = Blueprint('extracoes', __name__, url_prefix='/api/extracoes')

@bp.route('/listar', methods=['GET'])
@login_required
def listar_extracoes():
    """Lista extrações do usuário logado (metadados da BD, sem ler ficheiros Excel)."""
    username = session.get('username', '')
    is_admin = session.get('role') == 'admin'
    
    if not is_admin:
        ExtracoesService.limpar_extracoes_antigas(username, is_admin)
    
    extracoes = ExtracoesService.listar_extracoes(username, is_admin)

    return jsonify({
        'success': True,
        'extracoes': extracoes,
        'total': len(extracoes),
    })

@bp.route('/resumo', methods=['GET'])
@login_required
def resumo_dashboard():
    """Métricas agregadas do histórico de extrações do utilizador."""
    username = session.get('username', '')
    is_admin = session.get('role') == 'admin'
    resumo = ExtracoesService.calcular_resumo_dashboard(username, is_admin)
    return jsonify({'success': True, 'resumo': resumo})

@bp.route('/download/<extracao_id>', methods=['GET'])
@login_required
def download_extracao(extracao_id):
    """Download de uma extração"""
    username = session.get('username', '')
    is_admin = session.get('role') == 'admin'
    
    extracao = ExtracoesService.obter_extracao(extracao_id)
    
    if not extracao:
        return jsonify({'error': 'Extração não encontrada'}), 404
    
    if not is_admin and extracao.get('username') != username:
        return jsonify({'error': 'Acesso negado'}), 403
    
    filepath = ExtracoesService.resolver_filepath_extracao(extracao)
    if not filepath.is_file():
        return jsonify({'error': 'Arquivo não encontrado'}), 404

    return send_file(
        str(filepath),
        as_attachment=True,
        download_name=extracao.get('filename', 'extracao.xlsx'),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@bp.route('/deletar/<extracao_id>', methods=['DELETE'])
@login_required
def deletar_extracao(extracao_id):
    username = session.get('username', '')
    is_admin = session.get('role') == 'admin'
    
    success = ExtracoesService.deletar_extracao(extracao_id, username, is_admin)
    
    if success:
        AuditService.log(
            'extracao.delete',
            username=username,
            details={'extracao_id': extracao_id},
        )
        return jsonify({'success': True, 'message': 'Extração removida com sucesso'})
    return jsonify({'error': 'Extração não encontrada ou sem permissão'}), 404
