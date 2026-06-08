"""Mixin: Chrome para CLIs de consulta (headless=new, retry de driver)."""

from __future__ import annotations

import os
import traceback

from selenium import webdriver
from selenium.common.exceptions import SessionNotCreatedException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from config.settings import (
    CHROME_DRIVER_PATH,
    CHROME_PROFILE_DIRECTORY,
    CHROME_USER_DATA_DIR,
    HEADLESS_MODE,
)


class PjeChromeCliMixin:
    def setup_driver(self):
        try:
            chrome_options = Options()
            use_headless = self.headless or HEADLESS_MODE
            if use_headless:
                chrome_options.add_argument("--headless=new")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_argument("--window-size=1920,1080")
                chrome_options.add_argument("--start-maximized")
                chrome_options.add_argument("--disable-extensions")
                chrome_options.add_argument("--disable-software-rasterizer")
                chrome_options.add_argument("--disable-background-timer-throttling")
                chrome_options.add_argument("--disable-backgrounding-occluded-windows")
                chrome_options.add_argument("--disable-renderer-backgrounding")
                chrome_options.add_argument("--disable-features=TranslateUI")
                chrome_options.add_argument("--disable-ipc-flooding-protection")
                chrome_options.add_argument(
                    "--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
                )
                print("Modo headless ativado (CLI: --headless=new)")
            else:
                if CHROME_USER_DATA_DIR:
                    chrome_options.add_argument(f"--user-data-dir={CHROME_USER_DATA_DIR}")
                    chrome_options.add_argument(f"--profile-directory={CHROME_PROFILE_DIRECTORY}")
                chrome_options.add_experimental_option("detach", True)

            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option("useAutomationExtension", False)

            def _start_with_service(svc: Service) -> None:
                self.driver = webdriver.Chrome(service=svc, options=chrome_options)

            if CHROME_DRIVER_PATH and os.path.isfile(CHROME_DRIVER_PATH):
                try:
                    _start_with_service(Service(CHROME_DRIVER_PATH))
                except SessionNotCreatedException:
                    print(
                        "ChromeDriver em CHROME_DRIVER_PATH não abriu o Chrome (versão costuma ser a causa). "
                        "Tentando ChromeDriverManager alinhado ao Chrome instalado..."
                    )
                    _start_with_service(Service(ChromeDriverManager().install()))
            else:
                try:
                    _start_with_service(Service(ChromeDriverManager().install()))
                except Exception as e:
                    print(f"Aviso: Erro ao usar webdriver-manager: {e}. Tentando sem Service...")
                    self.driver = webdriver.Chrome(options=chrome_options)

            if not use_headless:
                self.driver.maximize_window()

            print("Driver do Chrome configurado com sucesso")
            return self.driver
        except SessionNotCreatedException as e:
            print(f"Erro ao configurar driver: {str(e)}")
            print(traceback.format_exc())
            print(
                "Dica: confira se o Google Chrome está atualizado; se usa CHROME_DRIVER_PATH no .env, "
                "remova ou aponte para um chromedriver da mesma versão major do Chrome, ou teste com --sem-headless."
            )
            raise
        except Exception as e:
            print(f"Erro ao configurar driver: {str(e)}")
            print(traceback.format_exc())
            raise
