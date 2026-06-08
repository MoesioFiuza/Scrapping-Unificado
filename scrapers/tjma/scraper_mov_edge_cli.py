from __future__ import annotations

from scrapers.pje_somente_mov_mixin import PjeSomenteMovMixin
from scrapers.tjma.scraper_edge_cli import PJeScraperTJMAEdgeCLI


class PJeScraperTJMAMovEdgeCLI(PjeSomenteMovMixin, PJeScraperTJMAEdgeCLI):
    pass
