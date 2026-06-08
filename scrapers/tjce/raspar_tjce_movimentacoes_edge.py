"""CLI TJCE (PJe) com Microsoft Edge — só movimentações.

Uso (raiz do repo):
  python scrapers/tjce/raspar_tjce_movimentacoes_edge.py --entrada lista.xlsx --workers 3

Driver: EDGE_DRIVER_PATH no .env ou msedgedriver em %%USERPROFILE%%\\Desktop\\ACESSO LOGADO\\
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scrapers.raspar_consulta_movimentacoes_core import main_movimentacoes


def main(argv: list[str]) -> int:
    return main_movimentacoes("scrapers.tjce.cli_helpers_edge", argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
