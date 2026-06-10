from __future__ import annotations

import logging
import threading
import uuid

from flask import Blueprint, current_app, jsonify, request, session

from app.services.audit_service import AuditService
from app.services.encerramento_job_service import EncerramentoJobService
from app.services.encerramento_runner import WORKERS_PADRAO, executar_encerramento
from app.services.movimentacoes_encerramento import analisar_processo, resumo_parcial

bp = Blueprint("encerramento", __name__, url_prefix="/api")
logger = logging.getLogger(__name__)

TRIBUNAL_TJCE = "8.06"
TRIBUNAL_ESAJ_CE = "8.06_esaj"


def _run_job(app, job_id: str, tribunal_key: str, numeros: list[str], workers: int) -> None:
    def on_prog(res: dict) -> None:
        if EncerramentoJobService.is_aborted(job_id):
            return
        EncerramentoJobService.merge_parcial(job_id, resumo_parcial(analisar_processo(res)))

    with app.app_context():
        try:
            if EncerramentoJobService.is_aborted(job_id):
                EncerramentoJobService.finish(job_id, status="aborted", error="Job cancelado.")
                return
            EncerramentoJobService.set_running(job_id)

            out = executar_encerramento(
                tribunal_key,
                numeros,
                workers=workers,
                progress_cb=on_prog,
                should_abort=lambda: EncerramentoJobService.is_aborted(job_id),
            )

            if EncerramentoJobService.is_aborted(job_id):
                EncerramentoJobService.finish(
                    job_id,
                    status="aborted",
                    error="Job cancelado.",
                    resultado=out.get("resultado"),
                )
            elif out.get("ok"):
                EncerramentoJobService.finish(
                    job_id,
                    status="completed",
                    resultado=out.get("resultado"),
                )
            else:
                EncerramentoJobService.finish(
                    job_id,
                    status="error",
                    error=out.get("error"),
                    resultado=out.get("resultado"),
                )
        except Exception as exc:
            logger.exception("Job encerramento %s", job_id)
            if EncerramentoJobService.is_aborted(job_id):
                EncerramentoJobService.finish(job_id, status="aborted", error="Job cancelado.")
            else:
                EncerramentoJobService.finish(job_id, status="error", error=str(exc))


def _iniciar_job(tribunal_key: str):
    data = request.get_json() or {}
    processos = data.get("processos") or []
    if not processos:
        return jsonify({"error": "Nenhum processo fornecido"}), 400

    numeros = [str(p.get("numero_processo")).strip() for p in processos if p.get("numero_processo")]
    if not numeros:
        return jsonify({"error": "Nenhum número de processo válido"}), 400

    from app.services.encerramento_runner import validar_numeros

    val_err = validar_numeros(tribunal_key, numeros)
    if val_err:
        return jsonify({"error": val_err}), 400

    username = session.get("username") or "anonymous"
    user_id = EncerramentoJobService.system_user_id()

    job_id = str(uuid.uuid4())
    EncerramentoJobService.create_job(
        user_id,
        job_id=job_id,
        tribunal_key=tribunal_key,
        total_processos=len(numeros),
        workers=WORKERS_PADRAO,
    )

    app_obj = current_app._get_current_object()
    thread = threading.Thread(
        target=_run_job,
        args=(app_obj, job_id, tribunal_key, numeros, WORKERS_PADRAO),
        daemon=True,
    )
    thread.start()

    AuditService.log(
        "encerramento.start",
        username=username,
        details={
            "job_id": job_id,
            "tribunal_key": tribunal_key,
            "total_processos": len(numeros),
            "workers": WORKERS_PADRAO,
        },
    )

    return jsonify({"success": True, "job_id": job_id})


def _status_job(job_id: str):
    job = EncerramentoJobService.get_job(job_id)
    if not job:
        return jsonify({"status": "error", "error": "Job não encontrado"}), 404
    return jsonify({"success": True, **job.to_status_dict()})


def _abort_job(job_id: str):
    job = EncerramentoJobService.get_job(job_id)
    if not job:
        return jsonify({"error": "Job não encontrado"}), 404
    if job.status in ("completed", "error", "aborted", "interrupted"):
        return jsonify({"error": "Job já finalizado"}), 400

    EncerramentoJobService.request_abort(job_id)
    username = session.get("username") or "anonymous"
    AuditService.log("encerramento.abort", username=username, details={"job_id": job_id})
    return jsonify({"success": True, "message": "Job será cancelado"})


@bp.route("/tjce/movimentacoes-encerramento", methods=["POST"])
def tjce_movimentacoes_encerramento():
    """TJCE (PJe CE): movimentações + sinais de encerramento, JSON only, 3 workers."""
    return _iniciar_job(TRIBUNAL_TJCE)


@bp.route("/tjce/movimentacoes-encerramento/<job_id>", methods=["GET"])
def tjce_movimentacoes_encerramento_status(job_id):
    return _status_job(job_id)


@bp.route("/tjce/movimentacoes-encerramento/<job_id>/abort", methods=["POST"])
def tjce_movimentacoes_encerramento_abort(job_id):
    return _abort_job(job_id)


@bp.route("/esaj-ce/movimentacoes-encerramento", methods=["POST"])
def esaj_ce_movimentacoes_encerramento():
    """eSAJ CE: movimentações + sinais de encerramento, JSON only, 3 workers."""
    return _iniciar_job(TRIBUNAL_ESAJ_CE)


@bp.route("/esaj-ce/movimentacoes-encerramento/<job_id>", methods=["GET"])
def esaj_ce_movimentacoes_encerramento_status(job_id):
    return _status_job(job_id)


@bp.route("/esaj-ce/movimentacoes-encerramento/<job_id>/abort", methods=["POST"])
def esaj_ce_movimentacoes_encerramento_abort(job_id):
    return _abort_job(job_id)
