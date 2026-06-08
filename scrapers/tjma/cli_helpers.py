from __future__ import annotations

from scrapers.consulta_cli_common import normalizar_resultado

TRIBUNAL_KEY = "8.10"
SLEEP_MODULE = "scrapers.tjma.scraper"
CLI_CLASS_PATH = "scrapers.tjma.scraper_cli:PJeScraperTJMACLI"
MOV_CLASS_PATH = "scrapers.tjma.scraper_mov_cli:PJeScraperTJMAMovCLI"
SLUG = "tjma"
DESC_PLANILHAS = "Raspa TJMA (PJe) e gera planilhas raspada + tratada."
DESC_MOV = "TJMA (PJe): exporta só movimentações para Excel."


def normalizar_resultado_scraper(numero_processo: str, raw: dict) -> dict:
    return normalizar_resultado(numero_processo, raw, TRIBUNAL_KEY)
