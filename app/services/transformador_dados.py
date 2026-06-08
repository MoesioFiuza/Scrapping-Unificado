from typing import Dict, Any, List
from datetime import datetime
import re
from app.services.transformador_esaj import TransformadorESAJ

class TransformadorDados:

    TRIBUNAL_ESTADO_MAP = {
        "8.19": "RJ",  # TJRJ
        "8.06": "CE",  # TJCE (PJe)
        "8.06_esaj": "CE",  # eSAJ TJCE
        "8.13": "MG",  # TJMG
        "8.17": "PE",  # TJPE
        "8.02": "AL",  # eSAJ TJAL
        "8.26": "SP",  # eSAJ SP
        "8.10": "MA",  # TJMA
        "8.07": "DF",  # TJDFT
        "8.20": "RN",  # TJRN
    }
    
    TRIBUNAL_NOME_MAP = {
        "8.19": "TJRJ",
        "8.06": "TJCE",
        "8.06_esaj": "eSAJ CE",
        "8.13": "TJMG",
        "8.17": "TJPE",
        "8.02": "eSAJ AL",
        "8.26": "eSAJ SP",
        "8.10": "TJMA",
        "8.07": "TJDFT",
        "8.20": "TJRN",
    }
    
    @staticmethod
    def limpar_texto(texto: str) -> str:
        if not texto:
            return ""
        texto = re.sub(r'\s+', ' ', str(texto))
        return texto.strip()

    @staticmethod
    def normalizar_nome_participante(nome: str) -> str:
        """Remove expressões como 'registrado(a) civilmente como X' do nome para exibição limpa na planilha."""
        if not nome:
            return ""
        nome = TransformadorDados.limpar_texto(nome)
        # Remove "registrado(a) civilmente como ..." (até o fim ou até próximo trecho relevante)
        nome = re.sub(r'\s*registrado\(a\)\s+civilmente\s+como\s+.+$', '', nome, flags=re.IGNORECASE)
        return nome.strip()
    
    @staticmethod
    def extrair_numero_cnj(numero_processo: str) -> str:
        return TransformadorDados.limpar_texto(numero_processo) if numero_processo else ""
    
    @staticmethod
    def extrair_tipo_rito(classe_judicial: str) -> str:
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
        return TransformadorDados.TRIBUNAL_ESTADO_MAP.get(tribunal_key, "")
    
    @staticmethod
    def obter_sistema_externo(tribunal_key: str) -> str:
        nome_tribunal = TransformadorDados.TRIBUNAL_NOME_MAP.get(tribunal_key, "")
        estado = TransformadorDados.obter_estado_por_tribunal(tribunal_key)
        
        if tribunal_key in ("8.26", "8.02", "8.06_esaj"):
            return f"TJ-{estado}-eSAJ-1° Grau"
        
        if nome_tribunal and estado:
            return f"TJ-{estado}-PJE-1° Grau"
        return ""
    
    @staticmethod
    def extrair_unidade_especialidade(classe_judicial: str, orgao_julgador: str = "") -> tuple:
        unidade = ""
        especialidade = "Cível"
        
        if classe_judicial:
            classe_lower = classe_judicial.lower()
            if "juizado especial" in classe_lower:
                unidade = "Juizado Especial"
            elif "vara" in classe_lower:
                unidade = "Vara"
            elif "juizado" in classe_lower:
                unidade = "Juizado"
        
        if not unidade and orgao_julgador:
            orgao_lower = orgao_julgador.lower()
            if "juizado" in orgao_lower:
                unidade = "Juizado Especial"
            elif "vara" in orgao_lower:
                unidade = "Vara"
            elif "núcleo" in orgao_lower or "nucleo" in orgao_lower:
                unidade = "Núcleo"
        
        return (unidade, especialidade)
    
    @staticmethod
    def extrair_numero_unidade(orgao_julgador: str) -> str:
        if not orgao_julgador:
            return "0"
        
        orgao_limpo = TransformadorDados.limpar_texto(orgao_julgador)
        
        match = re.search(r'(\d+)[ºª]', orgao_limpo)
        if match:
            return match.group(1)
        
        return "0"
    
    @staticmethod
    def extrair_comarca_estado(jurisdicao: str, orgao_julgador: str = "") -> tuple:
        comarca = ""
        jurisdicao_limpa = TransformadorDados.limpar_texto(jurisdicao) if jurisdicao else ""
        
        if orgao_julgador:
            orgao_limpo = TransformadorDados.limpar_texto(orgao_julgador)
            match_orgao = re.search(r'comarca de (.+)', orgao_limpo, re.IGNORECASE)
            if match_orgao:
                comarca = match_orgao.group(1).strip()
                comarca = comarca.rstrip('.')
        
        if not comarca and jurisdicao_limpa:
            match = re.search(r'Comarca de (.+)', jurisdicao_limpa, re.IGNORECASE)
            if match:
                comarca = match.group(1).strip()
            else:
                if "comarca" in jurisdicao_limpa.lower():
                    match2 = re.search(r'comarca[:\s]+(.+)', jurisdicao_limpa, re.IGNORECASE)
                    if match2:
                        comarca = match2.group(1).strip()
                else:
                    comarca = jurisdicao_limpa
        
        if not comarca and orgao_julgador:
            orgao_limpo = TransformadorDados.limpar_texto(orgao_julgador)
            if "núcleo" in orgao_limpo.lower() or "nucleo" in orgao_limpo.lower():
                match_nucleo = re.search(r'(núcleo[:\s]+[^,\.]+)', orgao_limpo, re.IGNORECASE)
                if match_nucleo:
                    comarca = match_nucleo.group(1).strip()
                else:
                    match_nucleo2 = re.search(r'núcleo[:\s]*(.+)', orgao_limpo, re.IGNORECASE)
                    if match_nucleo2:
                        comarca = f"Núcleo {match_nucleo2.group(1).strip()}"
                    else:
                        comarca = orgao_limpo
            else:
                if jurisdicao_limpa:
                    comarca = jurisdicao_limpa
                else:
                    comarca = orgao_limpo
        
        return (comarca, "")
    
    @staticmethod
    def extrair_tipo_parte(participante: Dict[str, Any]) -> str:
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
        eventos = []
        for mov in movimentacoes:
            movimento = mov.get('movimento', '') or mov.get('descricao', '')
            if movimento:
                data_evento = mov.get('data', '')
                hora_evento = mov.get('hora', '')
                
                if not data_evento:
                    data_match = re.search(r'(\d{2}/\d{2}/\d{4})\s+(\d{2}:\d{2}:\d{2})', movimento)
                    if not data_match:
                        data_match = re.search(r'(\d{2}/\d{2}/\d{4})', movimento)
                    
                    data_evento = data_match.group(1) if data_match else ""
                    if not hora_evento and data_match and len(data_match.groups()) > 1:
                        hora_evento = data_match.group(2)
                
                tipo_evento = "1035"
                
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
        if resultado.get('status') != 'sucesso' or not resultado.get('dados'):
            return {}
        
        if resultado.get('tribunal') in ('8.26', '8.02', '8.06_esaj'):
            resultado = TransformadorESAJ.normalizar_resultado(resultado)
        
        dados = resultado['dados']
        dados_processo = dados.get('dados_processo', {})
        polo_ativo = dados.get('polo_ativo', [])
        polo_passivo = dados.get('polo_passivo', [])
        movimentacoes = dados.get('movimentacoes', [])
        documentos = dados.get('documentos', [])
        
        ##print(f"DEBUG - Polo ativo recebido: {len(polo_ativo)} itens")
        ##print(f"DEBUG - Polo passivo recebido: {len(polo_passivo)} itens")
        ##if polo_ativo:
            ##print(f"DEBUG - Primeiro polo ativo: {polo_ativo[0]}")
        ##if polo_passivo:
            ##print(f"DEBUG - Primeiro polo passivo: {polo_passivo[0]}")
        
        numero_processo = resultado.get('numero_processo', '')
        tribunal_key = resultado.get('tribunal', '')
        classe_judicial = dados_processo.get('classe_judicial', '')
        assunto = dados_processo.get('assunto', '')
        jurisdicao = dados_processo.get('jurisdicao', '')
        orgao_julgador = dados_processo.get('orgao_julgador', '')
        data_distribuicao = dados_processo.get('data_distribuicao', '')    
        classe_judicial = TransformadorDados.limpar_texto(classe_judicial)
        assunto = TransformadorDados.limpar_texto(assunto)
        jurisdicao = TransformadorDados.limpar_texto(jurisdicao)
        orgao_julgador = TransformadorDados.limpar_texto(orgao_julgador)
        data_distribuicao = TransformadorDados.limpar_texto(data_distribuicao)        
        valor_causa = dados_processo.get('valor_acao', '') or dados_processo.get('valor_causa', '')
        valor_causa = TransformadorDados.limpar_texto(valor_causa)        
        unidade, especialidade = TransformadorDados.extrair_unidade_especialidade(classe_judicial, orgao_julgador)
        comarca, _ = TransformadorDados.extrair_comarca_estado(jurisdicao, orgao_julgador)
        tipo_rito = TransformadorDados.extrair_tipo_rito(classe_judicial)
        numero_unidade = TransformadorDados.extrair_numero_unidade(orgao_julgador)        
        estado = TransformadorDados.obter_estado_por_tribunal(tribunal_key)
        sistema_externo = TransformadorDados.obter_sistema_externo(tribunal_key)
        
        ##print(f"DEBUG - Tribunal: {tribunal_key}, Estado: {estado}, Sistema: {sistema_externo}")
        ##print(f"DEBUG - Comarca: {comarca}, Unidade: {unidade}, NumeroUnidade: {numero_unidade}, Especialidade: {especialidade}")
        
        partes_ativas_nomes = []
        advogados_polo_ativo = []
        for parte in polo_ativo:
            nome = TransformadorDados.limpar_texto(parte.get('nome', '') or parte.get('nome_completo', ''))
            nome_completo = TransformadorDados.limpar_texto(parte.get('nome_completo', ''))
            tipo = parte.get('tipo', '')
            
            if not nome:
                continue
            
            nome_exibicao = TransformadorDados.normalizar_nome_participante(nome)
            tipo_upper = tipo.upper() if tipo else ''
            nome_completo_upper = nome_completo.upper() if nome_completo else ''
            nome_upper = nome.upper()
            
            is_advogado = (
                'ADVOGADO' in tipo_upper or
                'ADVOGADO' in nome_completo_upper or
                'ADVOGADO' in nome_upper or
                'OAB' in nome_upper
            )
            
            if nome_exibicao:
                if not is_advogado:
                    partes_ativas_nomes.append(nome_exibicao)
                else:
                    oab = parte.get('oab') or ''
                    texto_adv = f"{nome_exibicao} - OAB {oab}" if oab else nome_exibicao
                    advogados_polo_ativo.append(texto_adv)
        
        partes_passivas_nomes = []
        for parte in polo_passivo:
            nome = TransformadorDados.limpar_texto(parte.get('nome', '') or parte.get('nome_completo', ''))
            nome_exibicao = TransformadorDados.normalizar_nome_participante(nome)
            if nome_exibicao:
                partes_passivas_nomes.append(nome_exibicao)
        
        cliente = partes_passivas_nomes[0] if partes_passivas_nomes else ""
        
        eventos = TransformadorDados.processar_movimentacoes(movimentacoes)

        data_status = ""
        if movimentacoes:
            primeira_mov = movimentacoes[0]
            data_status = primeira_mov.get('data', '')
            if not data_status:
                movimento = primeira_mov.get('movimento', '') or primeira_mov.get('descricao', '')
                if movimento:
                    data_match = re.search(r'(\d{2}/\d{2}/\d{4})', movimento)
                    if data_match:
                        data_status = data_match.group(1)
        
        dados_transformados = {
            'pasta': '',
            'numeroProcessoAnterior': '',
            'cnj': TransformadorDados.extrair_numero_cnj(numero_processo),
            'tipoPartePoloAtivo': 'Autor' if partes_ativas_nomes else '',
            'partePoloAtivo': '; '.join(partes_ativas_nomes),
            # Advogado Parte Contraria: nomes normalizados + OAB quando disponível (ex.: TJ-RJ)
            'Advogado Parte Contraria': '; '.join(advogados_polo_ativo),
            'tipoPartePoloPassivo': 'Réu' if partes_passivas_nomes else '',
            'partePoloPassivo': '; '.join(partes_passivas_nomes),
            'cliente': cliente,
            'tipoDeRito': tipo_rito,
            'dataDistribuicao': data_distribuicao,
            'numeroUnidade': numero_unidade,
            'unidade': unidade,
            'especialidade': especialidade if especialidade else 'Cível',
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
            'valorCausa': valor_causa,
            'valorFinalCausa': valor_causa,
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
        resultados = TransformadorESAJ.normalizar_lote(resultados)
        
        dados_transformados = []
        for resultado in resultados:
            transformado = TransformadorDados.transformar_dados(resultado)
            if transformado:
                dados_transformados.append(transformado)
        return dados_transformados

