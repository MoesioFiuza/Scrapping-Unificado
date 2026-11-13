from datetime import datetime

from app.extensions import db


class UsoRegistro(db.Model):
    """Uso do Valença Suite e logins, visível só no acompanhamento do super admin."""

    __tablename__ = "uso_registros"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    origem = db.Column(db.String(32), nullable=False, default="valenca_suite")
    servico = db.Column(db.String(160), nullable=False)
    maquina = db.Column(db.String(255), nullable=True)
    total = db.Column(db.Integer, nullable=False, default=0)
    sucesso = db.Column(db.Integer, nullable=False, default=0)
    erro = db.Column(db.Integer, nullable=False, default=0)
    iniciado_em = db.Column(db.DateTime, nullable=True)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    user = db.relationship("User", backref=db.backref("usos", lazy="dynamic"))
