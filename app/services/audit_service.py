from __future__ import annotations

from typing import Any

from flask import has_request_context, request

from app.extensions import db
from app.models import AuditLog, User


class AuditService:
    @staticmethod
    def _resolve_user(username: str | None) -> tuple[int | None, str | None]:
        if not username:
            return None, None
        user = User.query.filter_by(username=username.strip().lower()).first()
        return (user.id if user else None, username.strip().lower())

    @staticmethod
    def log(
        action: str,
        *,
        username: str | None = None,
        user_id: int | None = None,
        details: dict[str, Any] | None = None,
        ip_address: str | None = None,
    ) -> None:
        if user_id is None and username:
            user_id, username = AuditService._resolve_user(username)
        elif username is None and user_id:
            user = db.session.get(User, user_id)
            username = user.username if user else None

        if ip_address is None and has_request_context():
            ip_address = request.remote_addr

        db.session.add(
            AuditLog(
                user_id=user_id,
                username=username,
                action=action,
                details=details or {},
                ip_address=ip_address,
            )
        )
        db.session.commit()

    @staticmethod
    def list_logs(*, limit: int = 50, offset: int = 0) -> tuple[list[dict], int]:
        limit = max(1, min(limit, 200))
        offset = max(0, offset)
        query = AuditLog.query.order_by(AuditLog.created_at.desc())
        total = query.count()
        rows = query.offset(offset).limit(limit).all()
        return [r.to_dict() for r in rows], total
