from __future__ import annotations

from scrapers.pje_polos_adv_mixin import PjePolosAdvMixin
from scrapers.tjce.scrapper_edge_cli import PJeScraperTJCEEdgeCLI


class PJeScraperTJCEPolosEdgeCLI(PjePolosAdvMixin, PJeScraperTJCEEdgeCLI):
    """Edge: polos, partes e advogados (sem movimentações)."""

    pass
