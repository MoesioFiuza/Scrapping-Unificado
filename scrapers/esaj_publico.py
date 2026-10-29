"""Comportamento comum da consulta pública eSAJ (sem login).

Usado pela raspagem normal e pelos CLIs, que herdam o scraper de cada tribunal.
"""
from __future__ import annotations

import re
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

FRASE_SEM_INFORMACOES = "não existem informações disponíveis para os parâmetros informados"


def partes_formulario_esaj(numero_processo: str) -> tuple[str, str] | None:
    """(13 primeiros dígitos, foro com 4). Aceita CNJ mascarado ou 20 dígitos juntos."""
    bruto = str(numero_processo or "").strip()
    if bruto.endswith(".0"):
        bruto = bruto[:-2]
    digitos = re.sub(r"\D", "", bruto)
    if len(digitos) < 20:
        return None
    digitos = digitos[:20]
    return digitos[:13], digitos[16:20]


def consulta_sem_informacoes(driver, timeout: float = 12) -> bool:
    """True assim que o eSAJ avisa que não há dados para o número."""
    limite = time.monotonic() + timeout
    while time.monotonic() < limite:
        try:
            html = (driver.page_source or "").lower()
        except Exception:
            return False
        if FRASE_SEM_INFORMACOES in html:
            return True
        if driver.find_elements(By.ID, "classeProcesso"):
            return False
        time.sleep(0.25)
    try:
        return FRASE_SEM_INFORMACOES in (driver.page_source or "").lower()
    except Exception:
        return False


def _qtd_movimentos(driver) -> int:
    return len(driver.find_elements(By.CSS_SELECTOR, "tr.containerMovimentacao"))


def _links_mais(driver) -> list:
    vistos = set()
    links = []
    candidatos = driver.find_elements(By.CSS_SELECTOR, "a#linkMovimentacoesPaginado, a#linkmovimentacoes")
    candidatos += driver.find_elements(By.CSS_SELECTOR, "span.textoLinkMovimentacoesPaginado")
    for el in candidatos:
        try:
            if not el.is_displayed():
                continue
            if el.tag_name.lower() == "span":
                el = el.find_element(By.XPATH, "./ancestor::a[1]")
            if "mais" not in (el.text or "").lower():
                continue
            chave = el.id
            if chave in vistos:
                continue
            vistos.add(chave)
            links.append(el)
        except Exception:
            continue
    return links


def expandir_movimentacoes(driver) -> None:
    """Clica em Exibir movimentações e em cada Mais visível até a lista parar de crescer."""
    if driver.find_elements(By.ID, "btnExibirMovimentacoes"):
        try:
            botao = WebDriverWait(driver, 4).until(
                EC.element_to_be_clickable((By.ID, "btnExibirMovimentacoes"))
            )
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", botao)
            botao.click()
            print("Clicou em Exibir movimentações")
            time.sleep(0.6)
        except Exception:
            pass

    for _ in range(80):
        links = _links_mais(driver)
        if not links:
            break
        cresceu = False
        for link in links:
            antes = _qtd_movimentos(driver)
            try:
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", link)
                link.click()
            except Exception:
                try:
                    driver.execute_script("arguments[0].click();", link)
                except Exception:
                    continue
            time.sleep(0.5)
            if _qtd_movimentos(driver) <= antes:
                time.sleep(0.8)
            if _qtd_movimentos(driver) > antes:
                cresceu = True
        if not cresceu:
            break
