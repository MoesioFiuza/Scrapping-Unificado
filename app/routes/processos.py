from flask import Blueprint, request, jsonify, session, current_app
from app.services.scraper_service import ScraperService
from app.services.cli_extracao_runner import executar_cli_e_registrar
from app.services.job_service import JobService
from app.services.audit_service import AuditService
from app.utils.auth_decorator import login_required
from config.cli_tribunal_registry import listar_opcoes_por_tribunal
import asyncio
import uuid
import threading
import time
import logging
from collections import defaultdict

bp = Blueprint('processos', __name__, url_prefix='/api')
logger = logging.getLogger(__name__)

scraper_service = ScraperService()


def processar_scraping_async(app, session_id, processos):
    with app.app_context():
        loop = None
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            JobService.set_scraping_status(session_id, 'processing')

            logger.info("Iniciando scraping - Sessão: %s, Total: %s", session_id, len(processos))

            processos_por_tribunal = defaultdict(list)
            processos_sem_tribunal = []

            for idx, processo in enumerate(processos):
                if JobService.is_scraping_aborted(session_id):
                    break
                tribunal = processo.get('tribunal')
                if tribunal:
                    processos_por_tribunal[tribunal].append((idx, processo))
                else:
                    processos_sem_tribunal.append((idx, processo))

            resultados_dict = {}

            for tribunal_key, lista_processos in processos_por_tribunal.items():
                if JobService.is_scraping_aborted(session_id):
                    break

                for idx, processo in lista_processos:
                    if JobService.is_scraping_aborted(session_id):
                        break

                    numero_processo = processo['numero_processo']
                    resultado_temp = {
                        'numero_processo': numero_processo,
                        'tribunal': tribunal_key,
                        'status': 'processando',
                        'dados': None,
                        'erro': None,
                    }
                    resultados_dict[idx] = resultado_temp
                    JobService.merge_scraping_parcial(session_id, numero_processo, resultado_temp)

                    resultado = loop.run_until_complete(
                        scraper_service.processar_processo(numero_processo, tribunal_key)
                    )
                    resultados_dict[idx] = resultado
                    JobService.merge_scraping_parcial(session_id, numero_processo, resultado)

                if not JobService.is_scraping_aborted(session_id):
                    scraper_service._fechar_abas_tribunal(tribunal_key)

            for idx, processo in processos_sem_tribunal:
                if JobService.is_scraping_aborted(session_id):
                    break
                numero_processo = processo.get('numero_processo', '')
                resultado = {
                    'numero_processo': numero_processo,
                    'tribunal': None,
                    'status': 'erro',
                    'erro': 'Tribunal não identificado',
                }
                resultados_dict[idx] = resultado
                JobService.merge_scraping_parcial(session_id, numero_processo, resultado)

            if not JobService.is_scraping_aborted(session_id):
                resultados = [resultados_dict[idx] for idx in range(len(processos))]
                JobService.finish_scraping(session_id, resultados, 'completed')
                logger.info("Scraping concluído - Sessão: %s", session_id)
            else:
                JobService.finish_scraping(session_id, None, 'aborted', 'Scraping abortado pelo utilizador')
                logger.warning("Scraping abortado - Sessão: %s", session_id)

            scraper_service.fechar_scrapers()
            loop.close()
        except Exception as e:
            logger.error("Erro fatal na sessão %s: %s", session_id, e, exc_info=True)
            mensagem = scraper_service._obter_mensagem_amigavel(e)
            JobService.finish_scraping(session_id, None, 'error', mensagem)
            try:
                scraper_service.fechar_scrapers()
            except Exception:
                pass
        finally:
            if loop is not None:
                try:
                    loop.close()
                except Exception:
                    pass


@bp.route('/processos/scraper', methods=['POST'])
@login_required
def iniciar_scraping():
    data = request.get_json()
    processos = data.get('processos', [])
    if not processos:
        return jsonify({'error': 'Nenhum processo fornecido'}), 400

    username = session.get('username') or ''
    user_id = JobService.user_id_for_username(username)
    if not user_id:
        return jsonify({'error': 'Utilizador não encontrado'}), 400

    try:
        job = JobService.create_scraping_job(user_id, processos)
        app_obj = current_app._get_current_object()
        thread = threading.Thread(
            target=processar_scraping_async,
            args=(app_obj, job.id, processos),
            daemon=True,
        )
        thread.start()

        AuditService.log(
            'scraping.start',
            username=username,
            details={'session_id': job.id, 'total_processos': len(processos)},
        )

        return jsonify({'success': True, 'session_id': job.id})
    except Exception as e:
        logger.error("Erro ao iniciar scraping: %s", e, exc_info=True)
        return jsonify({'error': 'Erro ao processar scraping. Tente novamente.'}), 500


@bp.route('/processos/status/<session_id>', methods=['GET'])
@login_required
def status_processos(session_id):
    username = session.get('username') or ''
    is_admin = session.get('role') == 'admin'
    job = JobService.assert_scraping_access(session_id, username, is_admin)
    if not job:
        return jsonify({
            'status': 'error',
            'error': 'Sessão não encontrada ou expirada.',
            'resultados_parciais': [],
        }), 200

    return jsonify(job.to_status_dict())


@bp.route('/processos/abort/<session_id>', methods=['POST'])
@login_required
def abortar_scraping(session_id):
    username = session.get('username') or ''
    is_admin = session.get('role') == 'admin'
    job = JobService.assert_scraping_access(session_id, username, is_admin)
    if not job:
        return jsonify({'error': 'Sessão não encontrada'}), 404

    if job.status in ('completed', 'aborted', 'interrupted'):
        return jsonify({'error': 'Sessão já finalizada'}), 400

    JobService.request_scraping_abort(session_id)
    AuditService.log('scraping.abort', username=username, details={'session_id': session_id})
    return jsonify({'success': True, 'message': 'Scraping será abortado'})


@bp.route('/processos/status', methods=['GET'])
@login_required
def status_geral():
    return jsonify({'status': 'ok'})


def _run_cli_job(app, job_id: str, username: str, tribunal_key: str, browser: str, job_mode: str, numeros: list, workers: int):
    def on_prog(res: dict) -> None:
        if JobService.is_cli_aborted(job_id):
            return
        JobService.merge_cli_parcial(job_id, res)

    with app.app_context():
        try:
            if JobService.is_cli_aborted(job_id):
                JobService.finish_cli_job(job_id, status='aborted', error='Extração cancelada pelo utilizador')
                return
            JobService.set_cli_running(job_id)

            res = executar_cli_e_registrar(
                username=username,
                tribunal_key=tribunal_key,
                browser=browser,
                job_mode=job_mode,
                numeros=numeros,
                workers=workers,
                progress_cb=on_prog,
            )

            if JobService.is_cli_aborted(job_id):
                JobService.finish_cli_job(
                    job_id,
                    status='aborted',
                    error='Extração cancelada pelo utilizador',
                    extracao_ids=res.get('extracao_ids'),
                    filenames=res.get('filenames'),
                )
            elif res.get('ok'):
                JobService.finish_cli_job(
                    job_id,
                    status='completed',
                    extracao_ids=res.get('extracao_ids'),
                    filenames=res.get('filenames'),
                )
            else:
                JobService.finish_cli_job(
                    job_id,
                    status='error',
                    error=res.get('error'),
                    extracao_ids=res.get('extracao_ids'),
                    filenames=res.get('filenames'),
                )
        except Exception as e:
            logger.exception("Job CLI extração %s", job_id)
            if JobService.is_cli_aborted(job_id):
                JobService.finish_cli_job(job_id, status='aborted', error='Extração cancelada pelo utilizador')
            else:
                JobService.finish_cli_job(job_id, status='error', error=str(e))


@bp.route('/processos/cli-opcoes', methods=['GET'])
@login_required
def cli_opcoes():
    return jsonify({'success': True, 'opcoes': listar_opcoes_por_tribunal()})


@bp.route('/processos/cli-extracao', methods=['POST'])
@login_required
def iniciar_cli_extracao():
    data = request.get_json() or {}
    tribunal_key = data.get('tribunal_key')
    browser = (data.get('browser') or 'chrome').lower()
    job_mode = (data.get('job_mode') or '').lower()
    workers = int(data.get('workers') or 3)
    processos = data.get('processos') or []

    if not tribunal_key:
        return jsonify({'error': 'tribunal_key é obrigatório'}), 400
    if job_mode not in ('movimentacoes', 'planilhas', 'polos'):
        return jsonify({'error': 'job_mode inválido'}), 400
    if not processos:
        return jsonify({'error': 'Nenhum processo fornecido'}), 400

    numeros = [p.get('numero_processo') for p in processos if p.get('numero_processo')]
    username = session.get('username') or 'unknown'
    user_id = JobService.user_id_for_username(username)
    if not user_id:
        return jsonify({'error': 'Utilizador não encontrado'}), 400

    job_id = str(uuid.uuid4())
    JobService.create_cli_job(
        user_id,
        job_id=job_id,
        tribunal_key=tribunal_key,
        browser=browser,
        job_mode=job_mode,
        workers=workers,
        total_processos=len(numeros),
    )

    app_obj = current_app._get_current_object()
    thread = threading.Thread(
        target=_run_cli_job,
        args=(app_obj, job_id, username, tribunal_key, browser, job_mode, numeros, workers),
        daemon=True,
    )
    thread.start()

    AuditService.log(
        'cli.start',
        username=username,
        details={
            'job_id': job_id,
            'tribunal_key': tribunal_key,
            'job_mode': job_mode,
            'total_processos': len(numeros),
        },
    )

    return jsonify({'success': True, 'job_id': job_id})


@bp.route('/processos/cli-extracao/<job_id>', methods=['GET'])
@login_required
def status_cli_extracao(job_id):
    username = session.get('username') or ''
    is_admin = session.get('role') == 'admin'
    job = JobService.assert_cli_access(job_id, username, is_admin)
    if not job:
        return jsonify({'status': 'error', 'error': 'Job não encontrado'}), 404
    return jsonify(job.to_status_dict())


@bp.route('/processos/cli-extracao/<job_id>/abort', methods=['POST'])
@login_required
def abortar_cli_extracao(job_id):
    username = session.get('username') or ''
    is_admin = session.get('role') == 'admin'
    job = JobService.assert_cli_access(job_id, username, is_admin)
    if not job:
        return jsonify({'error': 'Job não encontrado'}), 404
    if job.status in ('completed', 'error', 'aborted', 'interrupted'):
        return jsonify({'error': 'Job já finalizado'}), 400

    JobService.request_cli_abort(job_id)
    AuditService.log('cli.abort', username=username, details={'job_id': job_id})
    return jsonify({'success': True, 'message': 'Extração CLI será cancelada'})


def get_scraping_sessions_snapshot():
    return JobService.get_scraping_sessions_snapshot()
