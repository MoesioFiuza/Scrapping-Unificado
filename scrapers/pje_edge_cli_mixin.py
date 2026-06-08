"""Mixin: Microsoft Edge para CLIs de consulta PJe (headless=new, msedgedriver)."""

from __future__ import annotations

import os
import traceback

from selenium import webdriver
from selenium.common.exceptions import SessionNotCreatedException
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService

from config.settings import (
    EDGE_DRIVER_PATH,
    EDGE_PROFILE_DIRECTORY,
    EDGE_USER_DATA_DIR,
    HEADLESS_MODE,
)

try:
    from webdriver_manager.microsoft import EdgeChromiumDriverManager
except ImportError:  # pragma: no cover
    EdgeChromiumDriverManager = None  # type: ignore[misc, assignment]


class PjeEdgeCliMixin:
    def setup_driver(self):
        try:
            edge_options = EdgeOptions()
            use_headless = self.headless or HEADLESS_MODE
            if use_headless:
                edge_options.add_argument("--headless=new")
                edge_options.add_argument("--no-sandbox")
                edge_options.add_argument("--disable-dev-shm-usage")
                edge_options.add_argument("--disable-gpu")
                edge_options.add_argument("--window-size=1920,1080")
                edge_options.add_argument("--start-maximized")
                edge_options.add_argument("--disable-extensions")
                edge_options.add_argument("--disable-software-rasterizer")
                edge_options.add_argument("--disable-background-timer-throttling")
                edge_options.add_argument("--disable-backgrounding-occluded-windows")
                edge_options.add_argument("--disable-renderer-backgrounding")
                edge_options.add_argument("--disable-features=TranslateUI")
                edge_options.add_argument("--disable-ipc-flooding-protection")
                edge_options.add_argument(
                    "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
                )
                print("Modo headless ativado (CLI Edge: --headless=new)")
            else:
                if EDGE_USER_DATA_DIR:
                    edge_options.add_argument(f"--user-data-dir={EDGE_USER_DATA_DIR}")
                    edge_options.add_argument(f"--profile-directory={EDGE_PROFILE_DIRECTORY}")
                edge_options.add_experimental_option("detach", True)

            edge_options.add_argument("--disable-blink-features=AutomationControlled")
            edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            edge_options.add_experimental_option("useAutomationExtension", False)

            def _start_with_service(svc: EdgeService) -> None:
                self.driver = webdriver.Edge(service=svc, options=edge_options)

            if EDGE_DRIVER_PATH and os.path.isfile(EDGE_DRIVER_PATH):
                try:
                    _start_with_service(EdgeService(EDGE_DRIVER_PATH))
                except SessionNotCreatedException:
                    print(
                        "msedgedriver em EDGE_DRIVER_PATH não abriu o Edge (versão costuma ser a causa). "
                        "Tentando EdgeChromiumDriverManager..."
                    )
                    if EdgeChromiumDriverManager is None:
                        raise
                    _start_with_service(EdgeService(EdgeChromiumDriverManager().install()))
            else:
                if EdgeChromiumDriverManager is not None:
                    try:
                        _start_with_service(EdgeService(EdgeChromiumDriverManager().install()))
                    except Exception as e:
                        print(f"Aviso: Erro ao usar EdgeChromiumDriverManager: {e}. Tentando Edge sem Service...")
                        self.driver = webdriver.Edge(options=edge_options)
                else:
                    self.driver = webdriver.Edge(options=edge_options)

            if not use_headless:
                self.driver.maximize_window()

            print("Driver do Microsoft Edge configurado com sucesso")
            return self.driver
        except SessionNotCreatedException as e:
            print(f"Erro ao configurar driver Edge: {str(e)}")
            print(traceback.format_exc())
            print(
                "Dica: confira se o Microsoft Edge está atualizado; ajuste EDGE_DRIVER_PATH no .env "
                "para um msedgedriver da mesma versão major, ou teste com --sem-headless."
            )
            raise
        except Exception as e:
            print(f"Erro ao configurar driver Edge: {str(e)}")
            print(traceback.format_exc())
            raise
