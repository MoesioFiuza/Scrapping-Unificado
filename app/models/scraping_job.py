from datetime import datetime

from app.extensions import db


class ScrapingJob(db.Model):
    __tablename__ = 'scraping_jobs'

    id = db.Column(db.String(64), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    status = db.Column(db.String(32), nullable=False, default='starting', index=True)
    total_processos = db.Column(db.Integer, nullable=False, default=0)
    processos_json = db.Column(db.JSON, nullable=False, default=list)
    resultados_parciais_json = db.Column(db.JSON, nullable=False, default=dict)
    resultados_json = db.Column(db.JSON, nullable=True)
    aborted = db.Column(db.Boolean, nullable=False, default=False)
    error_message = db.Column(db.Text, nullable=True)
    started_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    finished_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship('User', backref=db.backref('scraping_jobs', lazy='dynamic'))

    def to_status_dict(self) -> dict:
        parciais = self.resultados_parciais_json or {}
        if isinstance(parciais, dict):
            parciais_list = list(parciais.values())
        else:
            parciais_list = list(parciais or [])

        payload = {
            'status': self.status,
            'total_processos': self.total_processos,
            'resultados_parciais': parciais_list,
        }
        if self.status == 'completed' and self.resultados_json:
            payload['resultados'] = self.resultados_json
        elif self.status in ('error', 'interrupted', 'aborted'):
            payload['error'] = self.error_message or 'Erro desconhecido'
        return payload
