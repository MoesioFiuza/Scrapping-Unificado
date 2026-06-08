"""
CLI TJCE — só movimentações: não altera scrapers/tjce/scrapper.py.

Sobrescreve apenas _extrair_dados_processo para pular polos, documentos e dados básicos;
o fluxo raspar_processo (consulta, link, detalhe) permanece o da classe base via PJeScraperTJCECLI.
"""
from __future__ import annotations

from scrapers.pje_somente_mov_mixin import PjeSomenteMovMixin
from scrapers.tjce.scrapper_cli import PJeScraperTJCECLI


class PJeScraperTJCEMovCLI(PjeSomenteMovMixin, PJeScraperTJCECLI):
    pass
