from __future__ import annotations

from scrapers.pje_chrome_cli_mixin import PjeChromeCliMixin
from scrapers.tjrj.scraper import PJeScraperTJRJ


class PJeScraperTJRJCLI(PJeScraperTJRJ, PjeChromeCliMixin):
    pass
