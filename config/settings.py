import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / 'data'
USERS_JSON_LEGACY = DATA_DIR / 'users.json'
EXTRACOES_JSON_LEGACY = DATA_DIR / 'extracoes.json'

_default_sqlite_path = (DATA_DIR / 'scraper.db').resolve()
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    f'sqlite:///{_default_sqlite_path.as_posix()}',
)

# Super admin (e-mail) — configurável por ambiente
SUPER_ADMIN_EMAIL = (
    os.getenv('SUPER_ADMIN_EMAIL', 'moesio.fiuza@valenca.adv.br').strip().lower()
)

# Primeiro utilizador quando a BD está vazia e não há users.json
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', '').strip().lower()
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', '')

def get_chromedriver_path():
    """Caminho explícito do ChromeDriver (.env). None → webdriver-manager nos scrapers."""
    env_path = os.getenv('CHROME_DRIVER_PATH')
    if env_path and os.path.exists(env_path):
        return env_path
    return None


def get_edgedriver_path():
    """Caminho do msedgedriver; None se não existir (CLI Edge usa EdgeChromiumDriverManager)."""
    env_path = os.getenv("EDGE_DRIVER_PATH")
    if env_path and os.path.exists(env_path):
        return env_path
    if os.name == "nt":
        # Pasta comum neste projeto; pode sobrescrever com EDGE_DRIVER_PATH no .env
        default_path = os.path.join(
            os.path.expanduser("~"),
            "Desktop",
            "ACESSO LOGADO",
            "msedgedriver.exe",
        )
        if os.path.exists(default_path):
            return default_path
    return None


CHROME_DRIVER_PATH = get_chromedriver_path()
EDGE_DRIVER_PATH = get_edgedriver_path()
EDGE_USER_DATA_DIR = os.getenv("EDGE_USER_DATA_DIR") or None
EDGE_PROFILE_DIRECTORY = os.getenv("EDGE_PROFILE_DIRECTORY", "Default")
CHROME_USER_DATA_DIR = os.getenv('CHROME_USER_DATA_DIR') or None
CHROME_PROFILE_DIRECTORY = os.getenv('CHROME_PROFILE_DIRECTORY', 'Default')

HEADLESS_MODE = os.getenv('HEADLESS_MODE', 'True').lower() == 'true'

# SOCKS/HTTP proxy só para scrapers CE (TJCE PJe + eSAJ CE), ex.: túnel SSH local
SCRAPER_PROXY_CE = (os.getenv('SCRAPER_PROXY_CE') or '').strip() or None

MAX_PROCESSOS_POR_SESSAO = int(os.getenv('MAX_PROCESSOS_POR_SESSAO', '1000'))
DELAY_ENTRE_PROCESSOS = float(os.getenv('DELAY_ENTRE_PROCESSOS', '0.5'))

# DataWeb microserviço (DataJud → Excel)
DATAWEB_BASE_URL = os.getenv('DATAWEB_BASE_URL', 'http://212.47.68.222/dataweb').rstrip('/')
DATAWEB_TIMEOUT_SECONDS = int(os.getenv('DATAWEB_TIMEOUT_SECONDS', '600'))
DATAWEB_MAX_CNJS = int(os.getenv('DATAWEB_MAX_CNJS_POR_REQUISICAO', '500'))
DATAWEB_MAX_PARALLEL_LOTES = int(os.getenv('DATAWEB_MAX_PARALLEL_LOTES', '2'))

# Deploy — subpath atrás de reverse proxy (ex.: http://212.47.68.222/scraper)
APPLICATION_ROOT = os.getenv('APPLICATION_ROOT', '').strip().rstrip('/')
if APPLICATION_ROOT and not APPLICATION_ROOT.startswith('/'):
    APPLICATION_ROOT = f'/{APPLICATION_ROOT}'

FLASK_ENV = os.getenv('FLASK_ENV', 'development').lower()
IS_PRODUCTION = FLASK_ENV == 'production'

# Gunicorn / bind interno (nginx faz proxy)
GUNICORN_BIND = os.getenv('GUNICORN_BIND', '127.0.0.1:8001')
GUNICORN_WORKERS = int(os.getenv('GUNICORN_WORKERS', '2'))
GUNICORN_TIMEOUT = int(os.getenv('GUNICORN_TIMEOUT', '620'))