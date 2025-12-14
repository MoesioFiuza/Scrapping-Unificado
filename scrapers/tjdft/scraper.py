from scrapers.base import BaseScraper
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from config.settings import CHROME_DRIVER_PATH, CHROME_USER_DATA_DIR, CHROME_PROFILE_DIRECTORY, DELAY_ENTRE_PROCESSOS
import time
import re
import traceback
import os
from datetime import datetime

class PJeScraperTJDFT(BaseScraper):
    
    def __init__(self, config):
        super().__init__(config)
        self.url_consulta = "https://pje-consultapublica.tjdft.jus.br/consultapublica/ConsultaPublica/listView.seam"
        self.headless = config.get('headless', False)
    
    def setup_driver(self):
        """Configura o driver do Chrome"""
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from config.settings import HEADLESS_MODE
        
        try:
            chrome_options = Options()
            
            # Usar headless do config ou da variável de ambiente
            use_headless = self.headless or HEADLESS_MODE
            
            if use_headless:
                chrome_options.add_argument("--headless")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_argument("--window-size=1920,1080")
                chrome_options.add_argument("--start-maximized")
                chrome_options.add_argument("--disable-extensions")
                chrome_options.add_argument("--disable-software-rasterizer")
                chrome_options.add_argument("--disable-background-timer-throttling")
                chrome_options.add_argument("--disable-backgrounding-occluded-windows")
                chrome_options.add_argument("--disable-renderer-backgrounding")
                chrome_options.add_argument("--disable-features=TranslateUI")
                chrome_options.add_argument("--disable-ipc-flooding-protection")
                chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36")
                print("Modo headless ativado")
            else:
                if CHROME_USER_DATA_DIR:
                    chrome_options.add_argument(f"--user-data-dir={CHROME_USER_DATA_DIR}")
                    chrome_options.add_argument(f"--profile-directory={CHROME_PROFILE_DIRECTORY}")
                chrome_options.add_experimental_option("detach", True)
            
            # Opções comuns
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            if CHROME_DRIVER_PATH:
                service = Service(CHROME_DRIVER_PATH)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                # Usar webdriver-manager como fallback
                try:
                    from webdriver_manager.chrome import ChromeDriverManager
                    service = Service(ChromeDriverManager().install())
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                except Exception as e:
                    # Último recurso: deixar Selenium encontrar automaticamente
                    print(f"Aviso: Erro ao usar webdriver-manager: {e}. Tentando sem Service...")
                    self.driver = webdriver.Chrome(options=chrome_options)
            
            if not use_headless:
                self.driver.maximize_window()
            
            print("Driver do Chrome configurado com sucesso")
            return self.driver
        except Exception as e:
            print(f"Erro ao configurar driver: {str(e)}")
            print(traceback.format_exc())
            raise
    
    def raspar_processo(self, numero_processo: str) -> dict:
        """Raspa os dados de um processo do TJDFT"""
        print(f"Iniciando scraping do processo: {numero_processo}")
        
        self.ensure_driver()
        
        # 1. Guardar o ID da janela original (Pesquisa)
        janela_pesquisa = self.driver.current_window_handle
        todas_janelas_antes = set(self.driver.window_handles)
        
        try:
            # Acessar página de consulta
            print(f"Acessando: {self.url_consulta}")
            self.driver.get(self.url_consulta)
            time.sleep(2)
            
            # Aguardar página carregar
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[contains(@id, 'numProcesso-inputNumeroProcesso')]"))
            )
            
            # Preencher número do processo
            campo_processo = self.driver.find_element(By.XPATH, "//input[contains(@id, 'numProcesso-inputNumeroProcesso')]")
            campo_processo.clear()
            campo_processo.send_keys(numero_processo)
            time.sleep(1)
            
            # Clicar em consultar
            try:
                botao_consultar = self.driver.find_element(By.ID, "fPP:searchProcessos")
            except:
                botao_consultar = self.driver.find_element(By.XPATH, "//input[contains(@id, 'searchProcessos') or contains(@value, 'Consultar')]")
            
            botao_consultar.click()
            time.sleep(3)
            
            # Aguardar resultados ou mensagem de erro
            try:
                # Tentar encontrar a tabela de resultados
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "table.rich-table"))
                )
                
                # Verificar se há resultados
                try:
                    mensagem_sem_resultados = self.driver.find_element(By.XPATH, "//td[contains(text(), 'resultados encontrados')]")
                    if "«««»»»" in mensagem_sem_resultados.text or "0" in mensagem_sem_resultados.text:
                        return {
                            'sucesso': False,
                            'numero_processo': numero_processo,
                            'erro': "Processo não encontrado"
                        }
                except:
                    pass
                
                # 2. Clicar no botão que abre o PopUp
                primeiro_resultado = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "table.rich-table tbody tr:first-child td:first-child a"))
                )
                primeiro_resultado.click()
                
                # 3. Aguardar a nova janela abrir e trocar o foco para ela
                WebDriverWait(self.driver, 10).until(EC.new_window_is_opened(list(todas_janelas_antes)))
                
                todas_janelas_depois = set(self.driver.window_handles)
                nova_janela = (todas_janelas_depois - todas_janelas_antes).pop()
                
                self.driver.switch_to.window(nova_janela)
                print(f"Trocado foco para a janela do processo: {nova_janela}")
                
                # Aguardar o carregamento da NOVA página (Detalhes)
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'rich-stglpanel')]"))
                )
                
                # Aguardar mais um pouco para garantir renderização completa
                time.sleep(3)
                
                # 4. Agora sim, extrair os dados na janela correta
                dados = self._extrair_dados_processo()
                
                # 5. Fechar a janela de detalhes e voltar para a pesquisa
                self.driver.close()
                self.driver.switch_to.window(janela_pesquisa)
                
                # Retornar no formato esperado pelo ScraperService
                return {
                    'sucesso': True,
                    'numero_processo': numero_processo,
                    'dados': dados
                }
                
            except TimeoutException:
                # Verificar se há mensagem de erro
                try:
                    erro_element = self.driver.find_element(By.CSS_SELECTOR, "span.rich-message-text")
                    if erro_element:
                        return {
                            'sucesso': False,
                            'numero_processo': numero_processo,
                            'erro': erro_element.text
                        }
                except:
                    pass
                
                return {
                    'sucesso': False,
                    'numero_processo': numero_processo,
                    'erro': "Timeout ao aguardar resultados"
                }
        
        except Exception as e:
            print(f"Erro ao raspar processo {numero_processo}: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Se der erro, tenta garantir que voltou para a janela principal
            try:
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                self.driver.switch_to.window(janela_pesquisa)
            except:
                pass
            
            return {
                'sucesso': False,
                'numero_processo': numero_processo,
                'erro': f"Erro ao raspar: {str(e)}"
            }
    
    def _extrair_dados_processo(self) -> dict:
        """Extrai todos os dados do processo"""
        dados = {}
        
        try:
            # Aguardar conteúdo principal carregar
            print("Aguardando página de detalhes carregar...")
            time.sleep(2)
            
            # 1. DADOS DO PROCESSO
            dados['dados_processo'] = self._extrair_dados_basicos()
            
            # 2. POLO ATIVO
            dados['polo_ativo'] = self._extrair_polo_ativo()
            
            # 3. POLO PASSIVO
            dados['polo_passivo'] = self._extrair_polo_passivo()
            
            # 4. MOVIMENTAÇÕES
            dados['movimentacoes'] = self._extrair_movimentacoes()
            
            # 5. DOCUMENTOS
            dados['documentos'] = self._extrair_documentos()
            
            print("Dados extraídos com sucesso!")
            
        except Exception as e:
            error_msg = str(e)
            print(f"Erro ao extrair dados: {error_msg}")
            import traceback
            traceback.print_exc()
            dados['erro_extracao'] = error_msg
        
        return dados
    
    def _extrair_dados_basicos(self) -> dict:
        """Extrai dados básicos do processo"""
        dados_basicos = {}
        
        try:
            # Aguardar página carregar completamente
            time.sleep(2)
            
            # Procurar pelo painel usando múltiplos métodos
            panel = None
            
            # Método 1: Procurar pelo ID parcial divDadosProcesso
            try:
                header_div = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@id, 'divDadosProcesso')]"))
                )
                print("Header encontrado pelo ID 'divDadosProcesso'")
                panel = header_div.find_element(By.XPATH, "./ancestor::div[contains(@class, 'rich-stglpanel')]")
            except TimeoutException:
                pass
            
            # Método 2: Procurar pelo texto usando normalize-space
            if not panel:
                try:
                    header_div = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//div[normalize-space(text())='Dados do Processo']"))
                    )
                    print("Header encontrado pelo texto 'Dados do Processo'")
                    panel = header_div.find_element(By.XPATH, "./ancestor::div[contains(@class, 'rich-stglpanel')]")
                except TimeoutException:
                    pass
            
            # Método 3: Procurar por contains
            if not panel:
                try:
                    header_div = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//div[contains(., 'Dados do Processo')]"))
                    )
                    print("Header encontrado por contains(., 'Dados do Processo')")
                    panel = header_div.find_element(By.XPATH, "./ancestor::div[contains(@class, 'rich-stglpanel')]")
                except TimeoutException:
                    pass
            
            if not panel:
                print("ERRO: Painel 'Dados do Processo' não encontrado")
                return dados_basicos
            
            # Verificar se o painel está colapsado e expandir se necessário
            try:
                switch_off = panel.find_element(By.XPATH, ".//div[contains(@class, 'rich-stglpnl-marker') and contains(@id, 'switch_off')]")
                if switch_off.is_displayed():
                    print("Painel está colapsado, expandindo...")
                    panel_header = panel.find_element(By.XPATH, ".//div[contains(@class, 'rich-stglpanel-header')]")
                    panel_header.click()
                    time.sleep(2)
            except NoSuchElementException:
                print("Painel parece estar expandido")
            
            # Aguardar tabela carregar
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'rich-stglpanel-body')]//table[@width='100%']//div[contains(@class, 'propertyView')]"))
                )
            except TimeoutException:
                print("Nenhum propertyView encontrado")
                return dados_basicos
            
            time.sleep(1)
            
            # Encontrar todos os propertyView dentro do painel
            property_views = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'rich-stglpanel-body')]//table[@width='100%']//div[contains(@class, 'propertyView')]")
            
            print(f"Encontrados {len(property_views)} propertyViews")
            
            for pv in property_views:
                try:
                    # Encontrar o label
                    try:
                        label_elem = pv.find_element(By.TAG_NAME, "label")
                        label_text = label_elem.text.strip()
                    except:
                        label_text = ""
                    
                    # Encontrar o valor
                    value_div = pv.find_element(By.XPATH, ".//div[contains(@class, 'value')]")
                    
                    # Extrair texto do valor
                    try:
                        inner_div = value_div.find_element(By.XPATH, ".//div[@class='col-sm-12']")
                        valor = inner_div.text.strip()
                    except:
                        valor = value_div.text.strip()
                    
                    # Remover espaços extras
                    valor = re.sub(r'\s+', ' ', valor).strip()
                    
                    # Mapear labels para campos
                    if 'Número Processo' in label_text:
                        dados_basicos['numero_processo'] = valor
                    elif 'Data da Distribuição' in label_text:
                        dados_basicos['data_distribuicao'] = valor
                    elif 'Classe Judicial' in label_text:
                        dados_basicos['classe_judicial'] = valor
                    elif 'Assunto' in label_text:
                        dados_basicos['assunto'] = valor
                    elif 'Jurisdição' in label_text:
                        dados_basicos['jurisdicao'] = valor
                    elif 'Órgão Julgador' in label_text or ('Órgão Julgador' in valor and not label_text):
                        # Para órgão julgador, o label pode estar vazio
                        if 'Órgão Julgador' in valor:
                            try:
                                html_content = value_div.get_attribute('innerHTML')
                                match = re.search(r'Órgão Julgador</b>\s*<br\s*/?>\s*([^<]+)', html_content)
                                if match:
                                    dados_basicos['orgao_julgador'] = match.group(1).strip()
                                else:
                                    partes = valor.split('Órgão Julgador')
                                    if len(partes) > 1:
                                        dados_basicos['orgao_julgador'] = partes[1].strip().split('\n')[0].strip()
                                    else:
                                        dados_basicos['orgao_julgador'] = valor.split('\n')[0].strip()
                            except:
                                dados_basicos['orgao_julgador'] = valor.split('\n')[0].strip()
                    
                except Exception as e:
                    print(f"Erro ao processar propertyView: {e}")
                    continue
            
            # Garantir que todos os campos existam
            campos_obrigatorios = ['numero_processo', 'data_distribuicao', 'classe_judicial', 'assunto', 'jurisdicao', 'orgao_julgador', 'juiz', 'valor_acao']
            for campo in campos_obrigatorios:
                if campo not in dados_basicos:
                    dados_basicos[campo] = ""
                    
        except Exception as e:
            print(f"Erro geral em dados básicos: {e}")
            print(traceback.format_exc())
        
        return dados_basicos
    
    def _extrair_partes(self) -> list:
        """Extrai partes do processo (polo ativo e passivo)"""
        partes = []
        
        try:
            # Extrair polo ativo
            polo_ativo = self._extrair_polo_ativo()
            partes.extend(polo_ativo)
            
            # Extrair polo passivo
            polo_passivo = self._extrair_polo_passivo()
            partes.extend(polo_passivo)
        
        except Exception as e:
            print(f"Erro ao extrair partes: {e}")
            print(traceback.format_exc())
        
        return partes
    
    def _extrair_polo_ativo(self) -> list:
        """Extrai participantes do polo ativo"""
        participantes = []
        
        try:
            print("Extraindo polo ativo...")
            
            # Aguardar tabela carregar
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//table[contains(@id, 'processoPartesPoloAtivoResumidoList')]"))
                )
            except TimeoutException:
                print("Tabela de polo ativo não encontrada")
                return participantes
            
            time.sleep(1)
            
            # Encontrar tabela
            try:
                tabela = self.driver.find_element(By.XPATH, "//table[contains(@id, 'processoPartesPoloAtivoResumidoList')]")
            except NoSuchElementException:
                try:
                    panel_header = self.driver.find_element(By.XPATH, "//div[contains(@class, 'rich-panel-header') and (contains(text(), 'Polo ativo') or contains(text(), 'Polo Ativo'))]")
                    panel = panel_header.find_element(By.XPATH, "./ancestor::div[contains(@class, 'rich-panel')]")
                    tabela = panel.find_element(By.XPATH, ".//table[contains(@id, 'processoPartesPoloAtivoResumidoList')]")
                except:
                    print("Erro: Tabela de polo ativo não encontrada")
                    return participantes
            
            # Encontrar tbody
            try:
                tbody = tabela.find_element(By.XPATH, ".//tbody[@id[contains(., 'tb')]]")
            except:
                tbody = tabela.find_element(By.TAG_NAME, "tbody")
            
            # Encontrar todas as linhas
            linhas = tbody.find_elements(By.XPATH, ".//tr[contains(@class, 'rich-table-row')]")
            print(f"Encontradas {len(linhas)} linhas no polo ativo")
            
            for linha in linhas:
                try:
                    celulas = linha.find_elements(By.TAG_NAME, "td")
                    if len(celulas) >= 1:
                        # Extrair texto da primeira célula (participante)
                        try:
                            span_bold = celulas[0].find_element(By.XPATH, ".//span[contains(@class, 'text-bold')]")
                            texto_completo = span_bold.text.strip()
                        except:
                            try:
                                spans = celulas[0].find_elements(By.XPATH, ".//span")
                                texto_completo = ""
                                for span in spans:
                                    texto = span.text.strip()
                                    if texto and len(texto) > 5:
                                        texto_completo = texto
                                        break
                                if not texto_completo:
                                    texto_completo = celulas[0].text.strip()
                            except:
                                texto_completo = celulas[0].text.strip()
                        
                        texto_completo = re.sub(r'^[\s\xa0]+', '', texto_completo)
                        
                        if not texto_completo:
                            continue
                        
                        # Extrair situação da segunda célula (se houver)
                        situacao = ""
                        if len(celulas) >= 2:
                            situacao = celulas[1].text.strip()
                        
                        # Parsear dados do participante
                        participante = self._parsear_participante(texto_completo)
                        participante['situacao'] = situacao
                        participante['polo'] = 'Ativo'
                        
                        participantes.append(participante)
                        
                except Exception as e:
                    print(f"Erro ao processar linha do polo ativo: {e}")
                    continue
        
        except Exception as e:
            print(f"Erro ao extrair polo ativo: {e}")
            print(traceback.format_exc())
        
        return participantes
    
    def _extrair_polo_passivo(self) -> list:
        """Extrai participantes do polo passivo"""
        participantes = []
        
        try:
            print("Extraindo polo passivo...")
            
            # Aguardar tabela carregar
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//table[contains(@id, 'processoPartesPoloPassivoResumidoList')]"))
                )
            except TimeoutException:
                print("Tabela de polo passivo não encontrada")
                return participantes
            
            time.sleep(1)
            
            # Encontrar tabela
            try:
                tabela = self.driver.find_element(By.XPATH, "//table[contains(@id, 'processoPartesPoloPassivoResumidoList')]")
            except NoSuchElementException:
                try:
                    panel_header = self.driver.find_element(By.XPATH, "//div[contains(@class, 'rich-panel-header') and (contains(text(), 'Polo Passivo') or contains(text(), 'Polo passivo'))]")
                    panel = panel_header.find_element(By.XPATH, "./ancestor::div[contains(@class, 'rich-panel')]")
                    tabela = panel.find_element(By.XPATH, ".//table[contains(@id, 'processoPartesPoloPassivoResumidoList')]")
                except:
                    print("Erro: Tabela de polo passivo não encontrada")
                    return participantes
            
            # Encontrar tbody
            try:
                tbody = tabela.find_element(By.XPATH, ".//tbody[@id[contains(., 'tb')]]")
            except:
                tbody = tabela.find_element(By.TAG_NAME, "tbody")
            
            # Encontrar todas as linhas
            linhas = tbody.find_elements(By.XPATH, ".//tr[contains(@class, 'rich-table-row')]")
            print(f"Encontradas {len(linhas)} linhas no polo passivo")
            
            for linha in linhas:
                try:
                    celulas = linha.find_elements(By.TAG_NAME, "td")
                    if len(celulas) >= 1:
                        # Extrair texto da primeira célula (participante)
                        try:
                            span_bold = celulas[0].find_element(By.XPATH, ".//span[contains(@class, 'text-bold')]")
                            texto_completo = span_bold.text.strip()
                        except:
                            try:
                                spans = celulas[0].find_elements(By.XPATH, ".//span")
                                texto_completo = ""
                                for span in spans:
                                    texto = span.text.strip()
                                    if texto and len(texto) > 5:
                                        texto_completo = texto
                                        break
                                if not texto_completo:
                                    texto_completo = celulas[0].text.strip()
                            except:
                                texto_completo = celulas[0].text.strip()
                        
                        texto_completo = re.sub(r'^[\s\xa0]+', '', texto_completo)
                        
                        if not texto_completo:
                            continue
                        
                        # Extrair situação da segunda célula (se houver)
                        situacao = ""
                        if len(celulas) >= 2:
                            situacao = celulas[1].text.strip()
                        
                        # Parsear dados do participante
                        participante = self._parsear_participante(texto_completo)
                        participante['situacao'] = situacao
                        participante['polo'] = 'Passivo'
                        
                        participantes.append(participante)
                        
                except Exception as e:
                    print(f"Erro ao processar linha do polo passivo: {e}")
                    continue
        
        except Exception as e:
            print(f"Erro ao extrair polo passivo: {e}")
            print(traceback.format_exc())
        
        return participantes
    
    def _parsear_participante(self, texto: str) -> dict:
        """Parseia o texto do participante para extrair nome, CPF/CNPJ, OAB, tipo, etc."""
        participante = {
            'nome': '',
            'nome_completo': '',
            'cpf': '',
            'cnpj': '',
            'oab': '',
            'tipo': '',
            'advogado': ''
        }
        
        try:
            # Remover espaços extras
            texto = re.sub(r'\s+', ' ', texto).strip()
            participante['nome_completo'] = texto
            
            # Extrair CPF
            cpf_match = re.search(r'CPF:\s*([\d\.\-]+)', texto)
            if cpf_match:
                participante['cpf'] = cpf_match.group(1).strip()
            
            # Extrair CNPJ
            cnpj_match = re.search(r'CNPJ:\s*([\d\.\/\-]+)', texto)
            if cnpj_match:
                participante['cnpj'] = cnpj_match.group(1).strip()
            
            # Extrair OAB
            oab_match = re.search(r'OAB\s+([A-Z]{2}\d+[A-Z]?)', texto)
            if oab_match:
                participante['oab'] = oab_match.group(1).strip()
            
            # Extrair tipo (REQUERENTE, REQUERIDO, ADVOGADO, etc.)
            if 'REQUERENTE' in texto.upper():
                participante['tipo'] = 'Requerente'
            elif 'REQUERIDO' in texto.upper():
                participante['tipo'] = 'Requerido'
            elif 'ADVOGADO' in texto.upper():
                participante['tipo'] = 'Advogado'
                participante['advogado'] = texto
            
            # Extrair nome (remover CPF, CNPJ, OAB, tipo)
            nome = texto
            nome = re.sub(r'CPF:\s*[\d\.\-]+', '', nome)
            nome = re.sub(r'CNPJ:\s*[\d\.\/\-]+', '', nome)
            nome = re.sub(r'OAB\s+[A-Z]{2}\d+[A-Z]?', '', nome)
            nome = re.sub(r'\(REQUERENTE\)|\(REQUERIDO\)|\(ADVOGADO\)', '', nome, flags=re.IGNORECASE)
            nome = re.sub(r'\s+', ' ', nome).strip()
            participante['nome'] = nome
            
        except Exception as e:
            print(f"Erro ao parsear participante: {e}")
        
        return participante
    
    def _extrair_movimentacoes(self) -> list:
        """Extrai movimentações do processo"""
        movimentacoes = []
        
        try:
            print("Extraindo movimentações...")
            
            # Aguardar tabela carregar
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//table[contains(@id, 'processoEvento')]"))
                )
            except TimeoutException:
                print("Tabela de movimentações não encontrada")
                return movimentacoes
            
            time.sleep(1)
            
            # Encontrar tabela
            try:
                tabela = self.driver.find_element(By.XPATH, "//table[contains(@id, 'processoEvento')]")
            except NoSuchElementException:
                try:
                    panel_header = self.driver.find_element(By.XPATH, "//div[contains(@class, 'rich-panel-header') and contains(text(), 'Movimentações do Processo')]")
                    panel = panel_header.find_element(By.XPATH, "./ancestor::div[contains(@class, 'rich-panel')]")
                    tabela = panel.find_element(By.XPATH, ".//table[contains(@id, 'processoEvento')]")
                except:
                    print("Erro: Tabela de movimentações não encontrada")
                    return movimentacoes
            
            # Encontrar tbody
            try:
                tbody = tabela.find_element(By.XPATH, ".//tbody[@id[contains(., 'tb')]]")
            except:
                tbody = tabela.find_element(By.TAG_NAME, "tbody")
            
            # Encontrar todas as linhas
            linhas = tbody.find_elements(By.XPATH, ".//tr[contains(@class, 'rich-table-row')]")
            print(f"Encontradas {len(linhas)} linhas de movimentações")
            
            for linha in linhas:
                try:
                    celulas = linha.find_elements(By.TAG_NAME, "td")
                    if len(celulas) >= 1:
                        # Extrair movimento da primeira célula
                        try:
                            # Tentar encontrar span com id contendo j_id
                            span = celulas[0].find_element(By.XPATH, ".//span[@id[contains(., 'j_id')]]")
                            movimento_texto = span.text.strip()
                        except:
                            try:
                                div = celulas[0].find_element(By.XPATH, ".//div[@class='col-sm-12']")
                                movimento_texto = div.text.strip()
                            except:
                                movimento_texto = celulas[0].text.strip()
                        
                        if not movimento_texto:
                            continue
                        
                        # Extrair data e hora
                        data_match = re.search(r'(\d{2}/\d{2}/\d{4})\s+(\d{2}:\d{2}:\d{2})', movimento_texto)
                        
                        # Remover data/hora do texto para obter descrição
                        descricao = re.sub(r'\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}\s*-\s*', '', movimento_texto).strip()
                        
                        # Extrair documento da segunda célula (se houver)
                        documento = ""
                        if len(celulas) > 1:
                            try:
                                # Tentar encontrar link de documento
                                link = celulas[1].find_element(By.TAG_NAME, "a")
                                documento = link.text.strip()
                            except:
                                documento = celulas[1].text.strip()
                        
                        movimentacoes.append({
                            'movimento': movimento_texto,
                            'descricao': descricao,
                            'documento': documento,
                            'data': data_match.group(1) if data_match else None,
                            'hora': data_match.group(2) if data_match else None
                        })
                        
                except Exception as e:
                    print(f"Erro ao processar linha de movimentação: {e}")
                    continue
        
        except Exception as e:
            print(f"Erro ao extrair movimentações: {e}")
            print(traceback.format_exc())
        
        print(f"Total de movimentações extraídas: {len(movimentacoes)}")
        return movimentacoes
    
    def _extrair_documentos(self) -> list:
        """Extrai documentos do processo"""
        documentos = []
        # Implementar se necessário
        return documentos
