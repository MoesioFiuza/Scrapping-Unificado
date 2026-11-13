#!/usr/bin/env python3
"""Apaga logs e falhas do Valença Suite com mais de 30 dias da publicação."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from wsgi import app
from app.services.analise_erros_service import DIAS_RETENCAO, purgar_antigos

with app.app_context():
    r = purgar_antigos(DIAS_RETENCAO)
    print(
        f"apagados {r['logs']} log(s) e {r['falhas']} falha(s) "
        f"com mais de {DIAS_RETENCAO} dias"
    )
