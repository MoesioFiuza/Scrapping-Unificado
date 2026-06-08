from datetime import datetime

from app.extensions import db


class Extracao(db.Model):
    __tablename__ = 'extracoes'

    id = db.Column(db.String(64), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    filename = db.Column(db.String(512), nullable=False)
    filepath = db.Column(db.String(1024), nullable=False)
    tipo = db.Column(db.String(64), nullable=False)
    total_processos = db.Column(db.Integer, nullable=False, default=0)
    data_criacao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    user = db.relationship(
        'User',
        backref=db.backref('extracoes', lazy='dynamic', cascade='all, delete-orphan'),
    )

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'username': self.user.username if self.user else '',
            'filename': self.filename,
            'tipo': self.tipo,
            'data_criacao': self.data_criacao.isoformat(),
            'total_processos': self.total_processos,
            'filepath': self.filepath,
        }
