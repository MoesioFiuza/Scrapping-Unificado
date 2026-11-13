"""Acompanhamento de uso: Valença Suite (enviado pelo app) e extrações do site."""
from __future__ import annotations

from datetime import datetime

from app.extensions import db
from app.models import CliJob, ScrapingJob, UsoRegistro, User
from app.services.dashboard_escritorio_service import _contar_parciais


def _iso(valor) -> str | None:
    if not valor:
        return None
    return valor.isoformat() + "Z"


def registrar(
    user: User,
    *,
    origem: str,
    servico: str,
    maquina: str | None = None,
    total: int = 0,
    sucesso: int = 0,
    erro: int = 0,
    iniciado_em: datetime | None = None,
) -> None:
    db.session.add(
        UsoRegistro(
            user_id=user.id,
            origem=(origem or "valenca_suite")[:32],
            servico=(servico or "Serviço")[:160],
            maquina=(maquina or "")[:255] or None,
            total=max(0, int(total or 0)),
            sucesso=max(0, int(sucesso or 0)),
            erro=max(0, int(erro or 0)),
            iniciado_em=iniciado_em,
        )
    )
    db.session.commit()


def _linha_uso(row: UsoRegistro, login) -> dict:
    return {
        "quando": _iso(row.criado_em),
        "usuario": row.user.username if row.user else "",
        "ultimo_login": _iso(login),
        "origem": "Valença Suite" if row.origem == "valenca_suite" else "Site",
        "servico": row.servico,
        "total": row.total,
        "sucesso": row.sucesso,
        "erro": row.erro,
        "maquina": row.maquina or "",
    }


def _linha_job(job, usuario: str, login, servico: str) -> dict:
    sucesso, erro = _contar_parciais(job.resultados_parciais_json)
    quando = job.finished_at or job.started_at or getattr(job, "created_at", None)
    return {
        "quando": _iso(quando),
        "usuario": usuario,
        "ultimo_login": _iso(login),
        "origem": "Site",
        "servico": servico,
        "total": int(job.total_processos or 0),
        "sucesso": sucesso,
        "erro": erro,
        "maquina": "",
    }


def listar(limite: int = 400) -> dict:
    usos = (
        UsoRegistro.query.order_by(UsoRegistro.criado_em.desc()).limit(limite).all()
    )
    logins = {u.id: u.last_login_at for u in User.query.all()}
    nomes = {u.id: u.username for u in User.query.all()}

    linhas = [_linha_uso(row, logins.get(row.user_id)) for row in usos]

    for job in ScrapingJob.query.order_by(ScrapingJob.started_at.desc()).limit(120).all():
        linhas.append(
            _linha_job(job, nomes.get(job.user_id, ""), logins.get(job.user_id), "Extração no site")
        )
    for job in CliJob.query.order_by(CliJob.created_at.desc()).limit(120).all():
        tribunal = (job.tribunal_key or "cli").upper()
        linhas.append(
            _linha_job(
                job,
                nomes.get(job.user_id, ""),
                logins.get(job.user_id),
                f"CLI {tribunal}",
            )
        )

    linhas.sort(key=lambda item: item.get("quando") or "", reverse=True)
    linhas = linhas[:limite]

    por_usuario: dict[str, dict] = {}
    for item in linhas:
        if item["servico"] == "Login":
            continue
        nome = item["usuario"] or "—"
        atual = por_usuario.setdefault(
            nome,
            {
                "usuario": nome,
                "ultimo_login": item["ultimo_login"],
                "total": 0,
                "sucesso": 0,
                "erro": 0,
                "vezes": 0,
            },
        )
        atual["total"] += item["total"]
        atual["sucesso"] += item["sucesso"]
        atual["erro"] += item["erro"]
        atual["vezes"] += 1
        if item["ultimo_login"] and (
            not atual["ultimo_login"] or item["ultimo_login"] > atual["ultimo_login"]
        ):
            atual["ultimo_login"] = item["ultimo_login"]

    resumo = sorted(por_usuario.values(), key=lambda item: item["vezes"], reverse=True)
    return {"linhas": linhas, "resumo": resumo}
