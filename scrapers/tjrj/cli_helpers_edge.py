from __future__ import annotations

from scrapers.consulta_cli_common import normalizar_resultado

TRIBUNAL_KEY = "8.19"
SLEEP_MODULE = "scrapers.tjrj.scraper"
CLI_CLASS_PATH = "scrapers.tjrj.scraper_edge_cli:PJeScraperTJRJEdgeCLI"
MOV_CLASS_PATH = "scrapers.tjrj.scraper_mov_edge_cli:PJeScraperTJRJMovEdgeCLI"
POL_CLASS_PATH = "scrapers.tjrj.scraper_polos_edge_cli:PJeScraperTJRJPolosEdgeCLI"
SLUG = "tjrj"
DESC_PLANILHAS = "Raspa TJRJ (PJe, Edge) e gera planilhas raspada + tratada."
DESC_MOV = "TJRJ (PJe, Edge): exporta só movimentações para Excel."
DESC_POL = "TJRJ (PJe, Edge): partes e advogados por polo (Excel)."


def normalizar_resultado_scraper(numero_processo: str, raw: dict) -> dict:
    return normalizar_resultado(numero_processo, raw, TRIBUNAL_KEY)
