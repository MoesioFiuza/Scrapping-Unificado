import json
import os
from werkzeug.security import generate_password_hash, check_password_hash
from pathlib import Path

class AuthService:
    USERS_FILE = Path('data/users.json')
    SUPER_ADMIN = 'moesio.fiuza@valenca.adv.br'
    
    @staticmethod
    def load_users():
        if not AuthService.USERS_FILE.exists():
            AuthService.USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
            default_users = {
                "users": [
                    {
                        "username": "moesio.fiuza@valenca.adv.br",
                        "password_hash": generate_password_hash("Moabejose@0"),
                        "role": "admin"
                    }
                ]
            }
            with open(AuthService.USERS_FILE, 'w', encoding='utf-8') as f:
                json.dump(default_users, f, indent=2)
            return default_users
        
        with open(AuthService.USERS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            needs_save = False
            for user in data.get('users', []):
                if 'role' not in user:
                    user['role'] = 'user'
                    needs_save = True
            
            if needs_save:
                with open(AuthService.USERS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
            
            return data
    
    @staticmethod
    def verify_user(username, password):
        users_data = AuthService.load_users()
        for user in users_data.get('users', []):
            if user['username'] == username:
                if check_password_hash(user['password_hash'], password):
                    return user.get('role', 'user')
        return False
    
    @staticmethod
    def get_user_role(username):
        users_data = AuthService.load_users()
        for user in users_data.get('users', []):
            if user['username'] == username:
                return user.get('role', 'user')
        return None
    
    @staticmethod
    def add_user(username, password, role='user'):
        users_data = AuthService.load_users()
        for user in users_data.get('users', []):
            if user['username'] == username:
                return False, 'Usuário já existe'
        
        password_hash = generate_password_hash(password)
        users_data['users'].append({
            'username': username,
            'password_hash': password_hash,
            'role': role
        })
        with open(AuthService.USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(users_data, f, indent=2)
        return True, 'Usuário adicionado com sucesso'
    
    @staticmethod
    def get_all_users(current_username=None):
        users_data = AuthService.load_users()
        users_list = []
        is_super_admin = current_username == AuthService.SUPER_ADMIN
        
        for user in users_data.get('users', []):
            if not is_super_admin and user.get('role') == 'admin' and user['username'] != current_username:
                continue
            
            users_list.append({
                'username': user['username'],
                'role': user.get('role', 'user')
            })
        return users_list
    
    @staticmethod
    def is_super_admin(username):
        return username == AuthService.SUPER_ADMIN
    
    @staticmethod
    def can_manage_admin(current_username, target_username):
        if not AuthService.is_super_admin(current_username):
            target_role = AuthService.get_user_role(target_username)
            if target_role == 'admin':
                return False
        return True
    
    @staticmethod
    def delete_user(username):
        users_data = AuthService.load_users()
        original_count = len(users_data.get('users', []))
        users_data['users'] = [u for u in users_data.get('users', []) if u['username'] != username]
        
        if len(users_data['users']) == original_count:
            return False, 'Usuário não encontrado'
        
        with open(AuthService.USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(users_data, f, indent=2)
        return True, 'Usuário removido com sucesso'
    
    @staticmethod
    def update_user_role(username, new_role):
        users_data = AuthService.load_users()
        for user in users_data.get('users', []):
            if user['username'] == username:
                user['role'] = new_role
                with open(AuthService.USERS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(users_data, f, indent=2)
                return True, 'Role atualizado com sucesso'
        return False, 'Usuário não encontrado'