# -*- coding: utf-8 -*-
"""Downloads de aplicativos (ex.: Valença Suite) — exige login."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

from flask import Blueprint, jsonify, send_file, session

from app.services.valenca_build_service import OFFICIAL_APP_ID, can_access_app
from app.utils.auth_decorator import login_required

bp = Blueprint("downloads", __name__, url_prefix="/api/downloads")

_SAFE_NAME = re.compile(r"^[A-Za-z0-9._-]+$")
_SAFE_APP = re.compile(r"^[a-z0-9_-]+$")


def _downloads_root() -> Path:
    env = os.getenv("DOWNLOADS_DIR", "").strip()
    if env:
        return Path(env).resolve()
    # app/routes/downloads.py → raiz do Scrapping-Unificado
    return Path(__file__).resolve().parents[2] / "data" / "downloads"


def _app_dir(app_id: str) -> Path | None:
    if not _SAFE_APP.match(app_id or ""):
        return None
    path = (_downloads_root() / app_id).resolve()
    root = _downloads_root().resolve()
    if not str(path).startswith(str(root)):
        return None
    return path


def _current_user() -> tuple[str, str]:
    return (session.get("username") or "", session.get("role") or "user")


def _read_latest(app_dir: Path) -> dict | None:
    meta = app_dir / "latest.json"
    if not meta.is_file():
        return None
    try:
        with open(meta, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return None


@bp.route("/listar", methods=["GET"])
@login_required
def listar_downloads():
    """Lista apps visíveis: canal oficial (valenca) para todos; recortes só para admin/destinatário."""
    root = _downloads_root()
    root.mkdir(parents=True, exist_ok=True)
    username, role = _current_user()
    apps = []
    for child in sorted(root.iterdir() if root.is_dir() else []):
        if not child.is_dir():
            continue
        app_id = child.name
        if not can_access_app(app_id, username, role):
            continue
        meta = _read_latest(child)
        if not meta:
            continue
        official = app_id == OFFICIAL_APP_ID
        apps.append(
            {
                "app_id": app_id,
                "name": meta.get("name") or child.name,
                "version": meta.get("version") or "",
                "released_at": meta.get("released_at") or "",
                "notes": meta.get("notes") or "",
                "files": meta.get("files") or [],
                "modules": meta.get("modules") or [],
                "official": official,
            }
        )
    apps.sort(key=lambda a: (not a["official"], a.get("name") or a["app_id"]))
    return jsonify({"success": True, "apps": apps, "total": len(apps)})


@bp.route("/latest/<app_id>", methods=["GET"])
@login_required
def latest(app_id: str):
    username, role = _current_user()
    if not can_access_app(app_id, username, role):
        return jsonify({"error": "Aplicativo não encontrado"}), 404
    app_dir = _app_dir(app_id)
    if not app_dir or not app_dir.is_dir():
        return jsonify({"error": "Aplicativo não encontrado"}), 404
    meta = _read_latest(app_dir)
    if not meta:
        return jsonify({"error": "Nenhuma versão publicada ainda"}), 404
    return jsonify({"success": True, "app": meta})


@bp.route("/file/<app_id>/<filename>", methods=["GET"])
@login_required
def download_file(app_id: str, filename: str):
    """Baixa um arquivo publicado (Setup.exe / zip)."""
    username, role = _current_user()
    if not can_access_app(app_id, username, role):
        return jsonify({"error": "Aplicativo não encontrado"}), 404
    if not _SAFE_NAME.match(filename or ""):
        return jsonify({"error": "Nome de arquivo inválido"}), 400
    app_dir = _app_dir(app_id)
    if not app_dir:
        return jsonify({"error": "Aplicativo inválido"}), 400

    path = (app_dir / filename).resolve()
    if not str(path).startswith(str(app_dir.resolve())):
        return jsonify({"error": "Caminho inválido"}), 400
    if not path.is_file():
        return jsonify({"error": "Arquivo não encontrado"}), 404

    # Só permite baixar arquivos listados no latest.json (quando existir)
    meta = _read_latest(app_dir)
    if meta:
        permitidos = {f.get("filename") for f in (meta.get("files") or []) if f.get("filename")}
        if permitidos and filename not in permitidos:
            return jsonify({"error": "Arquivo não autorizado nesta versão"}), 403

    return send_file(path, as_attachment=True, download_name=filename)
