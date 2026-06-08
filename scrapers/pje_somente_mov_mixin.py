"""Mixin PJe: na página de detalhe, extrai só movimentações (fluxo raspar_processo da base)."""

from __future__ import annotations

import time
import traceback

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


class PjeSomenteMovMixin:
    def _extrair_dados_processo(self) -> dict:
        dados: dict = {}
        try:
            print("Aguardando página de detalhes (modo só movimentações)...")
            try:
                WebDriverWait(self.driver, 15).until(
                    lambda driver: (
                        len(driver.find_elements(By.CLASS_NAME, "rich-stglpanel-body")) > 0
                        or len(driver.find_elements(By.CLASS_NAME, "propertyView")) > 0
                        or "DetalheProcesso" in driver.current_url
                    )
                )
            except TimeoutException:
                print("Timeout aguardando página de detalhes; tentando extrair movimentações mesmo assim.")
            time.sleep(2)
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(0.5)
            dados["movimentacoes"] = self._extrair_movimentacoes()
            print(f"Movimentações (modo leve): {len(dados.get('movimentacoes', []))} itens.")
        except Exception as e:
            print(f"Erro ao extrair movimentações: {e}")
            print(traceback.format_exc())
            dados["erro_extracao"] = str(e)
        return dados
