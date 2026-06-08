"""Métricas agregadas para o Dashboard Escritório (admin)."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import func

from app.extensions import db
from app.models import CliJob, Extracao, ScrapingJob, User
from app.services.job_service import JobService
from config.tribunais import TRIBUNAIS_MAP, identificar_tribunal_por_processo

_NOME_PARA_CODIGO = {info.get("nome", ""): codigo for codigo, info in TRIBUNAIS_MAP.items()}


def _nome_tribunal(codigo: str | None) -> str:
    if not codigo:
        return "Desconhecido"
    info = TRIBUNAIS_MAP.get(codigo)
    return info.get("nome", codigo) if info else codigo


def _tribunal_from_filename(filename: str) -> str | None:
    if not filename:
        return None
    prefix = filename.split("_", 1)[0]
    return _NOME_PARA_CODIGO.get(prefix)


def _periodo_stats(desde: datetime) -> dict[str, int]:
    row = (
        db.session.query(
            func.count(Extracao.id),
            func.coalesce(func.sum(Extracao.total_processos), 0),
        )
        .filter(Extracao.data_criacao >= desde)
        .one()
    )
    extracoes = int(row[0] or 0)
    processos = int(row[1] or 0)

    n_scraping = ScrapingJob.query.filter(
        ScrapingJob.status == "completed",
        ScrapingJob.finished_at >= desde,
    ).count()
    n_cli = CliJob.query.filter(
        CliJob.status == "completed",
        CliJob.finished_at >= desde,
    ).count()

    return {
        "extracoes": extracoes,
        "processos": processos,
        "jobs_concluidos": n_scraping + n_cli,
    }


def _contar_parciais(parciais: dict | list | None) -> tuple[int, int]:
    sucesso = erro = 0
    if not parciais:
        return sucesso, erro
    items = parciais.values() if isinstance(parciais, dict) else parciais
    for row in items:
        if not isinstance(row, dict):
            continue
        st = (row.get("status") or "").lower()
        if st == "sucesso":
            sucesso += 1
        elif st == "erro":
            erro += 1
    return sucesso, erro


def _tribunal_from_scraping_job(job: ScrapingJob) -> str | None:
    processos = job.processos_json or []
    if processos and isinstance(processos, list):
        first = processos[0]
        if isinstance(first, dict):
            num = first.get("numero_processo")
            if num:
                return identificar_tribunal_por_processo(str(num))
    parciais = job.resultados_parciais_json or {}
    if isinstance(parciais, dict) and parciais:
        first_row = next(iter(parciais.values()), None)
        if isinstance(first_row, dict):
            trib = first_row.get("tribunal")
            if trib and trib in TRIBUNAIS_MAP:
                return trib
            num = first_row.get("numero_processo")
            if num:
                return identificar_tribunal_por_processo(str(num))
    return None


class DashboardEscritorioService:
    @staticmethod
    def build(*, dias_taxa: int = 30) -> dict[str, Any]:
        agora = datetime.utcnow()
        inicio_hoje = agora.replace(hour=0, minute=0, second=0, microsecond=0)
        inicio_semana = agora - timedelta(days=7)
        inicio_mes = agora - timedelta(days=30)
        inicio_taxa = agora - timedelta(days=max(1, min(dias_taxa, 365)))

        periodos = {
            "hoje": _periodo_stats(inicio_hoje),
            "semana": _periodo_stats(inicio_semana),
            "mes": _periodo_stats(inicio_mes),
        }

        # Top tribunais (últimos 30 dias) — extracoes + jobs CLI
        trib_extracoes: dict[str, int] = defaultdict(int)
        trib_processos: dict[str, int] = defaultdict(int)

        extracoes_mes = Extracao.query.filter(Extracao.data_criacao >= inicio_mes).all()
        for ext in extracoes_mes:
            codigo = _tribunal_from_filename(ext.filename)
            if not codigo and ext.tipo == "dataweb":
                codigo = "dataweb"
            if codigo:
                trib_extracoes[codigo] += 1
                trib_processos[codigo] += int(ext.total_processos or 0)

        cli_mes = CliJob.query.filter(CliJob.created_at >= inicio_mes).all()
        for job in cli_mes:
            codigo = job.tribunal_key or "desconhecido"
            trib_extracoes[codigo] += 1
            trib_processos[codigo] += int(job.total_processos or 0)

        top_tribunais = sorted(
            [
                {
                    "codigo": codigo,
                    "nome": "DataWeb" if codigo == "dataweb" else _nome_tribunal(codigo),
                    "extracoes": trib_extracoes[codigo],
                    "processos": trib_processos[codigo],
                }
                for codigo in trib_extracoes
            ],
            key=lambda x: (-x["extracoes"], -x["processos"]),
        )[:10]

        # Taxa de sucesso por tribunal (jobs concluídos com parciais)
        taxa_buckets: dict[str, dict[str, int]] = defaultdict(lambda: {"sucesso": 0, "erro": 0})

        scraping_done = ScrapingJob.query.filter(
            ScrapingJob.status == "completed",
            ScrapingJob.finished_at >= inicio_taxa,
        ).all()
        for job in scraping_done:
            codigo = _tribunal_from_scraping_job(job) or "desconhecido"
            s, e = _contar_parciais(job.resultados_parciais_json)
            if s or e:
                taxa_buckets[codigo]["sucesso"] += s
                taxa_buckets[codigo]["erro"] += e

        cli_done = CliJob.query.filter(
            CliJob.status == "completed",
            CliJob.finished_at >= inicio_taxa,
        ).all()
        for job in cli_done:
            codigo = job.tribunal_key or "desconhecido"
            s, e = _contar_parciais(job.resultados_parciais_json)
            if s or e:
                taxa_buckets[codigo]["sucesso"] += s
                taxa_buckets[codigo]["erro"] += e

        taxa_sucesso_por_tribunal = []
        for codigo, counts in sorted(
            taxa_buckets.items(),
            key=lambda kv: -(kv[1]["sucesso"] + kv[1]["erro"]),
        ):
            total = counts["sucesso"] + counts["erro"]
            taxa_sucesso_por_tribunal.append(
                {
                    "codigo": codigo,
                    "nome": _nome_tribunal(codigo),
                    "sucesso": counts["sucesso"],
                    "erro": counts["erro"],
                    "taxa_pct": round(100.0 * counts["sucesso"] / total, 1) if total else 0.0,
                }
            )

        # Utilizadores mais activos (30 dias)
        rows = (
            db.session.query(
                User.username,
                User.last_login_at,
                func.count(Extracao.id).label("extracoes"),
                func.coalesce(func.sum(Extracao.total_processos), 0).label("processos"),
                func.max(Extracao.data_criacao).label("ultima_extracao"),
            )
            .join(Extracao, Extracao.user_id == User.id)
            .filter(Extracao.data_criacao >= inicio_mes)
            .group_by(User.id, User.username, User.last_login_at)
            .order_by(func.count(Extracao.id).desc())
            .limit(10)
            .all()
        )
        utilizadores_ativos = [
            {
                "username": r.username,
                "extracoes_mes": int(r.extracoes or 0),
                "processos_mes": int(r.processos or 0),
                "ultima_extracao": r.ultima_extracao.isoformat() if r.ultima_extracao else None,
                "ultimo_login": r.last_login_at.isoformat() if r.last_login_at else None,
            }
            for r in rows
        ]

        jobs_em_curso = {
            "scraping": JobService.list_active_scraping_jobs(),
            "cli": JobService.list_active_cli_jobs(),
        }

        taxa_global_s = sum(t["sucesso"] for t in taxa_sucesso_por_tribunal)
        taxa_global_e = sum(t["erro"] for t in taxa_sucesso_por_tribunal)
        taxa_global_total = taxa_global_s + taxa_global_e

        return {
            "gerado_em": agora.isoformat(),
            "dias_taxa_sucesso": dias_taxa,
            "periodos": periodos,
            "taxa_sucesso_global": {
                "sucesso": taxa_global_s,
                "erro": taxa_global_e,
                "taxa_pct": round(100.0 * taxa_global_s / taxa_global_total, 1)
                if taxa_global_total
                else None,
            },
            "top_tribunais": top_tribunais,
            "taxa_sucesso_por_tribunal": taxa_sucesso_por_tribunal,
            "utilizadores_ativos": utilizadores_ativos,
            "jobs_em_curso": jobs_em_curso,
            "total_jobs_ativos": len(jobs_em_curso["scraping"]) + len(jobs_em_curso["cli"]),
        }
