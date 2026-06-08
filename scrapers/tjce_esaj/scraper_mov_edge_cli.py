"""eSAJ TJCE Edge: após a consulta, extrai só movimentações."""

from __future__ import annotations

import traceback

from scrapers.tjce_esaj.scraper_edge_cli import ESAJScraperTJCEEdgeCLI


class ESAJScraperTJCEMovEdgeCLI(ESAJScraperTJCEEdgeCLI):
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
