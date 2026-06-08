from __future__ import annotations

from scrapers.pje_edge_cli_mixin import PjeEdgeCliMixin
from scrapers.tjma.scraper import PJeScraperTJMA


class PJeScraperTJMAEdgeCLI(PjeEdgeCliMixin, PJeScraperTJMA):
    pass
