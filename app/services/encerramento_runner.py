"""Raspagem de movimentações (sem Excel) para endpoints de encerramento CE."""

from __future__ import annotations

import importlib
import logging
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from config.cli_tribunal_registry import modo_permitido
from config.settings import HEADLESS_MODE
from config.tribunais import (
    TRIBUNAIS_MAP,
    identificar_tribunal_por_processo,
    processo_compativel_com_tribunal,
)
from scrapers.consulta_cli_common import escala_sleep_scraper_module, import_class
from scrapers.raspar_consulta_movimentacoes_core import _payload_extras
from scrapers.raspar_consulta_planilhas_core import _split_indexed_chunks

logger = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parents[2]

HELPERS_POR_TRIBUNAL: dict[str, str] = {
    "8.06": "scrapers.tjce.cli_helpers",
    "8.06_esaj": "scrapers.tjce_esaj.cli_helpers",
}

WORKERS_PADRAO = 3


def validar_numeros(tribunal_key: str, numeros: list[str]) -> str | None:
    if tribunal_key not in HELPERS_POR_TRIBUNAL:
        return f"Tribunal não suportado: {tribunal_key!r}."
    if tribunal_key not in TRIBUNAIS_MAP:
        return "Tribunal inválido."
    if not modo_permitido(tribunal_key, "chrome", "movimentacoes"):
        return "Movimentações não disponíveis para este tribunal."
    if not numeros:
        return "Nenhum número de processo."

    for n in numeros:
        det = identificar_tribunal_por_processo(n)
        if not processo_compativel_com_tribunal(det, tribunal_key):
            return (
                f"Processo {n!r} pertence ao tribunal {det!r}, não a {tribunal_key!r}. "
                "Use só processos do Ceará (8.06)."
            )
    return None


def raspar_movimentacoes(
    tribunal_key: str,
    numeros: list[str],
    *,
    workers: int = WORKERS_PADRAO,
    progress_cb: Callable[[dict], None] | None = None,
) -> list[dict]:
    """Executa raspagem só movimentações; retorna lista de resultados normalizados."""
    helpers_module = HELPERS_POR_TRIBUNAL[tribunal_key]
    ch = importlib.import_module(helpers_module)
    cfg = dict(TRIBUNAIS_MAP[tribunal_key])
    if HEADLESS_MODE:
        cfg["headless"] = True

    workers = max(1, min(int(workers or WORKERS_PADRAO), 8))
    fator_sleep = 1.0
    resultados: list[dict] = []
    extras = _payload_extras(ch)
    MovCls = import_class(ch.MOV_CLASS_PATH)

    if workers == 1:
        with escala_sleep_scraper_module(ch.SLEEP_MODULE, fator_sleep):
            scraper = MovCls(cfg)
            try:
                scraper.setup_driver()
                for num in numeros:
                    raw = scraper.raspar_processo(num)
                    res = ch.normalizar_resultado_scraper(num, raw)
                    resultados.append(res)
                    if progress_cb:
                        progress_cb(res)
            finally:
                scraper.close()
    else:
        indexed = list(enumerate(numeros))
        chunks = _split_indexed_chunks(indexed, workers)
        n_chunks = len(chunks)
        logger.info(
            "Encerramento CE: %s workers, %s processos (%s)",
            n_chunks,
            len(numeros),
            tribunal_key,
        )
        root_str = str(_ROOT)
        payloads = [
            {
                "root": root_str,
                "chunk": [[i, n] for i, n in chunk],
                "cfg": cfg,
                "fator_sleep": fator_sleep,
                "worker_id": wi + 1,
                "somente_movimentacoes": True,
                **extras,
            }
            for wi, chunk in enumerate(chunks)
        ]
        slots: list[dict | None] = [None] * len(numeros)
        with ProcessPoolExecutor(max_workers=n_chunks) as pool:
            futures = [pool.submit(_mp_worker_chunk, p, helpers_module) for p in payloads]
            for fut in as_completed(futures):
                for idx, res in fut.result():
                    slots[idx] = res
                    if progress_cb:
                        progress_cb(res)
        resultados = [slots[i] for i in range(len(numeros)) if slots[i] is not None]

    return resultados


def _mp_worker_chunk(payload: dict, helpers_module: str) -> list[tuple[int, dict]]:
    ch = importlib.import_module(helpers_module)
    if hasattr(ch, "mp_worker_tjce_chunk"):
        return ch.mp_worker_tjce_chunk(payload)
    from scrapers.consulta_cli_common import mp_worker_consulta_chunk

    p = dict(payload)
    p.setdefault("tribunal_key", ch.TRIBUNAL_KEY)
    p.setdefault("sleep_module", ch.SLEEP_MODULE)
    p.setdefault("cli_class_path", ch.CLI_CLASS_PATH)
    p.setdefault("mov_class_path", ch.MOV_CLASS_PATH)
    if hasattr(ch, "POL_CLASS_PATH"):
        p.setdefault("pol_class_path", ch.POL_CLASS_PATH)
    return mp_worker_consulta_chunk(p)


def executar_encerramento(
    tribunal_key: str,
    numeros: list[str],
    *,
    workers: int = WORKERS_PADRAO,
    progress_cb: Callable[[dict], None] | None = None,
    should_abort: Callable[[], bool] | None = None,
) -> dict:
    """
    Raspagem + análise de encerramento. Sem Excel, sem registo em extracoes.

    Returns:
        { "ok": bool, "error": str | None, "resultado": dict | None }
    """
    from app.services.movimentacoes_encerramento import montar_resultado_job

    err = validar_numeros(tribunal_key, numeros)
    if err:
        return {"ok": False, "error": err, "resultado": None}

    if should_abort and should_abort():
        return {"ok": False, "error": "Job cancelado.", "resultado": None}

    def _prog(res: dict) -> None:
        if should_abort and should_abort():
            return
        if progress_cb:
            progress_cb(res)

    try:
        resultados = raspar_movimentacoes(
            tribunal_key,
            numeros,
            workers=workers,
            progress_cb=_prog,
        )
        if should_abort and should_abort():
            return {"ok": False, "error": "Job cancelado.", "resultado": None}
        resultado = montar_resultado_job(tribunal_key, workers, resultados)
        return {"ok": True, "error": None, "resultado": resultado}
    except Exception as exc:
        logger.exception("Encerramento CE %s", tribunal_key)
        return {"ok": False, "error": str(exc), "resultado": None}
