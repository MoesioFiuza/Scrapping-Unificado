from abc import ABC, abstractmethod
from selenium.webdriver.remote.webdriver import WebDriver
from typing import Dict, Any, Optional
import time

class BaseScraper(ABC):
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.driver: Optional[WebDriver] = None
    
    @abstractmethod
    def setup_driver(self) -> WebDriver:
        pass
    
    @abstractmethod
    def raspar_processo(self, numero_processo: str) -> Dict[str, Any]:
        pass
    
    def close(self):
        if self.driver:
            self.driver.quit()
            self.driver = None