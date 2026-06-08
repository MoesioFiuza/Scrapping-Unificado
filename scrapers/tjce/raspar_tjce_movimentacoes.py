#!/usr/bin/env python3
"""
CLI TJCE: consulta pública e exporta **somente movimentações** (sem polos, documentos, etc.).

Na raspagem o browser só extrai a tabela de movimentos após abrir o detalhe — mais leve que raspar_tjce_planilhas.

Uso (raiz do repo):
  python scrapers/tjce/raspar_tjce_movimentacoes.py --entrada lista.xlsx --coluna 0
  python scrapers/tjce/raspar_tjce_movimentacoes.py --entrada lista.xlsx --workers 3

Saída: um único .xlsx em data/output — abas Movimentacoes + Resumo (ver raspar_consulta_movimentacoes_core).
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scrapers.raspar_consulta_movimentacoes_core import main_movimentacoes


def main(argv: list[str]) -> int:
    return main_movimentacoes("scrapers.tjce.cli_helpers", argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
