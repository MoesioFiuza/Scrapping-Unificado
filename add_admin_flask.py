
import sys
import os
from pathlib import Path

# Adicionar o diretório raiz ao path
workspace_path = Path(__file__).parent.absolute()
sys.path.insert(0, str(workspace_path))

# Importar e criar app context
from app.main import app
from app.services.auth_service import AuthService

with app.app_context():
    username = 'amanda.xelian@valenca.adv.br'
    password = 'Fenobarbital'
    role = 'admin'
    
    success, message = AuthService.add_user(username, password, role)
    if success:
        print(f'✓ {message}')
        print(f'Usuário: {username}')
        print(f'Role: {role}')
    else:
        print(f'✗ Erro: {message}')
        sys.exit(1)
