# -*- coding: utf-8 -*-
"""Documentos de habilitação da Valença Suite (manifesto para o app + gestão pelo admin)."""
from __future__ import annotations

from flask import Blueprint, jsonify, request, send_file, session

from app.services import documentos_service as docs
from app.services.audit_service import AuditService
from app.utils.auth_decorator import admin_required, login_required

bp = Blueprint('documentos', __name__, url_prefix='/api/documentos')


def _erro(exc: Exception, status: int = 400):
    return jsonify({'success': False, 'error': str(exc)}), status


@bp.route('/manifest', methods=['GET'])
@login_required
def manifest():
    return jsonify({'success': True, 'equipes': docs.manifesto()})


@bp.route('/arquivo/<sha256>', methods=['GET'])
@login_required
def baixar(sha256: str):
    path = docs.caminho_arquivo(sha256)
    if not path:
        return jsonify({'success': False, 'error': 'Arquivo não encontrado'}), 404
    nome = request.args.get('nome') or f'{sha256[:12]}.pdf'
    return send_file(path, mimetype='application/pdf', as_attachment=True, download_name=nome)


@bp.route('/admin', methods=['GET'])
@admin_required
def admin_estado():
    return jsonify({'success': True, 'equipes': docs.estado_admin()})


@bp.route('/admin/<equipe>/<slot>', methods=['POST'])
@admin_required
def admin_upload(equipe: str, slot: str):
    arquivo = request.files.get('file')
    if not arquivo or not arquivo.filename:
        return _erro('Selecione um arquivo PDF.')
    if not arquivo.filename.lower().endswith('.pdf'):
        return _erro('Envie um arquivo .pdf.')
    username = session.get('username') or ''
    try:
        r = docs.salvar_upload(
            equipe,
            slot,
            arquivo,
            username,
            titulo=request.form.get('titulo', ''),
            tipo=request.form.get('tipo', ''),
            comprimir=request.form.get('comprimir', '1') != '0',
        )
    except docs.DocumentoErro as exc:
        return _erro(exc)
    AuditService.log(
        'documentos.upload',
        username=username,
        details={
            'equipe': equipe,
            'slot': r.slot,
            'arquivo_original': arquivo.filename,
            'nome_arquivo': r.nome_arquivo,
            'tamanho_original': r.tamanho_original,
            'tamanho': r.tamanho,
            'compressao': r.compressao,
        },
    )
    return jsonify({'success': True, 'slot': r.slot})


@bp.route('/admin/<equipe>/<slot>/tipo', methods=['POST'])
@admin_required
def admin_tipo(equipe: str, slot: str):
    tipo = (request.get_json(silent=True) or {}).get('tipo', '')
    username = session.get('username') or ''
    try:
        docs.definir_tipo(equipe, slot, tipo, username)
    except docs.DocumentoErro as exc:
        return _erro(exc)
    AuditService.log('documentos.tipo', username=username, details={'equipe': equipe, 'slot': slot, 'tipo': tipo})
    return jsonify({'success': True})


@bp.route('/admin/<equipe>/<slot>/rascunho', methods=['DELETE'])
@admin_required
def admin_descartar(equipe: str, slot: str):
    try:
        docs.descartar_rascunho(equipe, slot)
    except docs.DocumentoErro as exc:
        return _erro(exc)
    return jsonify({'success': True})


@bp.route('/admin/<equipe>/publicar', methods=['POST'])
@admin_required
def admin_publicar(equipe: str):
    username = session.get('username') or ''
    try:
        versao = docs.publicar(equipe, username)
    except docs.DocumentoErro as exc:
        return _erro(exc)
    AuditService.log(
        'documentos.publicar',
        username=username,
        details={'equipe': equipe, 'versao': versao.versao},
    )
    return jsonify({'success': True, 'versao': versao.versao})
