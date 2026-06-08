from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from sqlalchemy.orm.attributes import flag_modified

from app.extensions import db
from app.models import CliJob, ScrapingJob, User

logger = logging.getLogger(__name__)

_ACTIVE_SCRAPING = ('starting', 'processing', 'aborting')
_ACTIVE_CLI = ('queued', 'running', 'aborting')


class JobService:
    # --- Utilizador ---

    @staticmethod
    def user_id_for_username(username: str) -> int | None:
        user = User.query.filter_by(username=username.strip().lower()).first()
        return user.id if user else None

    @staticmethod
    def assert_scraping_access(job_id: str, username: str, is_admin: bool) -> ScrapingJob | None:
        job = db.session.get(ScrapingJob, job_id)
        if not job:
            return None
        if not is_admin and job.user.username != username.strip().lower():
            return None
        return job

    @staticmethod
    def assert_cli_access(job_id: str, username: str, is_admin: bool) -> CliJob | None:
        job = db.session.get(CliJob, job_id)
        if not job:
            return None
        if not is_admin and job.user.username != username.strip().lower():
            return None
        return job

    # --- Scraping ---

    @staticmethod
    def create_scraping_job(user_id: int, processos: list[dict]) -> ScrapingJob:
        import uuid

        job = ScrapingJob(
            id=str(uuid.uuid4()),
            user_id=user_id,
            status='starting',
            total_processos=len(processos),
            processos_json=processos,
            resultados_parciais_json={},
        )
        db.session.add(job)
        db.session.commit()
        return job

    @staticmethod
    def get_scraping_job(job_id: str) -> ScrapingJob | None:
        return db.session.get(ScrapingJob, job_id)

    @staticmethod
    def set_scraping_status(job_id: str, status: str, *, error: str | None = None) -> None:
        job = db.session.get(ScrapingJob, job_id)
        if not job:
            return
        job.status = status
        if error is not None:
            job.error_message = error
        if status in ('completed', 'error', 'aborted', 'interrupted'):
            job.finished_at = datetime.utcnow()
        db.session.commit()

    @staticmethod
    def merge_scraping_parcial(job_id: str, numero: str, row: dict) -> None:
        job = db.session.get(ScrapingJob, job_id)
        if not job:
            return
        bucket = dict(job.resultados_parciais_json or {})
        bucket[str(numero).strip()] = row
        job.resultados_parciais_json = bucket
        flag_modified(job, 'resultados_parciais_json')
        if job.status == 'starting':
            job.status = 'processing'
        db.session.commit()

    @staticmethod
    def is_scraping_aborted(job_id: str) -> bool:
        job = db.session.get(ScrapingJob, job_id)
        return bool(job and job.aborted)

    @staticmethod
    def request_scraping_abort(job_id: str) -> bool:
        job = db.session.get(ScrapingJob, job_id)
        if not job or job.status in ('completed', 'aborted', 'error', 'interrupted'):
            return False
        job.aborted = True
        job.status = 'aborting'
        db.session.commit()
        return True

    @staticmethod
    def finish_scraping(job_id: str, resultados: list[dict] | None, status: str, error: str | None = None) -> None:
        job = db.session.get(ScrapingJob, job_id)
        if not job:
            return
        job.status = status
        job.resultados_json = resultados
        job.error_message = error
        job.finished_at = datetime.utcnow()
        db.session.commit()

    # --- CLI ---

    @staticmethod
    def create_cli_job(
        user_id: int,
        *,
        job_id: str,
        tribunal_key: str,
        browser: str,
        job_mode: str,
        workers: int,
        total_processos: int,
    ) -> CliJob:
        job = CliJob(
            id=job_id,
            user_id=user_id,
            tribunal_key=tribunal_key,
            browser=browser,
            job_mode=job_mode,
            workers=workers,
            status='queued',
            total_processos=total_processos,
        )
        db.session.add(job)
        db.session.commit()
        return job

    @staticmethod
    def get_cli_job(job_id: str) -> CliJob | None:
        return db.session.get(CliJob, job_id)

    @staticmethod
    def set_cli_running(job_id: str) -> None:
        job = db.session.get(CliJob, job_id)
        if not job:
            return
        job.status = 'running'
        job.started_at = datetime.utcnow()
        db.session.commit()

    @staticmethod
    def merge_cli_parcial(job_id: str, res: dict) -> None:
        num = (res or {}).get('numero_processo')
        if not num:
            return
        job = db.session.get(CliJob, job_id)
        if not job:
            return
        bucket = dict(job.resultados_parciais_json or {})
        bucket[str(num).strip()] = {
            'numero_processo': num,
            'tribunal': res.get('tribunal'),
            'status': res.get('status'),
            'erro': res.get('erro'),
        }
        job.resultados_parciais_json = bucket
        flag_modified(job, 'resultados_parciais_json')
        db.session.commit()

    @staticmethod
    def is_cli_aborted(job_id: str) -> bool:
        job = db.session.get(CliJob, job_id)
        return bool(job and job.aborted)

    @staticmethod
    def request_cli_abort(job_id: str) -> bool:
        job = db.session.get(CliJob, job_id)
        if not job or job.status in ('completed', 'error', 'aborted', 'interrupted'):
            return False
        job.aborted = True
        job.status = 'aborting'
        job.error_message = 'Extração cancelada pelo utilizador'
        db.session.commit()
        return True

    @staticmethod
    def finish_cli_job(
        job_id: str,
        *,
        status: str,
        error: str | None = None,
        extracao_ids: list[str] | None = None,
        filenames: list[str] | None = None,
    ) -> None:
        job = db.session.get(CliJob, job_id)
        if not job:
            return
        job.status = status
        job.error_message = error
        job.extracao_ids_json = extracao_ids or []
        job.filenames_json = filenames or []
        job.finished_at = datetime.utcnow()
        db.session.commit()

    # --- Admin / startup ---

    @staticmethod
    def mark_stale_jobs_on_startup() -> None:
        msg = 'Servidor reiniciado — job interrompido.'
        n_scraping = (
            ScrapingJob.query.filter(ScrapingJob.status.in_(_ACTIVE_SCRAPING))
            .update(
                {
                    ScrapingJob.status: 'interrupted',
                    ScrapingJob.error_message: msg,
                    ScrapingJob.finished_at: datetime.utcnow(),
                },
                synchronize_session=False,
            )
        )
        n_cli = (
            CliJob.query.filter(CliJob.status.in_(_ACTIVE_CLI))
            .update(
                {
                    CliJob.status: 'interrupted',
                    CliJob.error_message: msg,
                    CliJob.finished_at: datetime.utcnow(),
                },
                synchronize_session=False,
            )
        )
        if n_scraping or n_cli:
            db.session.commit()
            logger.info(
                'Jobs interrompidos no arranque: %s scraping, %s CLI',
                n_scraping,
                n_cli,
            )

    @staticmethod
    def list_active_scraping_jobs() -> list[dict[str, Any]]:
        jobs = (
            ScrapingJob.query.filter(ScrapingJob.status.in_(_ACTIVE_SCRAPING))
            .order_by(ScrapingJob.started_at.desc())
            .all()
        )
        out = []
        for job in jobs:
            parciais = job.resultados_parciais_json or {}
            if not isinstance(parciais, dict):
                parciais = {}
            em_fila = processando = concluidos = 0
            for row in parciais.values():
                st = (row or {}).get('status', 'pendente')
                if st == 'pendente':
                    em_fila += 1
                elif st == 'processando':
                    processando += 1
                elif st in ('sucesso', 'erro'):
                    concluidos += 1
            total = job.total_processos
            if total:
                em_fila = max(0, total - processando - concluidos)
            out.append(
                {
                    'session_id': job.id,
                    'username': job.user.username if job.user else '',
                    'status': job.status,
                    'processos_em_fila': em_fila,
                    'processos_processando': processando,
                    'processos_concluidos': concluidos,
                    'total_processos': total,
                }
            )
        return out

    @staticmethod
    def list_active_cli_jobs() -> list[dict[str, Any]]:
        jobs = (
            CliJob.query.filter(CliJob.status.in_(_ACTIVE_CLI))
            .order_by(CliJob.created_at.desc())
            .all()
        )
        return [
            {
                'job_id': j.id,
                'username': j.user.username if j.user else '',
                'status': j.status,
                'tribunal_key': j.tribunal_key,
                'job_mode': j.job_mode,
                'total_processos': j.total_processos,
            }
            for j in jobs
        ]

    @staticmethod
    def get_scraping_sessions_snapshot() -> dict:
        """Compatibilidade com admin scraping-status (formato legado)."""
        import copy

        snapshot = {}
        for row in JobService.list_active_scraping_jobs():
            sid = row['session_id']
            job = db.session.get(ScrapingJob, sid)
            if not job:
                continue
            snapshot[sid] = {
                'status': job.status,
                'total_processos': job.total_processos,
                'resultados_parciais': job.resultados_parciais_json or {},
            }
        return copy.deepcopy(snapshot)
