from __future__ import annotations

from scrapers.consulta_cli_common import (
    mp_worker_consulta_chunk,
    normalizar_resultado,
)

TRIBUNAL_TJCE = "8.06"
TRIBUNAL_KEY = TRIBUNAL_TJCE
SLEEP_MODULE = "scrapers.tjce.scrapper"
CLI_CLASS_PATH = "scrapers.tjce.scrapper_cli:PJeScraperTJCECLI"
MOV_CLASS_PATH = "scrapers.tjce.scrapper_mov_cli:PJeScraperTJCEMovCLI"
POL_CLASS_PATH = "scrapers.tjce.scraper_polos_cli:PJeScraperTJCEPolosCLI"
SLUG = "tjce"
DESC_PLANILHAS = "Raspa TJCE (PJe) e gera planilhas raspada + tratada."
DESC_MOV = "TJCE (PJe): exporta só movimentações para Excel."
DESC_POL = "TJCE (PJe): partes e advogados por polo (Excel)."


def normalizar_resultado_scraper(numero_processo: str, raw: dict) -> dict:
    return normalizar_resultado(numero_processo, raw, TRIBUNAL_KEY)


def escala_sleep_scraper_tjce(fator: float):
    from scrapers.consulta_cli_common import escala_sleep_scraper_module

    return escala_sleep_scraper_module(SLEEP_MODULE, fator)


def mp_worker_tjce_chunk(payload: dict) -> list[tuple[int, dict]]:
    """Compatível com payloads antigos (preenche tribunal/sleep/classes se faltarem)."""
    p = dict(payload)
    p.setdefault("tribunal_key", TRIBUNAL_KEY)
    p.setdefault("sleep_module", SLEEP_MODULE)
    p.setdefault("cli_class_path", CLI_CLASS_PATH)
    p.setdefault("mov_class_path", MOV_CLASS_PATH)
    p.setdefault("pol_class_path", POL_CLASS_PATH)
    return mp_worker_consulta_chunk(p)
