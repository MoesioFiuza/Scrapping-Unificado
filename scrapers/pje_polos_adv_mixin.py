"""Mixin PJe: na página de detalhe, extrai só polo ativo, polo passivo e lista de advogados."""

from __future__ import annotations

import time
import traceback

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


class PjePolosAdvMixin:
    @staticmethod
    def _linha_e_advogado(parte: dict) -> bool:
        tipo = (parte.get("tipo") or "").upper()
        texto = (parte.get("nome_completo") or parte.get("nome") or "").lower()
        if parte.get("oab"):
            return True
        if "ADVOGADO" in tipo or "ADVOGADA" in tipo or "PROCURADOR" in tipo:
            return True
        if "advogado" in texto or "advogada" in texto or "procurador" in texto:
            return True
        return False

    def _montar_lista_advogados(self, polo_ativo: list | None, polo_passivo: list | None) -> list:
        out: list[dict] = []
        for polo_label, lista in (("ativo", polo_ativo or []), ("passivo", polo_passivo or [])):
            for p in lista:
                if self._linha_e_advogado(p):
                    row = dict(p)
                    row["polo_participacao"] = polo_label
                    out.append(row)
        return out

    def _extrair_dados_processo(self) -> dict:
        dados: dict = {}
        try:
            print("Aguardando página de detalhes (modo polos / advogados)...")
            try:
                WebDriverWait(self.driver, 15).until(
                    lambda driver: (
                        len(driver.find_elements(By.CLASS_NAME, "rich-stglpanel-body")) > 0
                        or len(driver.find_elements(By.CLASS_NAME, "propertyView")) > 0
                        or "DetalheProcesso" in driver.current_url
                    )
                )
            except TimeoutException:
                print("Timeout aguardando página de detalhes; tentando extrair polos mesmo assim.")
            time.sleep(1.5)
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(0.45)

            dados["polo_ativo"] = self._extrair_polo_ativo()
            dados["polo_passivo"] = self._extrair_polo_passivo()
            dados["advogados"] = self._montar_lista_advogados(
                dados.get("polo_ativo"), dados.get("polo_passivo")
            )
            print(
                f"Polos: ativo={len(dados.get('polo_ativo') or [])} "
                f"passivo={len(dados.get('polo_passivo') or [])} "
                f"advogados={len(dados.get('advogados') or [])}"
            )
        except Exception as e:
            print(f"Erro ao extrair polos/advogados: {e}")
            print(traceback.format_exc())
            dados["erro_extracao"] = str(e)
        return dados
