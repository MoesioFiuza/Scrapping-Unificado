from __future__ import annotations

from scrapers.consulta_cli_common import normalizar_resultado

TRIBUNAL_KEY = "8.02"
SLEEP_MODULE = "scrapers.tjal.scraper"
CLI_CLASS_PATH = "scrapers.tjal.scraper_edge_cli:ESAJScraperTJALEdgeCLI"
MOV_CLASS_PATH = "scrapers.tjal.scraper_mov_edge_cli:ESAJScraperTJALMovEdgeCLI"
SLUG = "tjal_esaj"
DESC_PLANILHAS = "Raspa eSAJ TJAL (Edge) e gera planilhas raspada + tratada."
DESC_MOV = "eSAJ TJAL (Edge): exporta só movimentações para Excel."


def normalizar_resultado_scraper(numero_processo: str, raw: dict) -> dict:
    return normalizar_resultado(numero_processo, raw, TRIBUNAL_KEY)
