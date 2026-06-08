from __future__ import annotations

from scrapers.pje_edge_cli_mixin import PjeEdgeCliMixin
from scrapers.tjal.scraper import ESAJScraperTJAL


class ESAJScraperTJALEdgeCLI(PjeEdgeCliMixin, ESAJScraperTJAL):
    """eSAJ TJAL com Microsoft Edge."""

    pass
