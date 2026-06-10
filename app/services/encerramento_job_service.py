from __future__ import annotations

import logging
import secrets
from datetime import datetime

from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models import EncerramentoJob, User

logger = logging.getLogger(__name__)

_ACTIVE = ("queued", "running", "aborting")
_SYSTEM_USERNAME = "encerramento@system"


class EncerramentoJobService:
    @staticmethod
    def get_job(job_id: str) -> EncerramentoJob | None:
        return db.session.get(EncerramentoJob, job_id)

    @staticmethod
    def system_user_id() -> int:
        """Utilizador interno para jobs públicos (sem autenticação)."""
        user = User.query.filter_by(username=_SYSTEM_USERNAME).first()
        if user:
            return user.id
        user = User(
            username=_SYSTEM_USERNAME,
            password_hash=generate_password_hash(secrets.token_hex(32)),
            role="user",
        )
        db.session.add(user)
        db.session.commit()
        logger.info("Utilizador de sistema criado para jobs de encerramento: %s", _SYSTEM_USERNAME)
        return user.id

    @staticmethod
    def create_job(user_id: int, *, job_id: str, tribunal_key: str, total_processos: int, workers: int = 3) -> EncerramentoJob:
        job = EncerramentoJob(
            id=job_id,
            user_id=user_id,
            tribunal_key=tribunal_key,
            workers=workers,
            status="queued",
            total_processos=total_processos,
        )
        db.session.add(job)
        db.session.commit()
        return job

    @staticmethod
    def set_running(job_id: str) -> None:
        job = db.session.get(EncerramentoJob, job_id)
        if not job:
            return
        job.status = "running"
        job.started_at = datetime.utcnow()
        db.session.commit()

    @staticmethod
    def merge_parcial(job_id: str, processo: dict) -> None:
        num = (processo or {}).get("numero_processo")
        if not num:
            return
        job = db.session.get(EncerramentoJob, job_id)
        if not job:
            return
        bucket = dict(job.resultados_parciais_json or {})
        bucket[str(num).strip()] = processo
        job.resultados_parciais_json = bucket
        db.session.commit()

    @staticmethod
    def is_aborted(job_id: str) -> bool:
        job = db.session.get(EncerramentoJob, job_id)
        return bool(job and job.aborted)

    @staticmethod
    def request_abort(job_id: str) -> bool:
        job = db.session.get(EncerramentoJob, job_id)
        if not job or job.status in ("completed", "error", "aborted", "interrupted"):
            return False
        job.aborted = True
        job.status = "aborting"
        job.error_message = "Job cancelado pelo utilizador"
        db.session.commit()
        return True

    @staticmethod
    def finish(
        job_id: str,
        *,
        status: str,
        error: str | None = None,
        resultado: dict | None = None,
    ) -> None:
        job = db.session.get(EncerramentoJob, job_id)
        if not job:
            return
        job.status = status
        job.error_message = error
        job.resultado_json = resultado
        job.finished_at = datetime.utcnow()
        db.session.commit()

    @staticmethod
    def mark_stale_on_startup() -> None:
        msg = "Servidor reiniciado — job interrompido."
        n = (
            EncerramentoJob.query.filter(EncerramentoJob.status.in_(_ACTIVE))
            .update(
                {
                    EncerramentoJob.status: "interrupted",
                    EncerramentoJob.error_message: msg,
                    EncerramentoJob.finished_at: datetime.utcnow(),
                },
                synchronize_session=False,
            )
        )
        if n:
            db.session.commit()
            logger.info("Jobs encerramento interrompidos no arranque: %s", n)
