from __future__ import annotations

from scrapers.pje_chrome_cli_mixin import PjeChromeCliMixin
from scrapers.tjpe.scraper import PJeScraperTJPE


class PJeScraperTJPECLI(PJeScraperTJPE, PjeChromeCliMixin):
    pass
