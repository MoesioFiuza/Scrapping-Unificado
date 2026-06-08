
from __future__ import annotations

from scrapers.pje_chrome_cli_mixin import PjeChromeCliMixin
from scrapers.tjce.scrapper import PJeScraperTJCE


class PJeScraperTJCECLI(PJeScraperTJCE, PjeChromeCliMixin):
    pass
