from __future__ import annotations

from scrapers.pje_chrome_cli_mixin import PjeChromeCliMixin
from scrapers.tjdft.scraper import PJeScraperTJDFT


class PJeScraperTJDFTCLI(PJeScraperTJDFT, PjeChromeCliMixin):
    pass
