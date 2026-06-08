from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scrapers.raspar_consulta_movimentacoes_core import main_movimentacoes


def main(argv: list[str]) -> int:
    return main_movimentacoes("scrapers.tjrn.cli_helpers_edge", argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
