from typing import Dict, Any, List
from datetime import datetime
import re

class TransformadorDados:
    """Transforma dados extraídos do scraping para formato padronizado"""
    
    # Mapeamento de tribunais para estados
    TRIBUNAL_ESTADO_MAP = {
        "8.19": "RJ",  # TJRJ
        "8.06": "CE",  # TJCE
        "8.13": "MG",  # TJMG
        "8.17": "PE",  # TJPE
        "8.26": "SP",  # TJSP
        "8.10": "MA",  # TJMA
        "8.07": "DF",  # TJDFT
        "8.20": "RN",  # TJRN
    }
    
    # Mapeamento de tribunais para nomes
    TRIBUNAL_NOME_MAP = {
        "8.19": "TJRJ",
        "8.06": "TJCE",
        "8.13": "TJMG",
        "8.17": "TJPE",
        "8.26": "TJSP",
        "8.10": "TJMA",
        "8.07": "TJDFT",
        "8.20": "TJRN",
    }
    
    @staticmethod
    def limpar_texto(texto: str) -> str:
        """Remove espaços extras e quebras de linha"""
        if not texto:
            return ""
        # Remove quebras de linha e espaços múltiplos
        texto = re.sub(r'\s+', ' ', str(texto))
        return texto.strip()
    
    @staticmethod
    def extrair_numero_cnj(numero_processo: str) -> str:
        """Extrai número CNJ do processo"""
        return TransformadorDados.limpar_texto(numero_processo) if numero_processo else ""
    
    @staticmethod
    def extrair_tipo_rito(classe_judicial: str) -> str:
        """Extrai tipo de rito da classe judicial"""
        if not classe_judicial:
            return ""
        
        classe_lower = classe_judicial.lower()
        if "juizado especial" in classe_lower or "sumar" in classe_lower or "sumaríssimo" in classe_lower:
            return "Sumaríssimo"
        elif "ordinário" in classe_lower:
            return "Ordinário"
        elif "especial" in classe_lower:
            return "Especial"
        return "Não informado"
    
    @staticmethod
    def obter_estado_por_tribunal(tribunal_key: str) -> str:
        """Obtém o estado baseado no código do tribunal"""
        return TransformadorDados.TRIBUNAL_ESTADO_MAP.get(tribunal_key, "")
    
    @staticmethod
    def obter_sistema_externo(tribunal_key: str) -> str:
        """Gera o sistema externo baseado no tribunal"""
        nome_tribunal = TransformadorDados.TRIBUNAL_NOME_MAP.get(tribunal_key, "")
        estado = TransformadorDados.obter_estado_por_tribunal(tribunal_key)
        if nome_tribunal and estado:
            return f"TJ-{estado}-PJE-1° Grau"
        return ""
    
    @staticmethod
    def extrair_unidade_especialidade(classe_judicial: str, orgao_julgador: str = "") -> tuple:
        """Extrai unidade e especialidade da classe judicial ou órgão julgador"""
        unidade = ""
        especialidade = "Cível"  # Sempre padrão Cível
        
        if classe_judicial:
            classe_lower = classe_judicial.lower()
            if "juizado especial" in classe_lower:
                unidade = "Juizado Especial"
            elif "vara" in classe_lower:
                unidade = "Vara"
            elif "juizado" in classe_lower:
                unidade = "Juizado"
        
        # Se não encontrou unidade na classe, tentar no órgão julgador
        if not unidade and orgao_julgador:
            orgao_lower = orgao_julgador.lower()
            if "juizado" in orgao_lower:
                unidade = "Juizado Especial"
            elif "vara" in orgao_lower:
                unidade = "Vara"
            elif "núcleo" in orgao_lower or "nucleo" in orgao_lower:
                unidade = "Núcleo"
        
        # Especialidade sempre será Cível (padrão)
        return (unidade, especialidade)
    
    @staticmethod
    def extrair_numero_unidade(orgao_julgador: str) -> str:
        """Extrai o número da unidade do órgão julgador"""
        if not orgao_julgador:
            return "0"
        
        orgao_limpo = TransformadorDados.limpar_texto(orgao_julgador)
        
        # Procurar por padrões como "1º", "1ª", "2º", "2ª", etc.
        # Exemplos: "1º Juizado", "2ª Vara", "1ª Unidade"
        match = re.search(r'(\d+)[ºª]', orgao_limpo)
        if match:
            return match.group(1)
        
        # Se não encontrou número, retornar "0"
        return "0"
    
    @staticmethod
    def extrair_comarca_estado(jurisdicao: str, orgao_julgador: str = "") -> tuple:
        """Extrai comarca e estado da jurisdição ou órgão julgador"""
        comarca = ""
        jurisdicao_limpa = TransformadorDados.limpar_texto(jurisdicao) if jurisdicao else ""
        
        # PRIORIDADE 1: Tentar extrair do órgão julgador primeiro (mais confiável)
        if orgao_julgador:
            orgao_limpo = TransformadorDados.limpar_texto(orgao_julgador)
            # Tentar extrair comarca do órgão (ex: "2ª Vara Cível da Comarca de Barbalha")
            # Captura tudo após "Comarca de" até o final da string
            match_orgao = re.search(r'comarca de (.+)', orgao_limpo, re.IGNORECASE)
            if match_orgao:
                comarca = match_orgao.group(1).strip()
                # Remover ponto final se houver
                comarca = comarca.rstrip('.')
        
        # PRIORIDADE 2: Se não encontrou no órgão, tentar na jurisdição
        if not comarca and jurisdicao_limpa:
            # Tentar diferentes formatos
            match = re.search(r'Comarca de (.+)', jurisdicao_limpa, re.IGNORECASE)
            if match:
                comarca = match.group(1).strip()
            else:
                # Se não tem "Comarca de", pode ser que a própria jurisdicao seja a comarca
                if "comarca" in jurisdicao_limpa.lower():
                    # Tentar extrair após "comarca"
                    match2 = re.search(r'comarca[:\s]+(.+)', jurisdicao_limpa, re.IGNORECASE)
                    if match2:
                        comarca = match2.group(1).strip()
                else:
                    # Se não tem "comarca" no texto, usar o texto completo
                    comarca = jurisdicao_limpa
        
        # PRIORIDADE 3: Se ainda não encontrou, tentar extrair do órgão (casos especiais)
        if not comarca and orgao_julgador:
            orgao_limpo = TransformadorDados.limpar_texto(orgao_julgador)
            if "núcleo" in orgao_limpo.lower() or "nucleo" in orgao_limpo.lower():
                # Se for núcleo, extrair o nome completo do núcleo
                match_nucleo = re.search(r'(núcleo[:\s]+[^,\.]+)', orgao_limpo, re.IGNORECASE)
                if match_nucleo:
                    comarca = match_nucleo.group(1).strip()
                else:
                    # Tentar pegar tudo após "Núcleo"
                    match_nucleo2 = re.search(r'núcleo[:\s]*(.+)', orgao_limpo, re.IGNORECASE)
                    if match_nucleo2:
                        comarca = f"Núcleo {match_nucleo2.group(1).strip()}"
                    else:
                        comarca = orgao_limpo
            else:
                # Se não tem "comarca" nem "núcleo", usar a jurisdição ou órgão como comarca
                if jurisdicao_limpa:
                    comarca = jurisdicao_limpa
                else:
                    comarca = orgao_limpo
        
        return (comarca, "")
    
    @staticmethod
    def extrair_tipo_parte(participante: Dict[str, Any]) -> str:
        """Extrai tipo da parte (Autor, Réu, etc)"""
        nome = participante.get('nome', '').upper()
        if 'AUTOR' in nome or 'AUTORA' in nome:
            return "Autor"
        elif 'RÉU' in nome or 'REU' in nome:
            return "Réu"
        elif 'ADVOGADO' in nome:
            return "Advogado"
        return ""
    
    @staticmethod
    def processar_movimentacoes(movimentacoes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Processa movimentações para formato padronizado"""
        eventos = []
        for mov in movimentacoes:
            movimento = mov.get('movimento', '')
            if movimento:
                # Extrair data e hora
                data_match = re.search(r'(\d{2}/\d{2}/\d{4})\s+(\d{2}:\d{2}:\d{2})', movimento)
                data_evento = data_match.group(1) if data_match else ""
                hora_evento = data_match.group(2) if data_match else ""
                
                # Extrair tipo de evento (pode ser melhorado com mapeamento)
                tipo_evento = "1035"  # Padrão, pode ser mapeado
                
                eventos.append({
                    'dataEvento': data_evento,
                    'tipoEvento': tipo_evento,
                    'descricaoEvento': movimento,
                    'complementoEvento': mov.get('documento', ''),
                    'observacaoEvento': '',
                    'solicitanteEvento': '',
                    'responsavelEvento': ''
                })
        return eventos
    
    @staticmethod
    def transformar_dados(resultado: Dict[str, Any]) -> Dict[str, Any]:
        """Transforma dados do scraping para formato completo"""
        if resultado.get('status') != 'sucesso' or not resultado.get('dados'):
            return {}
        
        dados = resultado['dados']
        dados_processo = dados.get('dados_processo', {})
        polo_ativo = dados.get('polo_ativo', [])
        polo_passivo = dados.get('polo_passivo', [])
        movimentacoes = dados.get('movimentacoes', [])
        documentos = dados.get('documentos', [])
        
        # Debug: verificar o que está chegando
        print(f"DEBUG - Polo ativo recebido: {len(polo_ativo)} itens")
        print(f"DEBUG - Polo passivo recebido: {len(polo_passivo)} itens")
        if polo_ativo:
            print(f"DEBUG - Primeiro polo ativo: {polo_ativo[0]}")
        if polo_passivo:
            print(f"DEBUG - Primeiro polo passivo: {polo_passivo[0]}")
        
        numero_processo = resultado.get('numero_processo', '')
        tribunal_key = resultado.get('tribunal', '')
        classe_judicial = dados_processo.get('classe_judicial', '')
        assunto = dados_processo.get('assunto', '')
        jurisdicao = dados_processo.get('jurisdicao', '')
        orgao_julgador = dados_processo.get('orgao_julgador', '')
        data_distribuicao = dados_processo.get('data_distribuicao', '')
        
        # Limpar todos os textos
        classe_judicial = TransformadorDados.limpar_texto(classe_judicial)
        assunto = TransformadorDados.limpar_texto(assunto)
        jurisdicao = TransformadorDados.limpar_texto(jurisdicao)
        orgao_julgador = TransformadorDados.limpar_texto(orgao_julgador)
        data_distribuicao = TransformadorDados.limpar_texto(data_distribuicao)
        
        # Extrair informações
        unidade, especialidade = TransformadorDados.extrair_unidade_especialidade(classe_judicial, orgao_julgador)
        comarca, _ = TransformadorDados.extrair_comarca_estado(jurisdicao, orgao_julgador)
        tipo_rito = TransformadorDados.extrair_tipo_rito(classe_judicial)
        numero_unidade = TransformadorDados.extrair_numero_unidade(orgao_julgador)
        
        # Obter estado do tribunal (sempre funciona para todos os tribunais mapeados)
        estado = TransformadorDados.obter_estado_por_tribunal(tribunal_key)
        sistema_externo = TransformadorDados.obter_sistema_externo(tribunal_key)
        
        # Debug
        print(f"DEBUG - Tribunal: {tribunal_key}, Estado: {estado}, Sistema: {sistema_externo}")
        print(f"DEBUG - Comarca: {comarca}, Unidade: {unidade}, NumeroUnidade: {numero_unidade}, Especialidade: {especialidade}")
        
        # Processar polo ativo - usar todos os nomes da raspagem, filtrando apenas autores
        partes_ativas_nomes = []
        for parte in polo_ativo:
            # Tentar pegar nome de diferentes campos
            nome = TransformadorDados.limpar_texto(parte.get('nome', '') or parte.get('nome_completo', ''))
            nome_completo = TransformadorDados.limpar_texto(parte.get('nome_completo', ''))
            tipo = parte.get('tipo', '')
            
            if not nome:
                continue
            
            # Verificar se é advogado
            tipo_upper = tipo.upper() if tipo else ''
            nome_completo_upper = nome_completo.upper() if nome_completo else ''
            nome_upper = nome.upper()
            
            is_advogado = (
                'ADVOGADO' in tipo_upper or
                'ADVOGADO' in nome_completo_upper or
                'ADVOGADO' in nome_upper or
                'OAB' in nome_upper
            )
            
            # Se não for advogado, incluir (assume que é autor por estar no polo ativo)
            if not is_advogado:
                partes_ativas_nomes.append(nome)
        
        # Processar polo passivo - usar todos os nomes da raspagem
        partes_passivas_nomes = []
        for parte in polo_passivo:
            # Tentar pegar nome de diferentes campos
            nome = TransformadorDados.limpar_texto(parte.get('nome', '') or parte.get('nome_completo', ''))
            
            if nome:
                # Se está no polo passivo, assume que é réu
                partes_passivas_nomes.append(nome)
        
        # Cliente = polo passivo (primeiro nome)
        cliente = partes_passivas_nomes[0] if partes_passivas_nomes else ""
        
        # Processar eventos
        eventos = TransformadorDados.processar_movimentacoes(movimentacoes)
        
        # Extrair data da última movimentação para status
        data_status = ""
        if movimentacoes:
            primeira_mov = movimentacoes[0]
            movimento = primeira_mov.get('movimento', '')
            data_match = re.search(r'(\d{2}/\d{2}/\d{4})', movimento)
            if data_match:
                data_status = data_match.group(1)
        
        # Construir objeto completo
        dados_transformados = {
            # Dados básicos
            'pasta': '',
            'numeroProcessoAnterior': '',
            'cnj': TransformadorDados.extrair_numero_cnj(numero_processo),
            'tipoPartePoloAtivo': 'Autor' if partes_ativas_nomes else '',
            'partePoloAtivo': '; '.join(partes_ativas_nomes),
            'tipoPartePoloPassivo': 'Réu' if partes_passivas_nomes else '',
            'partePoloPassivo': '; '.join(partes_passivas_nomes),
            'cliente': cliente,
            'tipoDeRito': tipo_rito,
            'dataDistribuicao': data_distribuicao,
            'numeroUnidade': numero_unidade,
            'unidade': unidade,
            'especialidade': especialidade if especialidade else 'Cível',  # Garantir que sempre tenha valor
            'comarca': comarca,
            'estado': estado,
            'orgao': orgao_julgador,
            'natureza': 'Judicial',
            'materia': 'Cível',
            'dataInstancia': '',
            'tipoInstancia': '1ª Instância',
            'sistemaExterno': sistema_externo,
            'processoEletronico': 'Sim',
            'processoEstrategico': 'Não',
            'valorCausa': '',
            'valorFinalCausa': '',
            'tipoAcao': 'Reclamação',
            'tipoObjeto': '',
            'dataFase': '',
            'fase': '',
            'dataStatus': data_status,
            'status': 'Ativo',
            'grupoProcesso': '101',
            'prioridadeDe': '438',
            'data_resultado': '',
            'tipo_resultado': '',
            'descricao_resultado': '',
            # Eventos (primeiro evento como exemplo)
            'dataEvento': eventos[0].get('dataEvento', '') if eventos else '',
            'tipoEvento': eventos[0].get('tipoEvento', '') if eventos else '',
            'descricaoEvento': eventos[0].get('descricaoEvento', '') if eventos else '',
            'complementoEvento': eventos[0].get('complementoEvento', '') if eventos else '',
            'observacaoEvento': eventos[0].get('observacaoEvento', '') if eventos else '',
            'solicitanteEvento': eventos[0].get('solicitanteEvento', '') if eventos else '',
            'responsavelEvento': eventos[0].get('responsavelEvento', '') if eventos else '',
            'grupoTrabalho': '',
            'corresponsavel': '32',
            'dataNotificacao': 'Agora',
            'dataNotificacaoAdicional': '',
            'probabilidadePerda': 'Possível',
            'dataValorProvisionado': '',
            'valorProvisionado': '',
            'dataAndamento': '',
            'tipoAndamento': 'Não informado',
            'descricaoAndamento': '',
            'complementoAndamento': '',
            'solicitanteAndamento': '438',
            'responsavelAndamento': '438',
            'corresponsavelAndamento': '438',
            'descricaoObjeto': 'Não informado',
            'escritorioCredenciado': '',
            'dataContratacao': '',
            'observacaoDoProcesso': '',
            'parecerDoProcesso': ''
        }
        
        return dados_transformados
    
    @staticmethod
    def transformar_lote(resultados: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transforma uma lista de resultados"""
        dados_transformados = []
        for resultado in resultados:
            transformado = TransformadorDados.transformar_dados(resultado)
            if transformado:
                dados_transformados.append(transformado)
        return dados_transformados

