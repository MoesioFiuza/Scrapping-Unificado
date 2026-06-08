"""CLI TJRJ (PJe) com Microsoft Edge — polo ativo, polo passivo e advogados.

Uso (raiz do repo):
  python scrapers/tjrj/raspar_tjrj_polos_edge.py --entrada lista.xlsx --workers 3

Driver: EDGE_DRIVER_PATH no .env ou msedgedriver no PATH.
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scrapers.raspar_consulta_polos_core import main_polos


def main(argv: list[str]) -> int:
    return main_polos("scrapers.tjrj.cli_helpers_edge", argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
