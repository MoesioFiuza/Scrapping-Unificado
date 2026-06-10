"""Detecção de sinais de encerramento em movimentações processuais."""

from __future__ import annotations

import unicodedata

SINAIS_ENCERRAMENTO: tuple[str, ...] = (
    "ARQUIVADO DEFINITIVAMENTE",
    "BAIXA DEFINITIVA",
    "ARQUIVADOS OS AUTOS DEFINITIVAMENTE",
)


def normalizar_texto(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(s.upper().split())


def _formatar_data_hora(mov: dict) -> str | None:
    data = (mov.get("data") or "").strip()
    hora = (mov.get("hora") or "").strip()
    if data and hora:
        return f"{data} {hora}"
    return data or hora or None


def extrair_movimentacoes_com_sinal(movimentacoes: list[dict]) -> tuple[list[dict], list[str]]:
    com_sinal: list[dict] = []
    todos_sinais: list[str] = []

    for mov in movimentacoes or []:
        texto = normalizar_texto(
            f"{mov.get('descricao') or ''} {mov.get('movimento') or ''}"
        )
        bateu = [s for s in SINAIS_ENCERRAMENTO if s in texto]
        if not bateu:
            continue
        com_sinal.append(
            {
                "data": mov.get("data") or None,
                "hora": mov.get("hora") or None,
                "data_hora": _formatar_data_hora(mov),
                "descricao": mov.get("descricao") or "",
                "movimento": mov.get("movimento") or mov.get("descricao") or "",
                "documento": mov.get("documento") or "",
                "sinais": bateu,
            }
        )
        todos_sinais.extend(bateu)

    return com_sinal, list(dict.fromkeys(todos_sinais))


def analisar_processo(res: dict) -> dict:
    num = res.get("numero_processo")
    if res.get("status") != "sucesso" or not res.get("dados"):
        return {
            "numero_processo": num,
            "status": res.get("status") or "erro",
            "erro": res.get("erro"),
            "encerrado": False,
            "total_movimentacoes": 0,
            "total_com_sinal": 0,
            "sinais_encontrados": [],
            "movimentacoes_com_sinal": [],
        }

    movs = res["dados"].get("movimentacoes") or []
    com_sinal, sinais = extrair_movimentacoes_com_sinal(movs)
    return {
        "numero_processo": num,
        "status": "sucesso",
        "erro": None,
        "encerrado": len(com_sinal) > 0,
        "total_movimentacoes": len(movs),
        "total_com_sinal": len(com_sinal),
        "sinais_encontrados": sinais,
        "movimentacoes_com_sinal": com_sinal,
    }


def resumo_parcial(processo: dict) -> dict:
    """Versão leve para polling (sem lista completa de movimentações com sinal)."""
    return {
        "numero_processo": processo.get("numero_processo"),
        "status": processo.get("status"),
        "erro": processo.get("erro"),
        "encerrado": processo.get("encerrado", False),
        "total_movimentacoes": processo.get("total_movimentacoes", 0),
        "total_com_sinal": processo.get("total_com_sinal", 0),
        "sinais_encontrados": processo.get("sinais_encontrados") or [],
    }


def montar_resultado_job(tribunal_key: str, workers: int, resultados: list[dict]) -> dict:
    from config.tribunais import TRIBUNAIS_MAP

    processos = [analisar_processo(r) for r in resultados]
    return {
        "tribunal_key": tribunal_key,
        "tribunal_nome": TRIBUNAIS_MAP.get(tribunal_key, {}).get("nome", tribunal_key),
        "workers": workers,
        "total_processos": len(processos),
        "processos_encerrados": sum(1 for p in processos if p.get("encerrado")),
        "processos": processos,
    }
