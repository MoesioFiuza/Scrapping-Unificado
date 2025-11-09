import os
from dotenv import load_dotenv

load_dotenv()

def get_chromedriver_path():
    """Obtém o caminho do ChromeDriver, retornando None se não encontrar um válido"""
    # 1. Tentar usar o caminho do .env se existir
    env_path = os.getenv('CHROME_DRIVER_PATH')
    if env_path and os.path.exists(env_path):
        return env_path
    
    # 2. Tentar caminho padrão do Windows (só se existir)
    if os.name == 'nt':  # Windows
        default_path = r'C:\Users\Moésio\Desktop\Nova Scrapper\chromedriver.exe'
        if os.path.exists(default_path):
            return default_path
    
    # 3. Retornar None - os scrapers usarão webdriver-manager como fallback
    return None

CHROME_DRIVER_PATH = get_chromedriver_path()
CHROME_USER_DATA_DIR = os.getenv('CHROME_USER_DATA_DIR') or None
CHROME_PROFILE_DIRECTORY = os.getenv('CHROME_PROFILE_DIRECTORY', 'Default')

HEADLESS_MODE = os.getenv('HEADLESS_MODE', 'True').lower() == 'true'

MAX_PROCESSOS_POR_SESSAO = int(os.getenv('MAX_PROCESSOS_POR_SESSAO', '1000'))
DELAY_ENTRE_PROCESSOS = float(os.getenv('DELAY_ENTRE_PROCESSOS', '0.5'))