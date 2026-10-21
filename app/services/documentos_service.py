# -*- coding: utf-8 -*-
"""PDFs de habilitação por equipe, publicados para a Valença Suite.

Cada equipe tem documentos com nome de arquivo fixo (o robô do aplicativo procura
por esses nomes). O admin substitui o arquivo de cada documento; o servidor
comprime, renomeia e só entrega ao aplicativo depois de "publicar".
"""
from __future__ import annotations

import hashlib
import logging
import os
import re
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

from app.extensions import db
from app.models import DocumentoRascunho, DocumentoVersao

logger = logging.getLogger(__name__)

TIPOS_PJE = ["Procuração", "Documento de Identificação"]


def _slot(ordem, nome_arquivo, titulo, tipo):
    return {'slot': str(ordem), 'ordem': ordem, 'nome_arquivo': nome_arquivo, 'titulo': titulo, 'tipo': tipo}


EQUIPES: dict[str, dict] = {
    'cagece': {
        'nome': 'CAGECE — PJe TJCE',
        'sistema': 'pje',
        'tipo_editavel': True,
        'pode_adicionar': False,
        'slots': [
            _slot(1, '1 - HABILITAÇÃO - CAGECE.pdf', 'Habilitação CAGECE', 'Documento de Identificação'),
            _slot(2, '2 - procuracao.pdf', 'Procuração', 'Procuração'),
            _slot(3, '3 - substabelecimento - valenca.pdf', 'Substabelecimento Valença', 'Documento de Identificação'),
            _slot(4, '4 - Ata_CAD_671_25_02_2025_DIRETOR_JUCEC.pdf', 'Ata — Diretor (JUCEC)', 'Documento de Identificação'),
            _slot(
                5,
                '5 - Ata_CAD_652_20_06_2024_JUCEC_DIRETORIA - Copia.pdf',
                'Ata — Diretoria (JUCEC)',
                'Documento de Identificação',
            ),
            _slot(6, '6 - estatuto social - cagece.pdf', 'Estatuto social', 'Documento de Identificação'),
        ],
    },
    'enel_rj': {
        'nome': 'Enel RJ (Ampla) — PJe TJRJ',
        'sistema': 'pje',
        'tipo_editavel': True,
        'pode_adicionar': False,
        'slots': [_slot(1, 'DOCUMENTOS ENEL.pdf', 'Procuração e documentos Ampla', 'Procuração')],
    },
    'enel_sp': {
        'nome': 'Enel SP — EPROC e eSAJ',
        'sistema': 'eproc',
        'tipo_editavel': False,
        'pode_adicionar': False,
        'slots': [
            _slot(1, '1 - PET. - HABILITAÇÃO.pdf', 'Petição de habilitação', 'Petição'),
            _slot(2, '2 - procuração.pdf', 'Procuração', 'Procuração'),
            _slot(3, '3 - Atos Constitutivos ENEL SP.pdf', 'Atos constitutivos', 'Documentação'),
        ],
    },
    'ndi': {
        'nome': 'NDI (Notre Dame) — EPROC SP',
        'sistema': 'eproc',
        'tipo_editavel': False,
        'pode_adicionar': True,
        'max_documentos': 20,
        'slots': [
            _slot(1, '1. Procuração Hapvida - NotreDame - Atual.pdf', 'Procuração Hapvida/NotreDame', 'Procuração'),
            _slot(
                2,
                '2. Substabelecimento Geral - Jurídico Interno - 29.05.2024_relatório de validação.pdf',
                'Substabelecimento — Jurídico interno',
                'Documentação',
            ),
            _slot(
                3,
                '3. Substabelecimento Geral - Escritório Valença - Assinado-mesclado.pdf',
                'Substabelecimento — Escritório Valença',
                'Documentação',
            ),
            _slot(4, '4. 2023 08 16 NDIS - AGE - Renún_José Carlos.pdf', 'AGE 16/08/2023', 'Documentação'),
            _slot(
                5,
                '5. 2023 03 14 NDIS - AGE - Renun_Joel_Marcelo Moreira_Lino_ eleiçoes.pdf',
                'AGE 14/03/2023',
                'Documentação',
            ),
            _slot(
                6,
                '6. 2023 02 07 NDIS - AGE - Renun_Irlau_Joao Alceu _ eleicaoo diretoria.pdf',
                'AGE 07/02/2023',
                'Documentação',
            ),
            _slot(7, '7. 2023 06 13 NDIS - AGE - Destituicao_Teresa Frei.pdf', 'AGE 13/06/2023', 'Documentação'),
            _slot(8, '8. 2024 03 28 NDIS - AGE - incorporacao BCBF _ cons.pdf', 'AGE 28/03/2024', 'Documentação'),
        ],
    },
}

_SHA = re.compile(r'^[0-9a-f]{64}$')
_NOME_INVALIDO = re.compile(r'[<>:"/\\|?*\x00-\x1f]+')


class DocumentoErro(Exception):
    """Erro de validação com mensagem para o usuário."""


def _max_bytes() -> int:
    try:
        return int(float(os.getenv('DOCUMENTOS_MAX_MB', '10')) * 1024 * 1024)
    except ValueError:
        return 10 * 1024 * 1024


def storage_root() -> Path:
    env = os.getenv('DOCUMENTOS_DIR', '').strip()
    root = Path(env) if env else Path(__file__).resolve().parents[2] / 'data' / 'documentos'
    root.mkdir(parents=True, exist_ok=True)
    return root


def caminho_arquivo(sha256: str) -> Path | None:
    if not _SHA.match(sha256 or ''):
        return None
    path = storage_root() / f'{sha256}.pdf'
    return path if path.is_file() else None


def equipe_config(equipe: str) -> dict:
    cfg = EQUIPES.get(equipe)
    if not cfg:
        raise DocumentoErro('Equipe desconhecida.')
    return cfg


def ultima_versao(equipe: str) -> DocumentoVersao | None:
    return (
        DocumentoVersao.query.filter_by(equipe=equipe).order_by(DocumentoVersao.versao.desc()).first()
    )


def estado_publicado(equipe: str) -> list[dict]:
    """Documentos em vigor. sha256=None significa 'usar o PDF que veio no instalador'."""
    versao = ultima_versao(equipe)
    if versao:
        return [dict(a) for a in versao.arquivos or []]
    return [dict(s, sha256=None, tamanho=None, paginas=None) for s in equipe_config(equipe)['slots']]


def manifesto() -> dict:
    equipes = {}
    for equipe in EQUIPES:
        versao = ultima_versao(equipe)
        if not versao:
            continue
        equipes[equipe] = {
            'versao': versao.versao,
            'publicado_em': versao.publicado_em.isoformat() + 'Z',
            'arquivos': [
                {
                    k: a.get(k)
                    for k in ('slot', 'ordem', 'nome_arquivo', 'titulo', 'tipo', 'sha256', 'tamanho')
                }
                for a in versao.arquivos or []
            ],
        }
    return equipes


def _rascunho_dict(r: DocumentoRascunho) -> dict:
    return {
        'titulo': r.titulo,
        'tipo': r.tipo,
        'sha256': r.sha256,
        'tamanho': r.tamanho,
        'tamanho_original': r.tamanho_original,
        'paginas': r.paginas,
        'compressao': r.compressao,
        'enviado_por': r.enviado_por,
        'enviado_em': r.enviado_em.isoformat() + 'Z',
    }


def estado_admin() -> list[dict]:
    saida = []
    for equipe, cfg in EQUIPES.items():
        versao = ultima_versao(equipe)
        rascunhos = {r.slot: r for r in DocumentoRascunho.query.filter_by(equipe=equipe).all()}
        docs = []
        for a in estado_publicado(equipe):
            r = rascunhos.pop(a['slot'], None)
            docs.append(
                {
                    'slot': a['slot'],
                    'ordem': a['ordem'],
                    'titulo': a.get('titulo'),
                    'nome_arquivo': a['nome_arquivo'],
                    'tipo': a.get('tipo'),
                    'publicado': {
                        'sha256': a.get('sha256'),
                        'tamanho': a.get('tamanho'),
                        'paginas': a.get('paginas'),
                        'origem': 'servidor' if a.get('sha256') else 'instalador',
                    },
                    'rascunho': _rascunho_dict(r) if r else None,
                }
            )
        for r in sorted(rascunhos.values(), key=lambda x: x.ordem):
            docs.append(
                {
                    'slot': r.slot,
                    'ordem': r.ordem,
                    'titulo': r.titulo,
                    'nome_arquivo': r.nome_arquivo,
                    'tipo': r.tipo,
                    'publicado': None,
                    'rascunho': _rascunho_dict(r),
                }
            )
        docs.sort(key=lambda d: d['ordem'])
        saida.append(
            {
                'id': equipe,
                'nome': cfg['nome'],
                'sistema': cfg['sistema'],
                'tipo_editavel': cfg['tipo_editavel'],
                'tipos': TIPOS_PJE if cfg['tipo_editavel'] else [],
                'pode_adicionar': cfg['pode_adicionar'],
                'versao': versao.versao if versao else 0,
                'publicado_em': versao.publicado_em.isoformat() + 'Z' if versao else None,
                'publicado_por': versao.publicado_por if versao else None,
                'pendentes': sum(1 for d in docs if d['rascunho']),
                'documentos': docs,
            }
        )
    return saida


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for bloco in iter(lambda: fh.read(1024 * 1024), b''):
            h.update(bloco)
    return h.hexdigest()


def _info_pdf(path: Path) -> tuple[int, bool]:
    """(páginas, assinado digitalmente). Levanta DocumentoErro se não for PDF legível."""
    from pypdf import PdfReader

    try:
        reader = PdfReader(str(path))
        if reader.is_encrypted:
            raise DocumentoErro('PDF protegido por senha não é aceito.')
        paginas = len(reader.pages)
        acro = reader.trailer['/Root'].get('/AcroForm')
        assinado = bool(acro and acro.get_object().get('/SigFlags'))
    except DocumentoErro:
        raise
    except Exception as exc:
        raise DocumentoErro(f'Arquivo não é um PDF válido ({exc.__class__.__name__}).')
    if paginas == 0:
        raise DocumentoErro('PDF sem páginas.')
    return paginas, assinado


def _comprimir(origem: Path, paginas: int) -> tuple[Path, str]:
    gs = shutil.which('gs')
    if not gs:
        logger.warning('Ghostscript (gs) não encontrado; PDF mantido sem compressão.')
        return origem, 'sem_ghostscript'
    destino = origem.with_name(origem.stem + '.gs.pdf')
    cmd = [
        gs,
        '-sDEVICE=pdfwrite',
        '-dCompatibilityLevel=1.5',
        '-dPDFSETTINGS=/ebook',
        '-dDetectDuplicateImages=true',
        '-dNOPAUSE',
        '-dBATCH',
        '-dQUIET',
        '-dSAFER',
        f'-sOutputFile={destino}',
        str(origem),
    ]
    try:
        subprocess.run(cmd, check=True, timeout=300, capture_output=True)
        paginas_gs, _ = _info_pdf(destino)
    except (subprocess.SubprocessError, OSError, DocumentoErro) as exc:
        logger.warning('Falha ao comprimir PDF: %s', exc)
        return origem, 'falhou'
    if paginas_gs != paginas:
        return origem, 'paginas_divergentes'
    if destino.stat().st_size >= origem.stat().st_size:
        return origem, 'original_menor'
    return destino, 'comprimido'


def _limpar_nome(titulo: str) -> str:
    nome = _NOME_INVALIDO.sub(' ', titulo or '')
    nome = re.sub(r'\s+', ' ', nome).strip(' .')
    return nome[:120]


def salvar_upload(equipe: str, slot: str, arquivo, username: str, titulo: str = '', tipo: str = '',
                  comprimir: bool = True) -> DocumentoRascunho:
    cfg = equipe_config(equipe)
    publicados = {a['slot']: a for a in estado_publicado(equipe)}
    rascunho = DocumentoRascunho.query.filter_by(equipe=equipe, slot=slot).first() if slot != 'novo' else None

    if slot == 'novo':
        if not cfg['pode_adicionar']:
            raise DocumentoErro('Esta equipe não permite adicionar documentos.')
        titulo_limpo = _limpar_nome(titulo)
        if not titulo_limpo:
            raise DocumentoErro('Informe o nome do documento novo.')
        ordens = [a['ordem'] for a in publicados.values()]
        ordens += [r.ordem for r in DocumentoRascunho.query.filter_by(equipe=equipe).all()]
        ordem = max(ordens or [0]) + 1
        if ordem > cfg.get('max_documentos', 9):
            raise DocumentoErro('Limite de documentos desta equipe atingido.')
        base = {
            'slot': str(ordem),
            'ordem': ordem,
            'nome_arquivo': f'{ordem}. {titulo_limpo}.pdf',
            'titulo': titulo_limpo,
            'tipo': 'Documentação',
        }
    else:
        base = publicados.get(slot)
        if not base and rascunho:
            base = {'slot': slot, 'ordem': rascunho.ordem, 'nome_arquivo': rascunho.nome_arquivo,
                    'titulo': rascunho.titulo, 'tipo': rascunho.tipo}
        if not base:
            raise DocumentoErro('Documento não encontrado nesta equipe.')

    if tipo and (not cfg['tipo_editavel'] or tipo not in TIPOS_PJE):
        raise DocumentoErro('Tipo de documento inválido para esta equipe.')

    with tempfile.TemporaryDirectory(dir=storage_root()) as tmp:
        origem = Path(tmp) / 'original.pdf'
        arquivo.save(str(origem))
        tamanho_original = origem.stat().st_size
        paginas, assinado = _info_pdf(origem)
        if assinado:
            final, compressao = origem, 'assinado'
        elif not comprimir:
            final, compressao = origem, 'desativada'
        else:
            final, compressao = _comprimir(origem, paginas)
        tamanho = final.stat().st_size
        if tamanho > _max_bytes():
            raise DocumentoErro(
                f'PDF ficou com {tamanho / 1024 / 1024:.1f} MB; o limite é '
                f'{_max_bytes() / 1024 / 1024:.0f} MB. Reduza o arquivo antes de enviar.'
            )
        sha = _sha256(final)
        destino = storage_root() / f'{sha}.pdf'
        if not destino.exists():
            shutil.move(str(final), destino)

    if not rascunho:
        rascunho = DocumentoRascunho(equipe=equipe, slot=base['slot'])
        db.session.add(rascunho)
    rascunho.ordem = base['ordem']
    rascunho.nome_arquivo = base['nome_arquivo']
    rascunho.titulo = base.get('titulo') or base['nome_arquivo']
    rascunho.tipo = tipo or rascunho.tipo or base.get('tipo')
    rascunho.sha256 = sha
    rascunho.tamanho = tamanho
    rascunho.tamanho_original = tamanho_original
    rascunho.paginas = paginas
    rascunho.compressao = compressao
    rascunho.enviado_por = username
    rascunho.enviado_em = datetime.utcnow()
    db.session.commit()
    return rascunho


def definir_tipo(equipe: str, slot: str, tipo: str, username: str) -> DocumentoRascunho:
    cfg = equipe_config(equipe)
    if not cfg['tipo_editavel'] or tipo not in TIPOS_PJE:
        raise DocumentoErro('Tipo de documento inválido para esta equipe.')
    rascunho = DocumentoRascunho.query.filter_by(equipe=equipe, slot=slot).first()
    if not rascunho:
        base = next((a for a in estado_publicado(equipe) if a['slot'] == slot), None)
        if not base:
            raise DocumentoErro('Documento não encontrado nesta equipe.')
        rascunho = DocumentoRascunho(
            equipe=equipe,
            slot=slot,
            ordem=base['ordem'],
            nome_arquivo=base['nome_arquivo'],
            titulo=base.get('titulo') or base['nome_arquivo'],
        )
        db.session.add(rascunho)
    rascunho.tipo = tipo
    rascunho.enviado_por = username
    rascunho.enviado_em = datetime.utcnow()
    db.session.commit()
    return rascunho


def descartar_rascunho(equipe: str, slot: str) -> None:
    equipe_config(equipe)
    DocumentoRascunho.query.filter_by(equipe=equipe, slot=slot).delete()
    db.session.commit()


def publicar(equipe: str, username: str) -> DocumentoVersao:
    equipe_config(equipe)
    rascunhos = DocumentoRascunho.query.filter_by(equipe=equipe).all()
    if not rascunhos:
        raise DocumentoErro('Não há alterações para publicar.')

    arquivos = {a['slot']: a for a in estado_publicado(equipe)}
    for r in rascunhos:
        atual = arquivos.get(r.slot) or {
            'slot': r.slot,
            'ordem': r.ordem,
            'nome_arquivo': r.nome_arquivo,
            'titulo': r.titulo,
            'tipo': r.tipo,
            'sha256': None,
            'tamanho': None,
            'paginas': None,
        }
        if r.sha256:
            if not caminho_arquivo(r.sha256):
                raise DocumentoErro(f'Arquivo do rascunho "{r.titulo}" sumiu do servidor. Envie de novo.')
            atual.update(sha256=r.sha256, tamanho=r.tamanho, paginas=r.paginas, titulo=r.titulo)
        if r.tipo:
            atual['tipo'] = r.tipo
        arquivos[r.slot] = atual

    anterior = ultima_versao(equipe)
    versao = DocumentoVersao(
        equipe=equipe,
        versao=(anterior.versao if anterior else 0) + 1,
        arquivos=sorted(arquivos.values(), key=lambda a: a['ordem']),
        publicado_por=username,
    )
    db.session.add(versao)
    for r in rascunhos:
        db.session.delete(r)
    db.session.commit()
    return versao
