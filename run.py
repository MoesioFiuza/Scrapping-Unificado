import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import app
from config.settings import IS_PRODUCTION

if __name__ == '__main__':
    # use_reloader=False evita reinício do Flask quando workers Selenium abrem processos
    use_reloader = os.getenv('FLASK_USE_RELOADER', 'false').lower() == 'true'
    app.run(
        debug=not IS_PRODUCTION,
        use_reloader=use_reloader,
        host=os.getenv('FLASK_HOST', '0.0.0.0'),
        port=int(os.getenv('FLASK_PORT', '5000')),
    )
