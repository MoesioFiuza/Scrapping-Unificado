from datetime import datetime

from app.extensions import db


class LogExecucao(db.Model):
    """Log técnico de uma execução do Valença Suite, visível só ao super admin."""

    __tablename__ = "log_execucoes"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    servico = db.Column(db.String(160), nullable=False)
    maquina = db.Column(db.String(255), nullable=True)
    versao = db.Column(db.String(32), nullable=True)
    texto = db.Column(db.Text, nullable=False)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    user = db.relationship("User", backref=db.backref("logs_execucao", lazy="dynamic"))
