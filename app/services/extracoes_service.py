import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd

class ExtracoesService:
    EXTRACOES_FILE = Path('data/extracoes.json')
    OUTPUT_DIR = Path('data/output')
    
    @staticmethod
    def _load_extracoes():
        if not ExtracoesService.EXTRACOES_FILE.exists():
            ExtracoesService.EXTRACOES_FILE.parent.mkdir(parents=True, exist_ok=True)
            ExtracoesService.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            with open(ExtracoesService.EXTRACOES_FILE, 'w', encoding='utf-8') as f:
                json.dump({'extracoes': []}, f, indent=2)
            return {'extracoes': []}
        
        with open(ExtracoesService.EXTRACOES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @staticmethod
    def _save_extracoes(data):
        with open(ExtracoesService.EXTRACOES_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    @staticmethod
    def registrar_extracao(username: str, filename: str, tipo: str, total_processos: int = 0):
        data = ExtracoesService._load_extracoes()
        
        extracao = {
            'id': str(datetime.now().timestamp()),
            'username': username,
            'filename': filename,
            'tipo': tipo,
            'data_criacao': datetime.now().isoformat(),
            'total_processos': total_processos,
            'filepath': str(ExtracoesService.OUTPUT_DIR / filename)
        }
        
        data['extracoes'].append(extracao)
        ExtracoesService._save_extracoes(data)
        return extracao
    
    @staticmethod
    def listar_extracoes(username: str, is_admin: bool = False) -> List[Dict[str, Any]]:
        data = ExtracoesService._load_extracoes()
        extracoes = data.get('extracoes', [])        
        if not is_admin:
            extracoes = [e for e in extracoes if e.get('username') == username]        
        extracoes.sort(key=lambda x: x.get('data_criacao', ''), reverse=True)
        
        return extracoes
    
    @staticmethod
    def limpar_extracoes_antigas(username: str, is_admin: bool = False):
        if is_admin:
            return
        
        data = ExtracoesService._load_extracoes()
        extracoes = data.get('extracoes', [])
        data_limite = datetime.now() - timedelta(days=30)
        
        extracoes_removidas = []
        extracoes_manter = []
        
        for extracao in extracoes:
            if extracao.get('username') != username:
                extracoes_manter.append(extracao)
                continue
            
            data_criacao = datetime.fromisoformat(extracao.get('data_criacao', ''))
            if data_criacao < data_limite:
                filepath = Path(extracao.get('filepath', ''))
                if filepath.exists():
                    try:
                        filepath.unlink()
                    except:
                        pass
                extracoes_removidas.append(extracao)
            else:
                extracoes_manter.append(extracao)
        
        data['extracoes'] = extracoes_manter
        ExtracoesService._save_extracoes(data)
        
        return len(extracoes_removidas)
    
    @staticmethod
    def deletar_extracao(extracao_id: str, username: str, is_admin: bool = False) -> bool:
        data = ExtracoesService._load_extracoes()
        extracoes = data.get('extracoes', [])
        
        for i, extracao in enumerate(extracoes):
            if extracao.get('id') == extracao_id:
                if not is_admin and extracao.get('username') != username:
                    return False
                
                filepath = Path(extracao.get('filepath', ''))
                if filepath.exists():
                    try:
                        filepath.unlink()
                    except:
                        pass                
                extracoes.pop(i)
                data['extracoes'] = extracoes
                ExtracoesService._save_extracoes(data)
                return True
        
        return False
    
    @staticmethod
    def obter_extracao(extracao_id: str) -> Dict[str, Any]:
        data = ExtracoesService._load_extracoes()
        for extracao in data.get('extracoes', []):
            if extracao.get('id') == extracao_id:
                return extracao
        return None
    
    @staticmethod
    def calcular_estatisticas(extracao: Dict[str, Any]) -> Dict[str, Any]:
        filepath = Path(extracao.get('filepath', ''))
        
        if not filepath.exists():
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
                except Exception as e:
                    print(f"Erro ao extrair tribunal do CNJ {cnj}: {e}")
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