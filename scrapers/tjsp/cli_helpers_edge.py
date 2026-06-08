from __future__ import annotations

from scrapers.consulta_cli_common import normalizar_resultado

TRIBUNAL_KEY = "8.26"
SLEEP_MODULE = "scrapers.tjsp.scraper"
CLI_CLASS_PATH = "scrapers.tjsp.scraper_edge_cli:ESAJScraperTJSPEdgeCLI"
MOV_CLASS_PATH = "scrapers.tjsp.scraper_mov_edge_cli:ESAJScraperTJSPMovEdgeCLI"
SLUG = "tjsp_esaj"
DESC_PLANILHAS = "Raspa eSAJ TJSP (Edge) e gera planilhas raspada + tratada."
DESC_MOV = "eSAJ TJSP (Edge): exporta só movimentações para Excel."


def normalizar_resultado_scraper(numero_processo: str, raw: dict) -> dict:
    return normalizar_resultado(numero_processo, raw, TRIBUNAL_KEY)
