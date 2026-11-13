"""Falhas de processo enviadas pelo Valença Suite."""
from __future__ import annotations

from app.extensions import db
from app.models import ErroRegistro, LogExecucao, User


def _iso(valor) -> str | None:
    if not valor:
        return None
    return valor.isoformat() + "Z"


def registrar(
    user: User,
    *,
    servico: str,
    cnj: str,
    erro: str,
    maquina: str | None = None,
    versao: str | None = None,
) -> None:
    db.session.add(
        ErroRegistro(
            user_id=user.id,
            servico=(servico or "Valença Suite")[:160],
            cnj=(cnj or "")[:80],
            erro=(erro or "")[:2000],
            maquina=(maquina or "")[:255] or None,
            versao=(versao or "")[:32] or None,
        )
    )
    db.session.commit()


def listar(limite: int = 400) -> dict:
    linhas = (
        ErroRegistro.query.order_by(ErroRegistro.criado_em.desc()).limit(limite).all()
    )
    return {
        "linhas": [
            {
                "quando": _iso(row.criado_em),
                "usuario": row.user.username if row.user else "",
                "servico": row.servico,
                "cnj": row.cnj,
                "erro": row.erro,
                "maquina": row.maquina or "",
                "versao": row.versao or "",
            }
            for row in linhas
        ]
    }


def registrar_log(
    user: User,
    *,
    servico: str,
    texto: str,
    maquina: str | None = None,
    versao: str | None = None,
) -> None:
    db.session.add(
        LogExecucao(
            user_id=user.id,
            servico=(servico or "Valença Suite")[:160],
            maquina=(maquina or "")[:255] or None,
            versao=(versao or "")[:32] or None,
            texto=(texto or "")[:200_000],
        )
    )
    db.session.commit()


def listar_logs(limite: int = 40) -> dict:
    linhas = (
        LogExecucao.query.order_by(LogExecucao.criado_em.desc()).limit(limite).all()
    )
    return {
        "logs": [
            {
                "id": row.id,
                "quando": _iso(row.criado_em),
                "usuario": row.user.username if row.user else "",
                "servico": row.servico,
                "maquina": row.maquina or "",
                "versao": row.versao or "",
            }
            for row in linhas
        ]
    }


def obter_log(log_id: int) -> dict | None:
    row = LogExecucao.query.filter_by(id=log_id).first()
    if row is None:
        return None
    return {
        "id": row.id,
        "quando": _iso(row.criado_em),
        "usuario": row.user.username if row.user else "",
        "servico": row.servico,
        "texto": row.texto,
    }
