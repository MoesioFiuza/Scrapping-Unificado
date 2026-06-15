from __future__ import annotations

import logging
import math
import uuid
from datetime import datetime

from app.extensions import db
from app.models import DataWebJob, User
from config.settings import DATAWEB_MAX_CNJS

logger = logging.getLogger(__name__)

_ACTIVE = ('queued', 'running')


class DataWebJobService:
    @staticmethod
    def get_job(job_id: str) -> DataWebJob | None:
        return db.session.get(DataWebJob, job_id)

    @staticmethod
    def user_id_for_username(username: str) -> int | None:
        user = User.query.filter_by(username=username.strip().lower()).first()
        return user.id if user else None

    @staticmethod
    def assert_access(job_id: str, username: str, is_admin: bool) -> DataWebJob | None:
        job = db.session.get(DataWebJob, job_id)
        if not job:
            return None
        if not is_admin and job.user.username != username.strip().lower():
            return None
        return job

    @staticmethod
    def create_job(user_id: int, cnjs: list[str]) -> DataWebJob:
        total_lotes = max(1, math.ceil(len(cnjs) / DATAWEB_MAX_CNJS))
        job = DataWebJob(
            id=str(uuid.uuid4()),
            user_id=user_id,
            cnjs_json=cnjs,
            status='queued',
            total_cnjs=len(cnjs),
            total_lotes=total_lotes,
        )
        db.session.add(job)
        db.session.commit()
        return job

    @staticmethod
    def set_running(job_id: str) -> None:
        job = db.session.get(DataWebJob, job_id)
        if not job:
            return
        job.status = 'running'
        job.started_at = datetime.utcnow()
        db.session.commit()

    @staticmethod
    def set_lote(job_id: str, lote_atual: int) -> None:
        job = db.session.get(DataWebJob, job_id)
        if not job:
            return
        job.lote_atual = lote_atual
        db.session.commit()

    @staticmethod
    def finish_success(job_id: str, *, extracao_id: str, filename: str) -> None:
        job = db.session.get(DataWebJob, job_id)
        if not job:
            return
        job.status = 'completed'
        job.extracao_id = extracao_id
        job.filename = filename
        job.lote_atual = job.total_lotes
        job.finished_at = datetime.utcnow()
        db.session.commit()

    @staticmethod
    def finish_error(job_id: str, error: str) -> None:
        job = db.session.get(DataWebJob, job_id)
        if not job:
            return
        job.status = 'error'
        job.error_message = error
        job.finished_at = datetime.utcnow()
        db.session.commit()

    @staticmethod
    def mark_stale_on_startup() -> None:
        stale = DataWebJob.query.filter(DataWebJob.status.in_(_ACTIVE)).all()
        for job in stale:
            job.status = 'interrupted'
            job.error_message = 'Serviço reiniciado durante o processamento.'
            job.finished_at = datetime.utcnow()
        if stale:
            db.session.commit()
            logger.info('Marcados %s job(s) DataWeb como interrupted', len(stale))
