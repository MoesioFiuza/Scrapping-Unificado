from __future__ import annotations

from scrapers.pje_edge_cli_mixin import PjeEdgeCliMixin
from scrapers.tjce.scrapper import PJeScraperTJCE


class PJeScraperTJCEEdgeCLI(PjeEdgeCliMixin, PJeScraperTJCE):
    """Mesmo fluxo TJCE (PJe); driver = Microsoft Edge (mixin antes da base no MRO)."""

    pass
