from datetime import datetime

from app.extensions import db


class DataWebJob(db.Model):
    __tablename__ = 'dataweb_jobs'

    id = db.Column(db.String(64), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    cnjs_json = db.Column(db.JSON, nullable=False, default=list)
    status = db.Column(db.String(32), nullable=False, default='queued', index=True)
    total_cnjs = db.Column(db.Integer, nullable=False, default=0)
    lote_atual = db.Column(db.Integer, nullable=False, default=0)
    total_lotes = db.Column(db.Integer, nullable=False, default=0)
    extracao_id = db.Column(db.String(64), nullable=True)
    filename = db.Column(db.String(512), nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    started_at = db.Column(db.DateTime, nullable=True)
    finished_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('dataweb_jobs', lazy='dynamic'))

    def to_status_dict(self) -> dict:
        payload: dict = {
            'status': self.status,
            'error': self.error_message,
            'total_cnjs': self.total_cnjs,
            'lote_atual': self.lote_atual,
            'total_lotes': self.total_lotes,
            'started_at': self.started_at.timestamp() if self.started_at else None,
        }
        if self.status == 'completed' and self.extracao_id and self.filename:
            payload['extracao_id'] = self.extracao_id
            payload['filename'] = self.filename
        return payload
