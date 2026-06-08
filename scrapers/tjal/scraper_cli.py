from __future__ import annotations

from scrapers.pje_chrome_cli_mixin import PjeChromeCliMixin
from scrapers.tjal.scraper import ESAJScraperTJAL


class ESAJScraperTJALCLI(ESAJScraperTJAL, PjeChromeCliMixin):
    """eSAJ TJAL: Chrome headless=new / retry de driver (igual aos outros CLIs)."""

    pass
