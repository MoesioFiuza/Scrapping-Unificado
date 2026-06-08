from __future__ import annotations

from scrapers.pje_polos_adv_mixin import PjePolosAdvMixin
from scrapers.tjce.scrapper_cli import PJeScraperTJCECLI


class PJeScraperTJCEPolosCLI(PjePolosAdvMixin, PJeScraperTJCECLI):
    """Chrome: polos, partes e advogados (sem movimentações)."""

    pass
