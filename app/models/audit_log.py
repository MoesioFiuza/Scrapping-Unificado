from datetime import datetime

from app.extensions import db


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    username = db.Column(db.String(255), nullable=True, index=True)
    action = db.Column(db.String(128), nullable=False, index=True)
    details = db.Column(db.JSON, nullable=True)
    ip_address = db.Column(db.String(64), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    user = db.relationship('User', backref=db.backref('audit_logs', lazy='dynamic'))

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'username': self.username,
            'action': self.action,
            'details': self.details or {},
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat(),
        }
