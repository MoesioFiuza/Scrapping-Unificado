
from __future__ import annotations

import importlib
import logging
import shutil
import time
import uuid
from collections.abc import Callable
from pathlib import Path

import pandas as pd

from app.services.extracoes_service import ExtracoesService
from config.cli_tribunal_registry import modo_permitido, obter_helpers
from config.tribunais import (
    TRIBUNAIS_MAP,
    identificar_tribunal_por_processo,
    processo_compativel_com_tribunal,
)

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT / "data" / "output"


def _slug_do_helpers(helpers_module: str) -> str:
    ch = importlib.import_module(helpers_module)
    return getattr(ch, "SLUG", getattr(ch, "TRIBUNAL_KEY", "cli").replace(".", "_"))


def _renomear_se_existir(origem: Path, destino: Path) -> Path:
    if destino.exists():
        destino.unlink()
    shutil.move(str(origem), str(destino))
    return destino


def executar_cli_e_registrar(
    username: str,
    tribunal_key: str,
    browser: str,
    job_mode: str,
    numeros: list[str],
    workers: int = 3,
    *,
    progress_cb: Callable[[dict], None] | None = None,
) -> dict:
    """
    Corre main_movimentacoes / main_planilhas / main_polos e regista ficheiro(s) em data/output.

    Returns:
        { "ok": bool, "error": str | None, "extracao_ids": list[str], "filenames": list[str] }
    """
    numeros = [str(n).strip() for n in numeros if str(n).strip()]
    if not numeros:
        return {"ok": False, "error": "Nenhum número de processo.", "extracao_ids": [], "filenames": []}

    if tribunal_key not in TRIBUNAIS_MAP:
        return {"ok": False, "error": "Tribunal inválido.", "extracao_ids": [], "filenames": []}

    browser = (browser or "chrome").lower()
    job_mode = (job_mode or "").lower()
    if not modo_permitido(tribunal_key, browser, job_mode):
        return {
            "ok": False,
            "error": f"Modo '{job_mode}' não disponível para este tribunal com {browser}.",
            "extracao_ids": [],
            "filenames": [],
        }

    for n in numeros:
        det = identificar_tribunal_por_processo(n)
        if not processo_compativel_com_tribunal(det, tribunal_key):
            return {
                "ok": False,
                "error": f"Processo {n!r} pertence ao tribunal {det!r}, não a {tribunal_key!r}. "
                "Use só processos do tribunal escolhido.",
                "extracao_ids": [],
                "filenames": [],
            }

    helpers = obter_helpers(tribunal_key, browser)
    if not helpers:
        return {"ok": False, "error": "Combinação tribunal/navegador inválida.", "extracao_ids": [], "filenames": []}

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    tag = uuid.uuid4().hex[:10]
    temp_in = OUTPUT_DIR / f"_cli_in_{tag}.xlsx"
    pd.DataFrame({"numero_processo": numeros}).to_excel(temp_in, index=False, sheet_name="Sheet1")

    argv = [
        "--entrada",
        str(temp_in),
        "--saida-dir",
        str(OUTPUT_DIR),
        "--workers",
        str(max(1, min(int(workers or 3), 8))),
    ]

    nome_trib = TRIBUNAIS_MAP[tribunal_key].get("nome", tribunal_key).replace(" ", "_")
    extracao_ids: list[str] = []
    filenames: list[str] = []

    t0 = time.time()
    try:
        if job_mode == "movimentacoes":
            from scrapers.raspar_consulta_movimentacoes_core import main_movimentacoes

            code = main_movimentacoes(helpers, argv, progress_cb=progress_cb)
            if code != 0:
                return {"ok": False, "error": "CLI movimentações terminou com erro.", "extracao_ids": [], "filenames": []}
            gerado = OUTPUT_DIR / f"{temp_in.stem}_movimentação.xlsx"
            if not gerado.is_file():
                return {"ok": False, "error": "Ficheiro de movimentações não encontrado.", "extracao_ids": [], "filenames": []}
            final_name = f"{nome_trib}_{browser}_movimentacoes_{tag}.xlsx"
            final_path = OUTPUT_DIR / final_name
            _renomear_se_existir(gerado, final_path)
            ex = ExtracoesService.registrar_extracao(username, final_name, "movimentacoes_cli", len(numeros))
            extracao_ids.append(ex["id"])
            filenames.append(final_name)

        elif job_mode == "planilhas":
            from scrapers.raspar_consulta_planilhas_core import main_planilhas

            code = main_planilhas(helpers, argv, progress_cb=progress_cb)
            if code != 0:
                return {"ok": False, "error": "CLI planilhas terminou com erro.", "extracao_ids": [], "filenames": []}
            slug = _slug_do_helpers(helpers)

            def _recent(pattern: str) -> list[Path]:
                return [p for p in OUTPUT_DIR.glob(pattern) if p.is_file() and p.stat().st_mtime >= t0 - 0.5]

            rasp = _recent(f"resultados_raspados_{slug}_*.xlsx")
            trat = _recent(f"resultados_tratados_{slug}_*.xlsx")
            if not rasp or not trat:
                return {"ok": False, "error": "Planilhas raspada/tratada não encontradas.", "extracao_ids": [], "filenames": []}
            rasp_p = max(rasp, key=lambda p: p.stat().st_mtime)
            trat_p = max(trat, key=lambda p: p.stat().st_mtime)

            fn_r = f"{nome_trib}_{browser}_raspado_{tag}.xlsx"
            fn_t = f"{nome_trib}_{browser}_tratado_{tag}.xlsx"
            rp = OUTPUT_DIR / fn_r
            tp = OUTPUT_DIR / fn_t
            _renomear_se_existir(rasp_p, rp)
            _renomear_se_existir(trat_p, tp)
            ex1 = ExtracoesService.registrar_extracao(username, fn_r, "raspado_cli", len(numeros))
            ex2 = ExtracoesService.registrar_extracao(username, fn_t, "tratado_cli", len(numeros))
            extracao_ids.extend([ex1["id"], ex2["id"]])
            filenames.extend([fn_r, fn_t])

        elif job_mode == "polos":
            from scrapers.raspar_consulta_polos_core import main_polos

            code = main_polos(helpers, argv, progress_cb=progress_cb)
            if code != 0:
                return {"ok": False, "error": "CLI polos terminou com erro.", "extracao_ids": [], "filenames": []}
            gerado = OUTPUT_DIR / f"{temp_in.stem}_polos_advogados.xlsx"
            if not gerado.is_file():
                return {"ok": False, "error": "Ficheiro de polos não encontrado.", "extracao_ids": [], "filenames": []}
            final_name = f"{nome_trib}_{browser}_polos_{tag}.xlsx"
            final_path = OUTPUT_DIR / final_name
            _renomear_se_existir(gerado, final_path)
            ex = ExtracoesService.registrar_extracao(username, final_name, "polos_cli", len(numeros))
            extracao_ids.append(ex["id"])
            filenames.append(final_name)

        else:
            return {"ok": False, "error": "Modo desconhecido.", "extracao_ids": [], "filenames": []}

        return {"ok": True, "error": None, "extracao_ids": extracao_ids, "filenames": filenames}
    except Exception as e:
        logger.exception("CLI extração")
        return {"ok": False, "error": str(e), "extracao_ids": extracao_ids, "filenames": filenames}
    finally:
        try:
            if temp_in.is_file():
                temp_in.unlink(missing_ok=True)
        except OSError:
            pass
