"""
CLI TJCE Edge — só movimentações: não altera scrapers/tjce/scrapper.py.

Mesma lógica que scrapper_mov_cli.py, com PJeScraperTJCEEdgeCLI (Edge).
"""
from __future__ import annotations

from scrapers.pje_somente_mov_mixin import PjeSomenteMovMixin
from scrapers.tjce.scrapper_edge_cli import PJeScraperTJCEEdgeCLI


class PJeScraperTJCEMovEdgeCLI(PjeSomenteMovMixin, PJeScraperTJCEEdgeCLI):
    pass
