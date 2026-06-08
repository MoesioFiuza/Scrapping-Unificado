from __future__ import annotations

from scrapers.pje_chrome_cli_mixin import PjeChromeCliMixin
from scrapers.tjsp.scraper import ESAJScraperTJSP


class ESAJScraperTJSPCLI(ESAJScraperTJSP, PjeChromeCliMixin):
    """eSAJ TJSP: mesmo Chrome headless=new / retry de driver que nos tribunais PJe."""

    pass
