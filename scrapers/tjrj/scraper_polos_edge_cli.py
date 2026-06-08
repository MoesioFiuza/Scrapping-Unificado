from __future__ import annotations

from scrapers.pje_polos_adv_mixin import PjePolosAdvMixin
from scrapers.tjrj.scraper_edge_cli import PJeScraperTJRJEdgeCLI


class PJeScraperTJRJPolosEdgeCLI(PjePolosAdvMixin, PJeScraperTJRJEdgeCLI):
    """Edge + consulta pública TJRJ: polo ativo, polo passivo e advogados (sem movimentações completas)."""

    pass
