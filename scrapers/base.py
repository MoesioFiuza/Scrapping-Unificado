from abc import ABC, abstractmethod
from selenium.webdriver.remote.webdriver import WebDriver
from typing import Dict, Any, Optional
import time

class BaseScraper(ABC):
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.driver: Optional[WebDriver] = None
    
    def is_driver_valid(self) -> bool:
        """Verifica se o driver está válido e funcional"""
        if not self.driver:
            return False
        
        try:
            # Tentar acessar uma propriedade simples para verificar se a sessão está válida
            _ = self.driver.current_url
            return True
        except Exception:
            # Se houver exceção, o driver está inválido
            return False
    
    def ensure_driver(self):
        """Garante que o driver existe e está válido, recriando se necessário"""
        if not self.is_driver_valid():
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
                self.driver = None
            self.setup_driver()
    
    @abstractmethod
    def setup_driver(self) -> WebDriver:
        pass
    
    @abstractmethod
    def raspar_processo(self, numero_processo: str) -> Dict[str, Any]:
        pass
    
    def close(self):
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None