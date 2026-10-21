from datetime import datetime

from app.extensions import db


class DocumentoVersao(db.Model):
    """Versão publicada dos PDFs de uma equipe (lida pela Valença Suite)."""

    __tablename__ = 'documento_versoes'
    __table_args__ = (db.UniqueConstraint('equipe', 'versao', name='uq_documento_versao'),)

    id = db.Column(db.Integer, primary_key=True)
    equipe = db.Column(db.String(32), nullable=False, index=True)
    versao = db.Column(db.Integer, nullable=False)
    arquivos = db.Column(db.JSON, nullable=False, default=list)
    publicado_por = db.Column(db.String(255), nullable=True)
    publicado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            'equipe': self.equipe,
            'versao': self.versao,
            'arquivos': self.arquivos or [],
            'publicado_por': self.publicado_por,
            'publicado_em': self.publicado_em.isoformat() + 'Z',
        }


class DocumentoRascunho(db.Model):
    """Alteração pendente de um documento (arquivo e/ou tipo) antes de publicar."""

    __tablename__ = 'documento_rascunhos'
    __table_args__ = (db.UniqueConstraint('equipe', 'slot', name='uq_documento_rascunho'),)

    id = db.Column(db.Integer, primary_key=True)
    equipe = db.Column(db.String(32), nullable=False, index=True)
    slot = db.Column(db.String(32), nullable=False)
    ordem = db.Column(db.Integer, nullable=False)
    nome_arquivo = db.Column(db.String(255), nullable=False)
    titulo = db.Column(db.String(255), nullable=False)
    tipo = db.Column(db.String(64), nullable=True)
    sha256 = db.Column(db.String(64), nullable=True)
    tamanho = db.Column(db.Integer, nullable=True)
    tamanho_original = db.Column(db.Integer, nullable=True)
    paginas = db.Column(db.Integer, nullable=True)
    compressao = db.Column(db.String(32), nullable=True)
    enviado_por = db.Column(db.String(255), nullable=True)
    enviado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
