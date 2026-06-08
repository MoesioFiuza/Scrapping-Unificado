from __future__ import annotations

from scrapers.consulta_cli_common import normalizar_resultado

TRIBUNAL_KEY = "8.07"
SLEEP_MODULE = "scrapers.tjdft.scraper"
CLI_CLASS_PATH = "scrapers.tjdft.scraper_edge_cli:PJeScraperTJDFTEdgeCLI"
MOV_CLASS_PATH = "scrapers.tjdft.scraper_mov_edge_cli:PJeScraperTJDFTMovEdgeCLI"
SLUG = "tjdft"
DESC_PLANILHAS = "Raspa TJDFT (PJe, Edge) e gera planilhas raspada + tratada."
DESC_MOV = "TJDFT (PJe, Edge): exporta só movimentações para Excel."


def normalizar_resultado_scraper(numero_processo: str, raw: dict) -> dict:
    return normalizar_resultado(numero_processo, raw, TRIBUNAL_KEY)
