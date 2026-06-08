from datetime import datetime

from app.extensions import db


class CliJob(db.Model):
    __tablename__ = 'cli_jobs'

    id = db.Column(db.String(64), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    tribunal_key = db.Column(db.String(64), nullable=False)
    browser = db.Column(db.String(16), nullable=False, default='chrome')
    job_mode = db.Column(db.String(32), nullable=False)
    workers = db.Column(db.Integer, nullable=False, default=3)
    status = db.Column(db.String(32), nullable=False, default='queued', index=True)
    total_processos = db.Column(db.Integer, nullable=False, default=0)
    resultados_parciais_json = db.Column(db.JSON, nullable=False, default=dict)
    extracao_ids_json = db.Column(db.JSON, nullable=False, default=list)
    filenames_json = db.Column(db.JSON, nullable=False, default=list)
    aborted = db.Column(db.Boolean, nullable=False, default=False)
    error_message = db.Column(db.Text, nullable=True)
    started_at = db.Column(db.DateTime, nullable=True)
    finished_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('cli_jobs', lazy='dynamic'))

    def to_status_dict(self) -> dict:
        parciais = self.resultados_parciais_json or {}
        if isinstance(parciais, dict):
            parciais_list = list(parciais.values())
        else:
            parciais_list = list(parciais or [])

        started_ts = self.started_at.timestamp() if self.started_at else None
        return {
            'status': self.status,
            'error': self.error_message,
            'extracao_ids': self.extracao_ids_json or [],
            'filenames': self.filenames_json or [],
            'total_processos': self.total_processos,
            'started_at': started_ts,
            'resultados_parciais': parciais_list,
        }
