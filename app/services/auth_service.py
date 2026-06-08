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
            target_role = AuthService.get_user_role(target_username)
            if target_role == 'admin':
                return False
        return True

    @staticmethod
    def delete_user(username):
        user = AuthService._get_user(username)
        if not user:
            return False, 'Usuário não encontrado'

        db.session.delete(user)
        db.session.commit()
        return True, 'Usuário removido com sucesso'

    @staticmethod
    def update_user_role(username, new_role):
        user = AuthService._get_user(username)
        if not user:
            return False, 'Usuário não encontrado'

        user.role = new_role
        db.session.commit()
        return True, 'Role atualizado com sucesso'
