"""CLI TJCE (PJe) Chrome — partes por polo, advogados por polo.

Uso (raiz do repo):
  python scrapers/tjce/raspar_tjce_polos.py --entrada lista.xlsx --workers 3
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scrapers.raspar_consulta_polos_core import main_polos


def main(argv: list[str]) -> int:
    return main_polos("scrapers.tjce.cli_helpers", argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
