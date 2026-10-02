# -*- coding: utf-8 -*-
"""Pedidos de instalador filtrado da Valença Suite (GitHub Actions + disco)."""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import threading
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

OFFICIAL_APP_ID = "valenca"
ACTIONS_WORKFLOW_URL = (
    "https://github.com/MoesioFiuza/Valenca-suite/actions/workflows/build-windows.yml"
)
DISPATCH_URL = (
    "https://api.github.com/repos/MoesioFiuza/Valenca-suite"
    "/actions/workflows/build-windows.yml/dispatches"
)
BUILD_TIMEOUT = timedelta(minutes=15)
_SAFE_APP = re.compile(r"^[a-z0-9_-]+$")
_LOCK = threading.Lock()

_CLIENT_HINTS = ("enel", "cagece", "ndi", "movida", "jusbr", "dataweb")
_PLACE_HINTS = ("tjsp", "tjrj", "tjce", "sp", "rj", "ce")
_SYSTEM_HINTS = ("esaj", "eproc", "pje")


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def downloads_root() -> Path:
    env = os.getenv("DOWNLOADS_DIR", "").strip()
    if env:
        return Path(env).resolve()
    return _project_root() / "data" / "downloads"


def _builds_path() -> Path:
    return _project_root() / "data" / "builds.json"


def _modules_path() -> Path:
    return _project_root() / "data" / "valenca_modules.json"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime | None = None) -> str:
    return (dt or _utcnow()).isoformat()


def read_latest(app_id: str) -> dict | None:
    if not _SAFE_APP.match(app_id or ""):
        return None
    meta = downloads_root() / app_id / "latest.json"
    if not meta.is_file():
        return None
    try:
        with open(meta, encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def official_version() -> str:
    meta = read_latest(OFFICIAL_APP_ID) or {}
    return str(meta.get("version") or "").strip()


def load_catalog() -> dict:
    path = _modules_path()
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def catalog_module_ids() -> set[str]:
    ids: set[str] = set()
    for cat in load_catalog().get("categories") or []:
        for mod in cat.get("modules") or []:
            mid = (mod.get("id") or "").strip()
            if mid:
                ids.add(mid)
    return ids


def _load_builds_unlocked() -> dict:
    path = _builds_path()
    if not path.exists():
        return {"builds": []}
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            return {"builds": []}
        data.setdefault("builds", [])
        return data
    except (OSError, json.JSONDecodeError):
        return {"builds": []}


def _save_builds_unlocked(data: dict) -> None:
    path = _builds_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
    tmp.replace(path)


def cache_key(version: str, modules: list[str]) -> str:
    ordered = ",".join(sorted(modules))
    return f"{version}|{ordered}"


def suggest_app_id(modules: list[str]) -> str:
    blob = " ".join(modules).lower()
    parts: list[str] = []
    for hint in _CLIENT_HINTS:
        if hint in blob and hint not in parts:
            parts.append(hint)
    for hint in _PLACE_HINTS:
        if re.search(rf"(^|_){re.escape(hint)}(_|$)", blob) and hint not in parts:
            parts.append(hint)
    if not any(h in parts for h in _CLIENT_HINTS):
        for hint in _SYSTEM_HINTS:
            if re.search(rf"(^|_){re.escape(hint)}(_|$)", blob) and hint not in parts:
                parts.append(hint)
    if not parts:
        tokens: list[str] = []
        for mid in modules:
            for tok in re.split(r"[^a-z0-9]+", mid.lower()):
                if tok and tok not in {"hab", "rasp", "utils"} and tok not in tokens:
                    tokens.append(tok)
        parts = tokens[:4]
    slug = "valenca-" + "-".join(parts) if parts else "valenca-custom"
    slug = re.sub(r"[^a-z0-9_-]", "", slug).strip("-_")
    if not slug or slug == OFFICIAL_APP_ID:
        slug = "valenca-custom"
    digest = hashlib.sha1(",".join(sorted(modules)).encode()).hexdigest()[:6]
    if len(slug) > 40:
        slug = f"valenca-{digest}"
    return slug


def _unique_app_id(modules: list[str], existing: list[dict]) -> str:
    base = suggest_app_id(modules)
    wanted = set(modules)
    taken = {
        b.get("app_id")
        for b in existing
        if b.get("app_id") and set(b.get("modules") or []) != wanted
    }
    if base not in taken and base != OFFICIAL_APP_ID:
        return base
    digest = hashlib.sha1(",".join(sorted(modules)).encode()).hexdigest()[:8]
    candidate = f"{base}-{digest}"
    candidate = re.sub(r"[^a-z0-9_-]", "", candidate)
    if candidate == OFFICIAL_APP_ID:
        candidate = f"valenca-build-{digest}"
    return candidate[:48]


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        raw = value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def _setup_filename(latest: dict | None) -> str | None:
    if not latest:
        return None
    files = latest.get("files") or []
    for item in files:
        if (item.get("kind") or "").lower() == "setup" and item.get("filename"):
            return item["filename"]
    for item in files:
        name = item.get("filename") or ""
        if name.lower().endswith(".exe"):
            return name
    return None


def _is_ready_on_disk(build: dict) -> bool:
    app_id = build.get("app_id") or ""
    latest = read_latest(app_id)
    if not latest:
        return False
    if latest.get("app_id") == OFFICIAL_APP_ID:
        return False
    disk_build = str(latest.get("build_id") or "")
    if disk_build and disk_build == str(build.get("build_id") or ""):
        return True
    disk_modules = latest.get("modules")
    if disk_modules is not None and set(disk_modules) == set(build.get("modules") or []):
        disk_ver = str(latest.get("version") or "")
        if disk_ver and disk_ver == str(build.get("official_version") or ""):
            return True
    released = _parse_dt(latest.get("released_at"))
    created = _parse_dt(build.get("created_at"))
    if released and created and released >= created - timedelta(minutes=1):
        return True
    return False


def refresh_builds() -> list[dict]:
    with _LOCK:
        data = _load_builds_unlocked()
        changed = False
        now = _utcnow()
        for build in data["builds"]:
            if build.get("status") != "pendente":
                continue
            if _is_ready_on_disk(build):
                latest = read_latest(build.get("app_id") or "")
                build["status"] = "pronto"
                build["ready_at"] = _iso(now)
                build["setup_filename"] = _setup_filename(latest)
                build["error"] = ""
                changed = True
                logger.info(
                    "Build %s pronto em disco (app_id=%s)",
                    build.get("id"),
                    build.get("app_id"),
                )
                continue
            created = _parse_dt(build.get("created_at")) or now
            if now - created >= BUILD_TIMEOUT:
                build["status"] = "falha"
                build["error"] = (
                    "Timeout (~15 min): latest.json não chegou em disco. "
                    f"Verifique o GitHub Actions: {ACTIONS_WORKFLOW_URL}"
                )
                build["actions_url"] = ACTIONS_WORKFLOW_URL
                changed = True
                logger.error(
                    "Build %s falhou por timeout (app_id=%s). Actions: %s",
                    build.get("id"),
                    build.get("app_id"),
                    ACTIONS_WORKFLOW_URL,
                )
        if changed:
            _save_builds_unlocked(data)
        return list(data["builds"])


def list_builds() -> list[dict]:
    builds = refresh_builds()
    builds.sort(key=lambda b: b.get("created_at") or "", reverse=True)
    return builds


def assigned_usernames_for_app(app_id: str) -> set[str]:
    if not app_id or app_id == OFFICIAL_APP_ID:
        return set()
    data = _load_builds_unlocked()
    names: set[str] = set()
    for build in data.get("builds") or []:
        if build.get("app_id") == app_id:
            user = (build.get("username") or "").strip().lower()
            if user:
                names.add(user)
    return names


def can_access_app(app_id: str, username: str | None, role: str | None) -> bool:
    if not app_id:
        return False
    if app_id == OFFICIAL_APP_ID:
        return True
    if role == "admin":
        return True
    user = (username or "").strip().lower()
    if not user:
        return False
    return user in assigned_usernames_for_app(app_id)


def _dispatch_github(app_id: str, build_id: str, modules: list[str]) -> None:
    token = os.getenv("GITHUB_BUILD_TOKEN", "").strip()
    if not token:
        raise RuntimeError(
            "GITHUB_BUILD_TOKEN não está configurado no servidor."
        )
    payload = json.dumps(
        {
            "ref": "main",
            "inputs": {
                "create_release": "false",
                "modules": ",".join(modules),
                "app_id": app_id,
                "build_id": build_id,
            },
        }
    ).encode("utf-8")
    req = Request(DISPATCH_URL, data=payload, method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("Content-Type", "application/json")
    try:
        with urlopen(req, timeout=30) as resp:
            if resp.status not in (201, 204):
                raise RuntimeError(f"GitHub devolveu HTTP {resp.status}")
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"Falha ao disparar Actions (HTTP {exc.code}): {body}") from exc
    except URLError as exc:
        raise RuntimeError(f"Não foi possível contactar o GitHub: {exc.reason}") from exc


def create_build(modules: list[str], username: str, created_by: str) -> tuple[dict, str]:
    allowed = catalog_module_ids()
    clean: list[str] = []
    seen: set[str] = set()
    for mid in modules:
        mid = str(mid).strip()
        if not mid or mid in seen:
            continue
        if mid not in allowed:
            raise ValueError(f"Módulo desconhecido: {mid}")
        seen.add(mid)
        clean.append(mid)
    if not clean:
        raise ValueError("Seleccione pelo menos um módulo.")

    dest = (username or "").strip()
    version = official_version()
    key = cache_key(version, clean)

    with _LOCK:
        data = _load_builds_unlocked()
        builds = data["builds"]

        reusable = next(
            (
                b
                for b in reversed(builds)
                if b.get("cache_key") == key
                and b.get("status") in ("pronto", "pendente")
                and b.get("app_id") != OFFICIAL_APP_ID
            ),
            None,
        )

        build_id = str(uuid.uuid4())
        pedido: dict[str, Any] = {
            "id": str(uuid.uuid4()),
            "build_id": build_id,
            "app_id": "",
            "modules": clean,
            "username": dest,
            "created_by": created_by,
            "created_at": _iso(),
            "status": "pendente",
            "official_version": version,
            "cache_key": key,
            "error": "",
            "actions_url": ACTIONS_WORKFLOW_URL,
            "setup_filename": None,
            "cached": False,
        }

        if reusable:
            pedido["app_id"] = reusable["app_id"]
            pedido["build_id"] = reusable.get("build_id") or build_id
            pedido["cached"] = True
            if reusable.get("status") == "pronto" or _is_ready_on_disk(reusable):
                latest = read_latest(reusable["app_id"])
                pedido["status"] = "pronto"
                pedido["ready_at"] = _iso()
                pedido["setup_filename"] = reusable.get("setup_filename") or _setup_filename(latest)
                builds.append(pedido)
                _save_builds_unlocked(data)
                return pedido, "Instalador já existia para esta combinação — reutilizado, sem novo build."
            builds.append(pedido)
            _save_builds_unlocked(data)
            return pedido, "Já existe um build pendente para esta combinação. Aguarde ~5–6 minutos."

        app_id = _unique_app_id(clean, builds)
        if app_id == OFFICIAL_APP_ID or not _SAFE_APP.match(app_id):
            raise ValueError("app_id inválido gerado para o instalador.")
        pedido["app_id"] = app_id
        builds.append(pedido)
        _save_builds_unlocked(data)

    try:
        _dispatch_github(app_id, pedido["build_id"], clean)
    except Exception as exc:
        with _LOCK:
            data = _load_builds_unlocked()
            for b in data["builds"]:
                if b.get("id") == pedido["id"]:
                    b["status"] = "falha"
                    b["error"] = str(exc)
                    b["actions_url"] = ACTIONS_WORKFLOW_URL
                    pedido = b
                    break
            _save_builds_unlocked(data)
        logger.exception("Falha ao disparar workflow Valença Suite")
        raise RuntimeError(str(exc)) from exc

    logger.info(
        "Disparado build Valença filtrado app_id=%s build_id=%s modules=%s",
        app_id,
        pedido["build_id"],
        ",".join(clean),
    )
    return pedido, "Build pedido. Costuma levar 5–6 minutos. Não clique de novo à toa."
