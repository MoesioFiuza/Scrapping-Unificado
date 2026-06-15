from __future__ import annotations

import logging
import threading
from datetime import datetime

from flask import Blueprint, current_app, jsonify, request, session

from app.services.audit_service import AuditService
from app.services.dataweb_client import DataWebError, get_dataweb_client
from app.services.dataweb_job_service import DataWebJobService
from app.services.extracoes_service import ExtracoesService
from app.utils.auth_decorator import login_required

bp = Blueprint('dataweb', __name__, url_prefix='/api/dataweb')
logger = logging.getLogger(__name__)


def _run_dataweb_job(app, job_id: str, username: str) -> None:
    with app.app_context():
        job = DataWebJobService.get_job(job_id)
        if not job:
            return

        cnjs = list(job.cnjs_json or [])
        DataWebJobService.set_running(job_id)
        client = get_dataweb_client()

        def on_lote(idx: int, total: int) -> None:
            DataWebJobService.set_lote(job_id, idx)

        try:
            excel_bytes = client.processar_cnjs(cnjs, on_lote_progress=on_lote)
        except DataWebError as exc:
            logger.warning('DataWeb job %s falhou: %s', job_id, exc)
            DataWebJobService.finish_error(job_id, str(exc))
            return
        except Exception as exc:
            logger.exception('DataWeb job %s', job_id)
            DataWebJobService.finish_error(job_id, str(exc))
            return

        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'dataweb_{ts}.xlsx'
        ExtracoesService.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        out_path = ExtracoesService.OUTPUT_DIR / filename
        out_path.write_bytes(excel_bytes)

        try:
            extracao = ExtracoesService.registrar_extracao(
                username=username,
                filename=filename,
                tipo='dataweb',
                total_processos=len(cnjs),
            )
        except Exception as exc:
            DataWebJobService.finish_error(job_id, f'Excel gerado mas falha ao registar: {exc}')
            return

        DataWebJobService.finish_success(
            job_id,
            extracao_id=extracao['id'],
            filename=filename,
        )
        AuditService.log(
            'dataweb.processar',
            username=username,
            details={'extracao_id': extracao['id'], 'total_cnjs': len(cnjs), 'job_id': job_id},
        )


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
    Inicia processamento DataWeb em background e devolve job_id para polling.
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

    username = session.get('username') or 'unknown'
    is_admin = session.get('role') == 'admin'
    user_id = DataWebJobService.user_id_for_username(username)
    if user_id is None:
        return jsonify({'success': False, 'error': 'Utilizador não encontrado.'}), 400

    client = get_dataweb_client()
    if not client.is_healthy():
        return jsonify({'success': False, 'error': 'DataWeb indisponível no momento.'}), 503

    job = DataWebJobService.create_job(user_id, cnjs)
    app = current_app._get_current_object()
    threading.Thread(
        target=_run_dataweb_job,
        args=(app, job.id, username),
        daemon=True,
    ).start()

    return jsonify(
        {
            'success': True,
            'job_id': job.id,
            'total_cnjs': job.total_cnjs,
            'total_lotes': job.total_lotes,
        }
    )


@bp.route('/status/<job_id>', methods=['GET'])
@login_required
def dataweb_status(job_id: str):
    username = session.get('username', '')
    is_admin = session.get('role') == 'admin'
    job = DataWebJobService.assert_access(job_id, username, is_admin)
    if not job:
        return jsonify({'success': False, 'error': 'Job não encontrado'}), 404
    return jsonify({'success': True, **job.to_status_dict()})
