#!/usr/bin/env python3
"""Importa users.json e extracoes.json para a base de dados."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.main import app
from app.db.bootstrap import migrate_json_to_database
from app.extensions import db
from app.models import Extracao, User


def main() -> int:
    parser = argparse.ArgumentParser(description='Migra JSON legado para SQLAlchemy')
    parser.add_argument('--force-users', action='store_true', help='Reimportar users.json')
    parser.add_argument('--force-extracoes', action='store_true', help='Reimportar extracoes.json')
    args = parser.parse_args()

    with app.app_context():
        db.create_all()
        stats = migrate_json_to_database(
            force_users=args.force_users,
            force_extracoes=args.force_extracoes,
        )
        print(f"Utilizadores importados: {stats['users']}")
        print(f"Extrações importadas: {stats['extracoes']}")
        print(f"Total na BD: {User.query.count()} users, {Extracao.query.count()} extracoes")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
