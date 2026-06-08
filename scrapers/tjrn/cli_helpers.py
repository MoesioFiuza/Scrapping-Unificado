from __future__ import annotations

from scrapers.consulta_cli_common import normalizar_resultado

TRIBUNAL_KEY = "8.20"
SLEEP_MODULE = "scrapers.tjrn.scraper"
CLI_CLASS_PATH = "scrapers.tjrn.scraper_cli:PJeScraperTJRNCLI"
MOV_CLASS_PATH = "scrapers.tjrn.scraper_mov_cli:PJeScraperTJRNMovCLI"
SLUG = "tjrn"
DESC_PLANILHAS = "Raspa TJRN (PJe) e gera planilhas raspada + tratada."
DESC_MOV = "TJRN (PJe): exporta só movimentações para Excel."


def normalizar_resultado_scraper(numero_processo: str, raw: dict) -> dict:
    return normalizar_resultado(numero_processo, raw, TRIBUNAL_KEY)
