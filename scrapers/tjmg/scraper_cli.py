from __future__ import annotations

from scrapers.pje_chrome_cli_mixin import PjeChromeCliMixin
from scrapers.tjmg.scraper import PJeScraperTJMG


class PJeScraperTJMGCLI(PJeScraperTJMG, PjeChromeCliMixin):
    pass
