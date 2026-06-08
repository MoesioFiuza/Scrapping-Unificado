from __future__ import annotations

from scrapers.consulta_cli_common import normalizar_resultado

TRIBUNAL_KEY = "8.19"
SLEEP_MODULE = "scrapers.tjrj.scraper"
CLI_CLASS_PATH = "scrapers.tjrj.scraper_cli:PJeScraperTJRJCLI"
MOV_CLASS_PATH = "scrapers.tjrj.scraper_mov_cli:PJeScraperTJRJMovCLI"
SLUG = "tjrj"
DESC_PLANILHAS = "Raspa TJRJ (PJe) e gera planilhas raspada + tratada."
DESC_MOV = "TJRJ (PJe): exporta só movimentações para Excel."


def normalizar_resultado_scraper(numero_processo: str, raw: dict) -> dict:
    return normalizar_resultado(numero_processo, raw, TRIBUNAL_KEY)
