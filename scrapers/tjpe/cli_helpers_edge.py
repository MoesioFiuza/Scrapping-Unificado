from __future__ import annotations

from scrapers.consulta_cli_common import normalizar_resultado

TRIBUNAL_KEY = "8.17"
SLEEP_MODULE = "scrapers.tjpe.scraper"
CLI_CLASS_PATH = "scrapers.tjpe.scraper_edge_cli:PJeScraperTJPEEdgeCLI"
MOV_CLASS_PATH = "scrapers.tjpe.scraper_mov_edge_cli:PJeScraperTJPEMovEdgeCLI"
SLUG = "tjpe"
DESC_PLANILHAS = "Raspa TJPE (PJe, Edge) e gera planilhas raspada + tratada."
DESC_MOV = "TJPE (PJe, Edge): exporta só movimentações para Excel."


def normalizar_resultado_scraper(numero_processo: str, raw: dict) -> dict:
    return normalizar_resultado(numero_processo, raw, TRIBUNAL_KEY)
