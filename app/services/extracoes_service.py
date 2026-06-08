from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd

from app.extensions import db
from app.models import Extracao, User


class ExtracoesService:
    _PROJECT_ROOT = Path(__file__).resolve().parents[2]
    OUTPUT_DIR = _PROJECT_ROOT / "data" / "output"
    INPUT_DIR = _PROJECT_ROOT / "data" / "input"

    @staticmethod
    def resolver_filepath_extracao(extracao: Dict[str, Any]) -> Path:
        raw = (extracao.get("filepath") or "").strip()
        if not raw:
            return Path("")
        p = Path(raw)
        if p.is_absolute():
            if p.is_file():
                return p
            return ExtracoesService.OUTPUT_DIR / p.name
        cand = (ExtracoesService._PROJECT_ROOT / p).resolve()
        if cand.is_file():
            return cand
        alt = (ExtracoesService.OUTPUT_DIR / p.name).resolve()
        return alt if alt.is_file() else cand

    @staticmethod
    def _get_user_id(username: str) -> int | None:
        user = User.query.filter_by(username=username.strip().lower()).first()
        return user.id if user else None

    @staticmethod
    def registrar_extracao(username: str, filename: str, tipo: str, total_processos: int = 0):
        user_id = ExtracoesService._get_user_id(username)
        if user_id is None:
            raise ValueError(f"Utilizador não encontrado: {username}")

        rel_fp = (Path("data") / "output" / filename).as_posix()
        extracao = Extracao(
            id=str(datetime.now().timestamp()),
            user_id=user_id,
            filename=filename,
            filepath=rel_fp,
            tipo=tipo,
            total_processos=total_processos,
            data_criacao=datetime.utcnow(),
        )
        db.session.add(extracao)
        db.session.commit()
        return extracao.to_dict()

    @staticmethod
    def listar_extracoes(username: str, is_admin: bool = False) -> List[Dict[str, Any]]:
        query = Extracao.query.join(User)
        if not is_admin:
            query = query.filter(User.username == username.strip().lower())
        rows = query.order_by(Extracao.data_criacao.desc()).all()
        return [e.to_dict() for e in rows]

    @staticmethod
    def calcular_resumo_dashboard(username: str, is_admin: bool = False) -> Dict[str, Any]:
        extracoes = ExtracoesService.listar_extracoes(username, is_admin)
        total_ficheiros = len(extracoes)
        total_processos = sum(int(e.get('total_processos') or 0) for e in extracoes)

        cutoff = datetime.utcnow() - timedelta(days=30)
        extracoes_30d = 0
        for e in extracoes:
            raw = e.get('data_criacao') or ''
            try:
                if datetime.fromisoformat(raw.replace('Z', '+00:00').split('+')[0]) >= cutoff:
                    extracoes_30d += 1
            except (ValueError, TypeError):
                pass

        return {
            'total_ficheiros': total_ficheiros,
            'total_processos_extraidos': total_processos,
            'media_processos_por_ficheiro': round(total_processos / total_ficheiros, 1) if total_ficheiros else 0,
            'extracoes_ultimos_30_dias': extracoes_30d,
            'extracoes_cli': sum(1 for e in extracoes if '_cli' in (e.get('tipo') or '')),
            'extracoes_app': sum(1 for e in extracoes if '_cli' not in (e.get('tipo') or '')),
        }

    @staticmethod
    def limpar_extracoes_antigas(username: str, is_admin: bool = False):
        if is_admin:
            return 0

        data_limite = datetime.utcnow() - timedelta(days=30)
        username = username.strip().lower()
        user = User.query.filter_by(username=username).first()
        if not user:
            return 0

        antigas = (
            Extracao.query.filter(
                Extracao.user_id == user.id,
                Extracao.data_criacao < data_limite,
            ).all()
        )

        for extracao in antigas:
            filepath = ExtracoesService.resolver_filepath_extracao(extracao.to_dict())
            if filepath.is_file():
                try:
                    filepath.unlink()
                except OSError:
                    pass
            db.session.delete(extracao)

        db.session.commit()
        return len(antigas)

    @staticmethod
    def deletar_extracao(extracao_id: str, username: str, is_admin: bool = False) -> bool:
        extracao = Extracao.query.get(extracao_id)
        if not extracao:
            return False

        if not is_admin and extracao.user.username != username.strip().lower():
            return False

        filepath = ExtracoesService.resolver_filepath_extracao(extracao.to_dict())
        if filepath.is_file():
            try:
                filepath.unlink()
            except OSError:
                pass

        db.session.delete(extracao)
        db.session.commit()
        return True

    @staticmethod
    def obter_extracao(extracao_id: str) -> Dict[str, Any] | None:
        extracao = Extracao.query.get(extracao_id)
        return extracao.to_dict() if extracao else None

    @staticmethod
    def calcular_estatisticas(extracao: Dict[str, Any]) -> Dict[str, Any]:
        filepath = ExtracoesService.resolver_filepath_extracao(extracao)

        if not filepath.is_file():
            return {
                'total_processos': extracao.get('total_processos', 0),
                'tribunais': {}
            }

        try:
            df = pd.read_excel(str(filepath))

            tribunais_count = {}
            total = 0

            def extrair_tribunal_cnj(cnj):
                if pd.isna(cnj) or not cnj:
                    return None
                try:
                    cnj_str = str(cnj).strip()
                    partes = cnj_str.split('.')
                    if len(partes) >= 4:
                        tribunal_code = partes[3] if len(partes) > 3 else None
                        if tribunal_code and tribunal_code.strip():
                            return tribunal_code.strip()
                except Exception:
                    pass
                return None

            tribunal_col = None
            tribunal_values = None

            for col_name in ['Tribunal', 'tribunal', 'sistemaExterno', 'Sistema Externo', 'sistema_externo']:
                if col_name in df.columns:
                    tribunal_col = col_name
                    tribunal_values = df[col_name]
                    break

            if tribunal_col is None:
                cnj_col = None
                for col_name in ['cnj', 'CNJ', 'Numero Processo', 'numero_processo', 'Numero Processo Anterior',
                                'numeroProcessoAnterior', 'NumeroProcessoAnterior', 'processo', 'Processo']:
                    if col_name in df.columns:
                        cnj_col = col_name
                        break

                if cnj_col is None:
                    for col in df.columns:
                        col_lower = str(col).lower()
                        if 'processo' in col_lower or 'cnj' in col_lower or ('numero' in col_lower and 'processo' in col_lower):
                            sample = df[col].dropna().head(10)
                            if len(sample) > 0:
                                cnj_count = sum(1 for val in sample if '.' in str(val) and len(str(val).split('.')) >= 4)
                                if cnj_count >= len(sample) * 0.5:
                                    cnj_col = col
                                    break

                if cnj_col:
                    df['_tribunal_extracted'] = df[cnj_col].apply(extrair_tribunal_cnj)
                    tribunal_values = df['_tribunal_extracted'].dropna()
                    if len(tribunal_values) > 0:
                        tribunal_col = '_tribunal_extracted'

            if tribunal_values is not None and len(tribunal_values) > 0:
                tribunais_series = tribunal_values.value_counts()
                for tribunal, count in tribunais_series.items():
                    if pd.notna(tribunal) and str(tribunal).strip() and str(tribunal).strip() != 'None':
                        tribunal_str = str(tribunal).strip()
                        tribunais_count[tribunal_str] = tribunais_count.get(tribunal_str, 0) + int(count)
                        total += int(count)

            tribunais_percent = {}
            for tribunal, count in tribunais_count.items():
                if total > 0:
                    percent = (count / total) * 100
                    tribunais_percent[tribunal] = {
                        'count': count,
                        'percent': round(percent, 1)
                    }

            total_tribunais = len(tribunais_count)
            maior_tribunal = max(tribunais_count.items(), key=lambda x: x[1]) if tribunais_count else None
            menor_tribunal = min(tribunais_count.items(), key=lambda x: x[1]) if tribunais_count else None

            return {
                'total_processos': total if total > 0 else extracao.get('total_processos', 0),
                'tribunais': tribunais_percent,
                'total_tribunais': total_tribunais,
                'maior_tribunal': {
                    'codigo': maior_tribunal[0] if maior_tribunal else None,
                    'count': maior_tribunal[1] if maior_tribunal else 0
                } if maior_tribunal else None,
                'menor_tribunal': {
                    'codigo': menor_tribunal[0] if menor_tribunal else None,
                    'count': menor_tribunal[1] if menor_tribunal else 0
                } if menor_tribunal else None
            }
        except Exception as e:
            print(f"Erro ao calcular estatísticas: {e}")
            return {
                'total_processos': extracao.get('total_processos', 0),
                'tribunais': {}
            }
