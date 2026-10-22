from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

from app.extensions import db
from app.models import User
from config.settings import SUPER_ADMIN_EMAIL


class AuthService:
    @staticmethod
    def _get_user(username: str) -> User | None:
        if not username:
            return None
        return User.query.filter_by(username=username.strip().lower()).first()

    @staticmethod
    def verify_user(username, password):
        user = AuthService._get_user(username)
        if not user or not user.is_active:
            return False
        if check_password_hash(user.password_hash, password):
            user.last_login_at = datetime.utcnow()
            db.session.commit()
            return user.role
        return False

    @staticmethod
    def get_user_role(username):
        user = AuthService._get_user(username)
        if not user or not user.is_active:
            return None
        return user.role

    @staticmethod
    def add_user(username, password, role='user'):
        username = username.strip().lower()
        if AuthService._get_user(username):
            return False, 'Usuário já existe'

        db.session.add(
            User(
                username=username,
                password_hash=generate_password_hash(password),
                role=role,
            )
        )
        db.session.commit()
        return True, 'Usuário adicionado com sucesso'

    @staticmethod
    def get_all_users(current_username=None):
        current_username = (current_username or '').strip().lower()
        is_super_admin = AuthService.is_super_admin(current_username)
        users_list = []

        for user in User.query.order_by(User.username).all():
            if (
                not is_super_admin
                and user.role == 'admin'
                and user.username != current_username
            ):
                continue
            users_list.append(user.to_public_dict())
        return users_list

    @staticmethod
    def is_super_admin(username):
        return (username or '').strip().lower() == SUPER_ADMIN_EMAIL

    @staticmethod
    def can_manage_admin(current_username, target_username):
        if not AuthService.is_super_admin(current_username):
            target = AuthService._get_user(target_username)
            if target and target.role == 'admin':
                return False
        return True

    @staticmethod
    def deactivate_user(username):
        user = AuthService._get_user(username)
        if not user:
            return False, 'Usuário não encontrado'
        if not user.is_active:
            return False, 'Usuário já está desactivado'
        user.is_active = False
        db.session.commit()
        return True, 'Usuário desactivado com sucesso'

    @staticmethod
    def activate_user(username):
        user = AuthService._get_user(username)
        if not user:
            return False, 'Usuário não encontrado'
        if user.is_active:
            return False, 'Usuário já está activo'
        user.is_active = True
        db.session.commit()
        return True, 'Usuário reactivado com sucesso'

    @staticmethod
    def reset_password(username, new_password):
        user = AuthService._get_user(username)
        if not user:
            return False, 'Usuário não encontrado'
        if not new_password or len(new_password) < 8:
            return False, 'A nova senha deve ter pelo menos 8 caracteres'
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        return True, 'Senha redefinida com sucesso'

    @staticmethod
    def change_password(username, current_password, new_password):
        user = AuthService._get_user(username)
        if not user or not user.is_active:
            return False, 'Usuário não encontrado'
        if not check_password_hash(user.password_hash, current_password):
            return False, 'Senha actual incorrecta'
        if not new_password or len(new_password) < 8:
            return False, 'A nova senha deve ter pelo menos 8 caracteres'
        if current_password == new_password:
            return False, 'A nova senha deve ser diferente da actual'
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        return True, 'Senha alterada com sucesso'

    @staticmethod
    def update_user_role(username, new_role):
        user = AuthService._get_user(username)
        if not user:
            return False, 'Usuário não encontrado'

        user.role = new_role
        db.session.commit()
        return True, 'Role atualizado com sucesso'
