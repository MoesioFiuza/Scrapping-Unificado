"""Inicialização da BD e importação única a partir dos JSON legados."""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models import Extracao, User
from config.settings import (
    ADMIN_EMAIL,
    ADMIN_PASSWORD,
    EXTRACOES_JSON_LEGACY,
    PROJECT_ROOT,
    USERS_JSON_LEGACY,
)

logger = logging.getLogger(__name__)


def init_database(app) -> None:
    with app.app_context():
        db.create_all()
        from app.services.job_service import JobService

        JobService.mark_stale_jobs_on_startup()
        _bootstrap_if_empty()


def _bootstrap_if_empty() -> None:
    if User.query.count() == 0:
        if USERS_JSON_LEGACY.is_file():
            imported = _import_users_from_json(USERS_JSON_LEGACY)
            logger.info("Importados %s utilizador(es) de %s", imported, USERS_JSON_LEGACY)
        elif ADMIN_EMAIL and ADMIN_PASSWORD:
            db.session.add(
                User(
                    username=ADMIN_EMAIL.strip().lower(),
                    password_hash=generate_password_hash(ADMIN_PASSWORD),
                    role='admin',
                )
            )
            db.session.commit()
            logger.info("Utilizador admin inicial criado a partir de variáveis de ambiente")
        else:
            logger.warning(
                "Nenhum utilizador na BD. Defina ADMIN_EMAIL/ADMIN_PASSWORD no .env "
                "ou execute: python scripts/migrate_json_to_db.py"
            )

    if Extracao.query.count() == 0 and EXTRACOES_JSON_LEGACY.is_file():
        imported = _import_extracoes_from_json(EXTRACOES_JSON_LEGACY)
        logger.info("Importadas %s extração(ões) de %s", imported, EXTRACOES_JSON_LEGACY)


def _import_users_from_json(path: Path) -> int:
    with open(path, encoding='utf-8') as f:
        data = json.load(f)

    count = 0
    for raw in data.get('users', []):
        username = (raw.get('username') or '').strip().lower()
        if not username:
            continue
        if User.query.filter_by(username=username).first():
            continue
        db.session.add(
            User(
                username=username,
                password_hash=raw['password_hash'],
                role=raw.get('role') or 'user',
            )
        )
        count += 1
    db.session.commit()
    return count


def _import_extracoes_from_json(path: Path) -> int:
    with open(path, encoding='utf-8') as f:
        data = json.load(f)

    count = 0
    for raw in data.get('extracoes', []):
        ext_id = str(raw.get('id') or '').strip()
        if not ext_id or Extracao.query.get(ext_id):
            continue

        username = (raw.get('username') or '').strip().lower()
        user = User.query.filter_by(username=username).first() if username else None
        if not user:
            logger.warning("Extração %s ignorada: utilizador '%s' não encontrado", ext_id, username)
            continue

        raw_fp = (raw.get('filepath') or '').replace('\\', '/')
        if raw_fp and not raw_fp.startswith('data/'):
            raw_fp = (Path('data') / 'output' / Path(raw_fp).name).as_posix()
        elif not raw_fp:
            raw_fp = (Path('data') / 'output' / raw.get('filename', '')).as_posix()

        try:
            data_criacao = datetime.fromisoformat(
                (raw.get('data_criacao') or '').replace('Z', '+00:00').split('+')[0]
            )
        except (ValueError, TypeError):
            data_criacao = datetime.utcnow()

        db.session.add(
            Extracao(
                id=ext_id,
                user_id=user.id,
                filename=raw.get('filename') or Path(raw_fp).name,
                filepath=raw_fp,
                tipo=raw.get('tipo') or 'desconhecido',
                total_processos=int(raw.get('total_processos') or 0),
                data_criacao=data_criacao,
            )
        )
        count += 1
    db.session.commit()
    return count


def migrate_json_to_database(force_users: bool = False, force_extracoes: bool = False) -> dict:
    """Script CLI: importa JSON legado para a BD."""
    stats = {'users': 0, 'extracoes': 0}
    if force_users or User.query.count() == 0:
        if USERS_JSON_LEGACY.is_file():
            stats['users'] = _import_users_from_json(USERS_JSON_LEGACY)
    if force_extracoes or Extracao.query.count() == 0:
        if EXTRACOES_JSON_LEGACY.is_file():
            stats['extracoes'] = _import_extracoes_from_json(EXTRACOES_JSON_LEGACY)
    return stats
