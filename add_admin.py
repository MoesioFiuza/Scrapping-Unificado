#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script temporário para adicionar usuário admin"""
import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.auth_service import AuthService

# Adicionar usuário admin
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
