from __future__ import annotations

from scrapers.pje_chrome_cli_mixin import PjeChromeCliMixin
from scrapers.tjma.scraper import PJeScraperTJMA


class PJeScraperTJMACLI(PJeScraperTJMA, PjeChromeCliMixin):
    pass
