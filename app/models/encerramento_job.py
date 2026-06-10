from datetime import datetime

from app.extensions import db


class EncerramentoJob(db.Model):
    __tablename__ = "encerramento_jobs"

    id = db.Column(db.String(64), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    tribunal_key = db.Column(db.String(64), nullable=False)
    workers = db.Column(db.Integer, nullable=False, default=3)
    status = db.Column(db.String(32), nullable=False, default="queued", index=True)
    total_processos = db.Column(db.Integer, nullable=False, default=0)
    resultados_parciais_json = db.Column(db.JSON, nullable=False, default=dict)
    resultado_json = db.Column(db.JSON, nullable=True)
    aborted = db.Column(db.Boolean, nullable=False, default=False)
    error_message = db.Column(db.Text, nullable=True)
    started_at = db.Column(db.DateTime, nullable=True)
    finished_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("encerramento_jobs", lazy="dynamic"))

    def to_status_dict(self) -> dict:
        parciais = self.resultados_parciais_json or {}
        if isinstance(parciais, dict):
            parciais_list = list(parciais.values())
        else:
            parciais_list = list(parciais or [])

        payload: dict = {
            "status": self.status,
            "error": self.error_message,
            "tribunal_key": self.tribunal_key,
            "workers": self.workers,
            "total_processos": self.total_processos,
            "started_at": self.started_at.timestamp() if self.started_at else None,
            "resultados_parciais": parciais_list,
        }
        if self.status in ("completed", "aborted", "error", "interrupted") and self.resultado_json:
            payload["resultado"] = self.resultado_json
        return payload
