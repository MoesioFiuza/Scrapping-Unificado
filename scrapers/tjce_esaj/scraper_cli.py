from __future__ import annotations

from scrapers.pje_chrome_cli_mixin import PjeChromeCliMixin
from scrapers.tjce_esaj.scraper import ESAJScraperTJCE


class ESAJScraperTJCECLI(ESAJScraperTJCE, PjeChromeCliMixin):
    """eSAJ TJCE: Chrome headless=new / retry de driver."""

    pass
