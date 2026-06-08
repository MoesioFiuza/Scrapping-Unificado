"""eSAJ TJAL: após a consulta, extrai só movimentações."""

from __future__ import annotations

import traceback

from scrapers.tjal.scraper_cli import ESAJScraperTJALCLI


class ESAJScraperTJALMovCLI(ESAJScraperTJALCLI):
    def _extrair_dados_processo(self) -> dict:
        dados: dict = {}
        try:
            dados["movimentacoes"] = self._extrair_movimentacoes()
            print(f"Movimentações (modo leve): {len(dados.get('movimentacoes', []))} itens.")
        except Exception as e:
            print(f"Erro ao extrair movimentações: {e}")
            print(traceback.format_exc())
            dados["erro_extracao"] = str(e)
        return dados
