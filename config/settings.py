import os
from dotenv import load_dotenv

load_dotenv()

CHROME_DRIVER_PATH = os.getenv('CHROME_DRIVER_PATH', r'C:\Users\Moésio\Desktop\Nova Scrapper\chromedriver.exe')
CHROME_USER_DATA_DIR = os.getenv('CHROME_USER_DATA_DIR') or None
CHROME_PROFILE_DIRECTORY = os.getenv('CHROME_PROFILE_DIRECTORY', 'Default')

HEADLESS_MODE = os.getenv('HEADLESS_MODE', 'False').lower() == 'true'

MAX_PROCESSOS_POR_SESSAO = int(os.getenv('MAX_PROCESSOS_POR_SESSAO', '1000'))
DELAY_ENTRE_PROCESSOS = float(os.getenv('DELAY_ENTRE_PROCESSOS', '0.5'))