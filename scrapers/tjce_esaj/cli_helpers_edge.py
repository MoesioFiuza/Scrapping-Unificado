from __future__ import annotations

from scrapers.consulta_cli_common import normalizar_resultado

TRIBUNAL_KEY = "8.06_esaj"
SLEEP_MODULE = "scrapers.tjce_esaj.scraper"
CLI_CLASS_PATH = "scrapers.tjce_esaj.scraper_edge_cli:ESAJScraperTJCEEdgeCLI"
MOV_CLASS_PATH = "scrapers.tjce_esaj.scraper_mov_edge_cli:ESAJScraperTJCEMovEdgeCLI"
SLUG = "tjce_esaj"
DESC_PLANILHAS = "Raspa eSAJ TJCE (Edge) e gera planilhas raspada + tratada."
DESC_MOV = "eSAJ TJCE (Edge): exporta só movimentações para Excel."


def normalizar_resultado_scraper(numero_processo: str, raw: dict) -> dict:
    return normalizar_resultado(numero_processo, raw, TRIBUNAL_KEY)
