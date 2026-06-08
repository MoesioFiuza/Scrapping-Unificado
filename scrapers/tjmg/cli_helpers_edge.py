from __future__ import annotations

from scrapers.consulta_cli_common import normalizar_resultado

TRIBUNAL_KEY = "8.13"
SLEEP_MODULE = "scrapers.tjmg.scraper"
CLI_CLASS_PATH = "scrapers.tjmg.scraper_edge_cli:PJeScraperTJMGEdgeCLI"
MOV_CLASS_PATH = "scrapers.tjmg.scraper_mov_edge_cli:PJeScraperTJMGMovEdgeCLI"
SLUG = "tjmg"
DESC_PLANILHAS = "Raspa TJMG (PJe, Edge) e gera planilhas raspada + tratada."
DESC_MOV = "TJMG (PJe, Edge): exporta só movimentações para Excel."


def normalizar_resultado_scraper(numero_processo: str, raw: dict) -> dict:
    return normalizar_resultado(numero_processo, raw, TRIBUNAL_KEY)
