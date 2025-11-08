import pandas as pd
import os
from typing import List, Dict, Any

class ExcelService:
    @staticmethod
    def ler_planilha(filepath: str) -> pd.DataFrame:
        if filepath.endswith(('.xlsx', '.xls')):
            return pd.read_excel(filepath)
        elif filepath.endswith('.csv'):
            return pd.read_csv(filepath)
        else:
            raise ValueError("Formato de arquivo não suportado")
    
    @staticmethod
    def exportar_resultados(resultados: List[Dict[str, Any]], output_path: str):
        dados_export = []
        for resultado in resultados:
            if resultado.get('status') == 'sucesso' and resultado.get('dados'):
                dados = resultado['dados']
                dados_processo = dados.get('dados_processo', {})
                dados_export.append({
                    'Numero Processo': resultado.get('numero_processo', ''),
                    'Tribunal': resultado.get('tribunal', ''),
                    'Data Distribuicao': dados_processo.get('data_distribuicao', ''),
                    'Classe Judicial': dados_processo.get('classe_judicial', ''),
                    'Assunto': dados_processo.get('assunto', ''),
                    'Jurisdicao': dados_processo.get('jurisdicao', ''),
                    'Orgao Julgador': dados_processo.get('orgao_julgador', ''),
                })
        
        df = pd.DataFrame(dados_export)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_excel(output_path, index=False)
        return output_path