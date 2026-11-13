from datetime import datetime

from app.extensions import db


class ErroRegistro(db.Model):
    """Falha de um processo no Valença Suite, visível só na análise de erros do super admin."""

    __tablename__ = "erro_registros"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    servico = db.Column(db.String(160), nullable=False)
    cnj = db.Column(db.String(80), nullable=False, default="")
    erro = db.Column(db.Text, nullable=False)
    maquina = db.Column(db.String(255), nullable=True)
    versao = db.Column(db.String(32), nullable=True)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    user = db.relationship("User", backref=db.backref("erros_processo", lazy="dynamic"))
