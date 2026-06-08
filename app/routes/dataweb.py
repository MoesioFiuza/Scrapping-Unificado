from datetime import datetime

from flask import Blueprint, jsonify, request, session

from app.services.dataweb_client import DataWebError, get_dataweb_client
from app.services.extracoes_service import ExtracoesService
from app.services.audit_service import AuditService
from app.utils.auth_decorator import login_required

bp = Blueprint('dataweb', __name__, url_prefix='/api/dataweb')


@bp.route('/health', methods=['GET'])
@login_required
def dataweb_health():
    client = get_dataweb_client()
    healthy = client.is_healthy()
    return jsonify({'success': True, 'healthy': healthy})


@bp.route('/processar', methods=['POST'])
@login_required
def dataweb_processar():
    """
    Envia CNJs ao microserviço DataWeb e regista o Excel gerado em data/output.
    Body JSON: { "cnjs": ["..."] } ou { "processos": [{ "numero_processo": "..." }] }
    """
    data = request.get_json() or {}
    cnjs = list(data.get('cnjs') or [])

    if not cnjs:
        for p in data.get('processos') or []:
            num = (p or {}).get('numero_processo')
            if num:
                cnjs.append(str(num))

    if not cnjs:
        return jsonify({'success': False, 'error': 'Informe ao menos um CNJ.'}), 400

    client = get_dataweb_client()
    try:
        excel_bytes = client.processar_cnjs(cnjs)
    except DataWebError as exc:
        status = exc.status if exc.status and 400 <= exc.status < 600 else 400
        return jsonify(
            {
                'success': False,
                'error': str(exc),
                'title': exc.title,
            }
        ), status

    username = session.get('username') or 'unknown'
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'dataweb_{ts}.xlsx'
    ExtracoesService.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = ExtracoesService.OUTPUT_DIR / filename
    out_path.write_bytes(excel_bytes)

    extracao = ExtracoesService.registrar_extracao(
        username=username,
        filename=filename,
        tipo='dataweb',
        total_processos=len(cnjs),
    )

    AuditService.log(
        'dataweb.processar',
        username=username,
        details={'extracao_id': extracao['id'], 'total_cnjs': len(cnjs)},
    )

    return jsonify(
        {
            'success': True,
            'extracao_id': extracao['id'],
            'filename': filename,
            'total_cnjs': len(cnjs),
        }
    )
