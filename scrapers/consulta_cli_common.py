"""Utilitários partilhados pelos CLIs de consulta (planilhas + movimentações) por tribunal."""

from __future__ import annotations

import importlib
import re
from contextlib import contextmanager
from pathlib import Path

# e-SAJ (vários tribunais): resposta quando não há capa para o número/foro consultados.
MENSAGEM_ESAJ_SEM_INFORMACOES = (
    "Não existem informações disponíveis para os parâmetros informados"
)


def esaj_resposta_sem_informacoes(page_source: str) -> bool:
    return MENSAGEM_ESAJ_SEM_INFORMACOES in (page_source or "")


def resolver_diretorio_saida_cli(saida_dir: Path | None, entrada: Path | None) -> Path:
    """
    Se --saida-dir foi passado, usa-o.
    Senão, com ficheiro de --entrada válido, usa a pasta desse ficheiro.
    Caso contrário, data/output (relativo à raiz do projeto no caller).
    """
    if saida_dir is not None:
        return Path(saida_dir)
    if entrada is not None and entrada.is_file():
        return Path(entrada).resolve().parent
    return Path("data/output")


# Caracteres de controlo que o openpyxl rejeita (IllegalCharacterError).
_RE_CARACTERES_ILEGAIS_EXCEL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def sanitizar_texto_para_excel(val) -> str:
    """Remove control chars que o openpyxl não aceita em células .xlsx."""
    if val is None:
        return ""
    if isinstance(val, float):
        import math

        try:
            if math.isnan(val):
                return ""
        except (TypeError, ValueError):
            pass
    s = str(val)
    return _RE_CARACTERES_ILEGAIS_EXCEL.sub("", s)


def sanitizar_dataframe_para_excel(df):
    """Sanitiza colunas de texto para export openpyxl (evita IllegalCharacterError)."""
    import pandas as pd

    out = df.copy()
    for col in out.columns:
        if out[col].dtype == object or pd.api.types.is_string_dtype(out[col]):
            out[col] = out[col].map(
                lambda v: (
                    sanitizar_texto_para_excel(v)
                    if v is not None and not (isinstance(v, float) and pd.isna(v))
                    else ""
                )
            )
    return out


def normalizar_resultado(numero_processo: str, raw: dict, tribunal_key: str) -> dict:
    ok = raw.get("sucesso", False)
    return {
        "numero_processo": numero_processo,
        "tribunal": tribunal_key,
        "status": "sucesso" if ok else "erro",
        "dados": raw.get("dados") if ok else None,
        "erro": raw.get("erro") if not ok else None,
    }


def import_class(class_path: str) -> type:
    mod_name, sep, cls_name = class_path.partition(":")
    if not sep or not cls_name:
        raise ValueError(f"Caminho de classe inválido (use 'modulo:Classe'): {class_path!r}")
    mod = importlib.import_module(mod_name)
    return getattr(mod, cls_name)


@contextmanager
def escala_sleep_scraper_module(module_qualname: str, fator: float):
    mod = importlib.import_module(module_qualname)
    original = mod.time.sleep
    if fator >= 0.999:
        yield
        return

    fator = max(0.15, min(1.0, float(fator)))
    piso = 0.04

    def sleep_encurtado(segundos):
        if segundos is None or segundos <= 0:
            return original(segundos)
        return original(max(piso, float(segundos) * fator))

    mod.time.sleep = sleep_encurtado
    try:
        yield
    finally:
        mod.time.sleep = original


def mp_worker_consulta_chunk(payload: dict) -> list[tuple[int, dict]]:
    import sys

    root = payload["root"]
    if root not in sys.path:
        sys.path.insert(0, root)

    chunk = [(int(t[0]), str(t[1])) for t in payload["chunk"]]
    cfg = dict(payload["cfg"])
    fator_sleep = float(payload["fator_sleep"])
    wid = int(payload.get("worker_id", 0))
    somente_mov = bool(payload.get("somente_movimentacoes", False))
    somente_polos = bool(payload.get("somente_polos_adv", False))
    tribunal_key = str(payload["tribunal_key"])
    sleep_module = str(payload["sleep_module"])
    if somente_polos:
        class_path = str(payload["pol_class_path"])
    elif somente_mov:
        class_path = str(payload["mov_class_path"])
    else:
        class_path = str(payload["cli_class_path"])
    ScraperCls = import_class(class_path)

    out: list[tuple[int, dict]] = []
    with escala_sleep_scraper_module(sleep_module, fator_sleep):
        scraper = ScraperCls(cfg)
        try:
            scraper.setup_driver()
            total = len(chunk)
            for local_i, (idx, num) in enumerate(chunk, 1):
                print(f"[worker {wid} {local_i}/{total}] {num} ...")
                raw = scraper.raspar_processo(num)
                res = normalizar_resultado(num, raw, tribunal_key)
                out.append((idx, res))
                if res["status"] == "erro":
                    print(f"[worker {wid}]  Erro: {res.get('erro')}")
                else:
                    print(f"[worker {wid}]  OK")
        finally:
            scraper.close()
    return out
