from __future__ import annotations

from scrapers.pje_chrome_cli_mixin import PjeChromeCliMixin
from scrapers.tjrn.scraper import PJeScraperTJRN


class PJeScraperTJRNCLI(PJeScraperTJRN, PjeChromeCliMixin):
    pass
