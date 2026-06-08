"""eSAJ TJSP: após a consulta, extrai só movimentações (sem polos/dados básicos no dict)."""

from __future__ import annotations

import traceback

from scrapers.tjsp.scraper_cli import ESAJScraperTJSPCLI


class ESAJScraperTJSPMovCLI(ESAJScraperTJSPCLI):
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
