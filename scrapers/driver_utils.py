"""Utilitários partilhados para criar drivers Selenium com fallback automático."""

from __future__ import annotations

import logging

from selenium import webdriver
from selenium.common.exceptions import SessionNotCreatedException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service

logger = logging.getLogger(__name__)


def create_chrome_driver(
    options: ChromeOptions,
    *,
    driver_path: str | None = None,
) -> webdriver.Chrome:
    """
    Cria Chrome WebDriver. Se ``driver_path`` falhar (ex.: versão incompatível),
    faz fallback para webdriver-manager e, por último, Selenium sem Service.
    """
    errors: list[str] = []

    if driver_path:
        try:
            return webdriver.Chrome(service=Service(driver_path), options=options)
        except SessionNotCreatedException as exc:
            msg = f"ChromeDriver em {driver_path!r} incompatível: {exc}"
            logger.warning("%s — a usar webdriver-manager.", msg)
            errors.append(msg)
        except Exception as exc:
            msg = f"Falha com CHROME_DRIVER_PATH={driver_path!r}: {exc}"
            logger.warning("%s — a usar webdriver-manager.", msg)
            errors.append(msg)

    try:
        from webdriver_manager.chrome import ChromeDriverManager

        managed = ChromeDriverManager().install()
        return webdriver.Chrome(service=Service(managed), options=options)
    except Exception as exc:
        errors.append(f"webdriver-manager: {exc}")
        try:
            return webdriver.Chrome(options=options)
        except Exception as exc2:
            raise RuntimeError("; ".join(errors + [str(exc2)])) from exc2
