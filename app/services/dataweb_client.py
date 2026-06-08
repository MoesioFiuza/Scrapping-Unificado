from __future__ import annotations

import io
import logging
import time
from typing import Any

import pandas as pd
import requests

from config.settings import (
    DATAWEB_BASE_URL,
    DATAWEB_MAX_CNJS,
    DATAWEB_MAX_PARALLEL_LOTES,
    DATAWEB_TIMEOUT_SECONDS,
)

logger = logging.getLogger(__name__)


class DataWebError(Exception):
    def __init__(self, message: str, *, status: int | None = None, title: str | None = None):
        super().__init__(message)
        self.status = status
        self.title = title


class DataWebClient:
    """Client HTTP para o microserviço DataWeb (CNJs → Excel via DataJud)."""

    def __init__(
        self,
        base_url: str | None = None,
        timeout_seconds: int | None = None,
        max_cnjs_por_requisicao: int | None = None,
    ):
        self.base_url = (base_url or DATAWEB_BASE_URL).rstrip("/")
        self.timeout = timeout_seconds if timeout_seconds is not None else DATAWEB_TIMEOUT_SECONDS
        self.max_cnjs = max_cnjs_por_requisicao or DATAWEB_MAX_CNJS
        self._session = requests.Session()
        self._session.headers.update({"Content-Type": "application/json", "Accept": "*/*"})

    def is_healthy(self) -> bool:
        try:
            resp = self._session.get(f"{self.base_url}/health", timeout=15)
            if resp.status_code != 200:
                return False
            data = resp.json()
            return data.get("status") == "healthy"
        except Exception as exc:
            logger.warning("DataWeb health check falhou: %s", exc)
            return False

    @staticmethod
    def _normalizar_cnjs(cnjs: list[str]) -> list[str]:
        out: list[str] = []
        seen: set[str] = set()
        for raw in cnjs:
            if raw is None:
                continue
            c = str(raw).strip()
            if not c or c.lower() in ("nan", "none"):
                continue
            if c not in seen:
                seen.add(c)
                out.append(c)
        return out

    def processar_cnjs(self, cnjs: list[str]) -> bytes:
        cnjs = self._normalizar_cnjs(cnjs)
        if not cnjs:
            raise DataWebError(
                "Informe ao menos um CNJ no campo 'cnjs'.",
                status=400,
                title="Requisição inválida",
            )

        lotes = [cnjs[i : i + self.max_cnjs] for i in range(0, len(cnjs), self.max_cnjs)]
        logger.info("DataWeb: %s CNJ(s) em %s lote(s)", len(cnjs), len(lotes))

        resultados: list[bytes] = []
        # Processamento sequencial para respeitar limite de concorrência recomendado
        for idx, lote in enumerate(lotes, 1):
            logger.info("DataWeb lote %s/%s (%s CNJs)", idx, len(lotes), len(lote))
            resultados.append(self._processar_lote_com_retry(lote))

        if len(resultados) == 1:
            return resultados[0]
        return _mesclar_excels(resultados)

    def _processar_lote_com_retry(self, cnjs: list[str], max_retries: int = 1) -> bytes:
        last_err: DataWebError | None = None
        for attempt in range(max_retries + 1):
            try:
                return self._processar_lote(cnjs)
            except DataWebError as exc:
                last_err = exc
                if exc.status in (422, 500) and attempt < max_retries:
                    logger.warning("DataWeb retry %s após erro %s", attempt + 1, exc.status)
                    time.sleep(2)
                    continue
                raise
        raise last_err or DataWebError("Erro desconhecido ao contactar DataWeb.")

    def _processar_lote(self, cnjs: list[str]) -> bytes:
        url = f"{self.base_url}/api/v1/processar"
        try:
            resp = self._session.post(
                url,
                json={"cnjs": cnjs},
                timeout=self.timeout,
            )
        except requests.Timeout as exc:
            raise DataWebError(
                f"Timeout após {self.timeout}s aguardando o DataWeb. Tente menos CNJs ou tente novamente.",
                status=504,
                title="Timeout",
            ) from exc
        except requests.RequestException as exc:
            raise DataWebError(f"Falha de rede ao contactar DataWeb: {exc}", status=503) from exc

        if resp.status_code == 200:
            content_type = (resp.headers.get("Content-Type") or "").lower()
            if (
                "spreadsheet" in content_type
                or "excel" in content_type
                or resp.content[:2] == b"PK"
            ):
                return resp.content
            raise DataWebError(
                "Resposta 200 inesperada (não é Excel).",
                status=502,
                title="Resposta inválida",
            )

        detail, title = _parse_problem_details(resp)
        raise DataWebError(detail, status=resp.status_code, title=title)


def _parse_problem_details(resp: requests.Response) -> tuple[str, str | None]:
    title: str | None = None
    detail = f"Erro HTTP {resp.status_code} do DataWeb."
    try:
        if "json" in (resp.headers.get("Content-Type") or "").lower():
            data: dict[str, Any] = resp.json()
            title = data.get("title")
            detail = data.get("detail") or data.get("title") or detail
    except Exception:
        if resp.text:
            detail = resp.text[:500]
    return detail, title


def _mesclar_excels(byte_list: list[bytes]) -> bytes:
    """Concatena abas homónimas de vários Excels num único ficheiro."""
    sheet_frames: dict[str, list[pd.DataFrame]] = {}
    for data in byte_list:
        xl = pd.ExcelFile(io.BytesIO(data))
        for sheet in xl.sheet_names:
            df = pd.read_excel(xl, sheet_name=sheet)
            sheet_frames.setdefault(sheet, []).append(df)

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        for sheet, frames in sheet_frames.items():
            merged = pd.concat(frames, ignore_index=True)
            safe_name = sheet[:31]
            merged.to_excel(writer, sheet_name=safe_name, index=False)
    return buf.getvalue()


_default_client: DataWebClient | None = None


def get_dataweb_client() -> DataWebClient:
    global _default_client
    if _default_client is None:
        _default_client = DataWebClient()
    return _default_client
