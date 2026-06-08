from typing import Dict, Any, List
import re

class TransformadorESAJ:

    @staticmethod
    def limpar_texto(texto: str) -> str:
        if not texto:
            return ""
        texto = re.sub(r'\s+', ' ', str(texto))
        return texto.strip()
    
    @staticmethod
    def normalizar_resultado(resultado: Dict[str, Any]) -> Dict[str, Any]:

        if resultado.get('status') != 'sucesso' or not resultado.get('dados'):
            return resultado
        
        dados = resultado['dados']
        dados_processo = dados.get('dados_processo', {})
        
        dados_processo_normalizado = {
            'classe_judicial': TransformadorESAJ.limpar_texto(
                dados_processo.get('classe_judicial', '')
            ),
            'assunto': TransformadorESAJ.limpar_texto(
                dados_processo.get('assunto', '')
            ),
            'jurisdicao': TransformadorESAJ.limpar_texto(
                dados_processo.get('jurisdicao', '')
            ),
            'orgao_julgador': TransformadorESAJ.limpar_texto(
                dados_processo.get('orgao_julgador', '')
            ),
            'data_distribuicao': TransformadorESAJ.limpar_texto(
                dados_processo.get('data_distribuicao', '')
            ),
            'situacao': TransformadorESAJ.limpar_texto(
                dados_processo.get('situacao', '')
            ),
            'juiz': TransformadorESAJ.limpar_texto(
                dados_processo.get('juiz', '')
            ),
            'valor_acao': TransformadorESAJ.limpar_texto(
                dados_processo.get('valor_acao', '') or dados_processo.get('valor_causa', '')
            ),
            'area': TransformadorESAJ.limpar_texto(
                dados_processo.get('area', 'Cível')
            ),
            'controle': TransformadorESAJ.limpar_texto(
                dados_processo.get('controle', '')
            ),
            'outros_numeros': TransformadorESAJ.limpar_texto(
                dados_processo.get('outros_numeros', '')
            ),
            'outros_assuntos': TransformadorESAJ.limpar_texto(
                dados_processo.get('outros_assuntos', '')
            )
        }
        
        polo_ativo_normalizado = []
        for parte in dados.get('polo_ativo', []):
            parte_normalizada = {
                'nome': TransformadorESAJ.limpar_texto(
                    parte.get('nome', '') or parte.get('nome_completo', '')
                ),
                'nome_completo': TransformadorESAJ.limpar_texto(
                    parte.get('nome_completo', '') or parte.get('nome', '')
                ),
                'tipo': TransformadorESAJ.limpar_texto(
                    parte.get('tipo', '')
                ),
                'situacao': TransformadorESAJ.limpar_texto(
                    parte.get('situacao', 'Ativo')
                ),
                'cpf': TransformadorESAJ.limpar_texto(
                    parte.get('cpf', '')
                ),
                'cnpj': TransformadorESAJ.limpar_texto(
                    parte.get('cnpj', '')
                ),
                'oab': TransformadorESAJ.limpar_texto(
                    parte.get('oab', '')
                ),
                'advogado': TransformadorESAJ.limpar_texto(
                    parte.get('advogado', '')
                )
            }
            if parte_normalizada['nome']:
                polo_ativo_normalizado.append(parte_normalizada)
        
        polo_passivo_normalizado = []
        for parte in dados.get('polo_passivo', []):
            parte_normalizada = {
                'nome': TransformadorESAJ.limpar_texto(
                    parte.get('nome', '') or parte.get('nome_completo', '')
                ),
                'nome_completo': TransformadorESAJ.limpar_texto(
                    parte.get('nome_completo', '') or parte.get('nome', '')
                ),
                'tipo': TransformadorESAJ.limpar_texto(
                    parte.get('tipo', '')
                ),
                'situacao': TransformadorESAJ.limpar_texto(
                    parte.get('situacao', 'Ativo')
                ),
                'cpf': TransformadorESAJ.limpar_texto(
                    parte.get('cpf', '')
                ),
                'cnpj': TransformadorESAJ.limpar_texto(
                    parte.get('cnpj', '')
                ),
                'oab': TransformadorESAJ.limpar_texto(
                    parte.get('oab', '')
                ),
                'advogado': TransformadorESAJ.limpar_texto(
                    parte.get('advogado', '')
                )
            }
            if parte_normalizada['nome']:
                polo_passivo_normalizado.append(parte_normalizada)
        
        movimentacoes_normalizadas = []
        for mov in dados.get('movimentacoes', []):
            movimento_texto = mov.get('movimento', '') or mov.get('descricao', '')
            data_mov = mov.get('data', '')            
            if not data_mov and movimento_texto:
                data_match = re.search(r'(\d{2}/\d{2}/\d{4})', movimento_texto)
                if data_match:
                    data_mov = data_match.group(1)
                    movimento_texto = re.sub(r'^\d{2}/\d{2}/\d{4}\s*[-–]\s*', '', movimento_texto).strip()
            
            movimentacao_normalizada = {
                'data': TransformadorESAJ.limpar_texto(data_mov),
                'movimento': TransformadorESAJ.limpar_texto(movimento_texto),
                'descricao': TransformadorESAJ.limpar_texto(movimento_texto),  # Mesmo valor
                'hora': TransformadorESAJ.limpar_texto(mov.get('hora', ''))
            }            
            if movimentacao_normalizada['movimento']:
                movimentacoes_normalizadas.append(movimentacao_normalizada)
        
        resultado_normalizado = resultado.copy()
        resultado_normalizado['dados'] = {
            'dados_processo': dados_processo_normalizado,
            'polo_ativo': polo_ativo_normalizado,
            'polo_passivo': polo_passivo_normalizado,
            'movimentacoes': movimentacoes_normalizadas,
            'documentos': dados.get('documentos', [])  # Manter documentos como estão
        }
        
        return resultado_normalizado
    
    @staticmethod
    def normalizar_lote(resultados: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        resultados_normalizados = []
        for resultado in resultados:
            if resultado.get('tribunal') in ('8.26', '8.02', '8.06_esaj'):
                resultado_normalizado = TransformadorESAJ.normalizar_resultado(resultado)
                resultados_normalizados.append(resultado_normalizado)
            else:
                resultados_normalizados.append(resultado)
        
        return resultados_normalizados