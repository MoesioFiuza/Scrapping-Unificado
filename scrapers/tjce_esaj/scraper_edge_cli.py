from __future__ import annotations

from scrapers.pje_edge_cli_mixin import PjeEdgeCliMixin
from scrapers.tjce_esaj.scraper import ESAJScraperTJCE


class ESAJScraperTJCEEdgeCLI(PjeEdgeCliMixin, ESAJScraperTJCE):
    """eSAJ TJCE com Microsoft Edge."""

    pass
