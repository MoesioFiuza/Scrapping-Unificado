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

class PJeScraperTJMA(BaseScraper):
    
    def __init__(self, config):
        super().__init__(config)
        self.url_consulta = "https://pje.tjma.jus.br/pje/ConsultaPublica/listView.seam"
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
        """Raspa os dados de um processo do TJMA"""
        print(f"Iniciando scraping do processo: {numero_processo}")
        
        # Garantir que o driver está válido
        self.ensure_driver()
        
        # Guardar a aba principal (primeira aba)
        aba_principal = None
        try:
            aba_principal = self.driver.window_handles[0] if self.driver.window_handles else None
        except Exception as e:
            print(f"Erro ao obter aba principal: {e}")
            # Se falhar, recriar o driver
            self.ensure_driver()
            aba_principal = self.driver.window_handles[0] if self.driver.window_handles else None
        
        try:
            # Acessar página de consulta
            print(f"Acessando: {self.url_consulta}")
            self.driver.get(self.url_consulta)
            time.sleep(5)
            
            # Localizar e preencher campo de número do processo
            campo_processo_id = "fPP:numProcesso-inputNumeroProcessoDecoration:numProcesso-inputNumeroProcesso"
            print(f"Procurando campo: {campo_processo_id}")
            
            try:
                campo_processo = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.ID, campo_processo_id))
                )
                print("Campo encontrado!")
            except TimeoutException:
                print("Campo não encontrado! Tentando alternativa...")
                # Tentar por name
                campo_processo = self.driver.find_element(By.NAME, "fPP:numProcesso-inputNumeroProcessoDecoration:numProcesso-inputNumeroProcesso")
            
            campo_processo.clear()
            campo_processo.send_keys(numero_processo)
            print(f"Número do processo preenchido: {numero_processo}")
            campo_processo.send_keys(Keys.RETURN)
            
            # Aguardar resultados aparecerem
            print("Aguardando resultados...")
            time.sleep(5)
            
            # Clicar no link do processo (primeiro resultado)
            try:
                # Tentar diferentes seletores
                print("Procurando link do processo...")
                
                # Opção 1: Buscar por texto contendo o número
                xpath_options = [
                    f"//b[contains(text(), '{numero_processo}')]",
                    f"//a[contains(text(), '{numero_processo}')]",
                    f"//*[contains(text(), '{numero_processo}')]",
                    f"//b[@class='btn-block' and contains(text(), '{numero_processo.split('-')[0]}')]"
                ]
                
                link_processo = None
                for xpath in xpath_options:
                    try:
                        link_processo = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, xpath))
                        )
                        print(f"Link encontrado com XPath: {xpath}")
                        break
                    except TimeoutException:
                        continue
                
                if not link_processo:
                    # Tentar buscar na tabela de resultados
                    try:
                        tabela_resultados = self.driver.find_element(By.XPATH, "//table[contains(@class, 'rich-table')]")
                        link_processo = tabela_resultados.find_element(By.TAG_NAME, "a")
                        print("Link encontrado na tabela")
                    except:
                        pass
                
                if link_processo:
                    # Salvar URL atual antes do clique
                    url_antes = self.driver.current_url
                    print(f"URL antes do clique: {url_antes}")
                    
                    # Tentar múltiplas formas de clicar
                    try:
                        # Método 1: Clique normal
                        link_processo.click()
                        print("Link clicado (método normal)!")
                    except:
                        try:
                            # Método 2: Clique via JavaScript
                            self.driver.execute_script("arguments[0].click();", link_processo)
                            print("Link clicado (método JavaScript)!")
                        except:
                            # Método 3: Navegar diretamente pela URL se o link tiver href
                            try:
                                href = link_processo.get_attribute('href')
                                if href:
                                    self.driver.get(href)
                                    print(f"Navegando diretamente para: {href}")
                            except:
                                pass
                    
                    # Verificar se abriu nova aba/janela
                    if len(self.driver.window_handles) > 1:
                        print("Nova aba detectada! Mudando para a nova aba...")
                        # Mudar para a nova aba
                        self.driver.switch_to.window(self.driver.window_handles[-1])
                        print("Mudado para nova aba")
                    
                    # Aguardar mudança de URL ou carregamento da página de detalhes
                    print("Aguardando página de detalhes carregar...")
                    
                    # Aguardar até que a URL mude OU até que apareçam elementos específicos da página de detalhes
                    try:
                        WebDriverWait(self.driver, 15).until(
                            lambda driver: (
                                "DetalheProcesso" in driver.current_url or
                                driver.current_url != url_antes
                            )
                        )
                        print(f"URL mudou para: {self.driver.current_url}")
                    except TimeoutException:
                        print("URL não mudou, mas verificando se conteúdo carregou via AJAX...")
                    
                    # Aguardar mais tempo para garantir que o JavaScript terminou de renderizar
                    time.sleep(5)
                    
                    # Verificar se estamos na página correta procurando por elementos específicos da página de detalhes
                    url_atual = self.driver.current_url
                    print(f"URL atual: {url_atual}")
                    
                    # Verificar se temos os elementos corretos da página de detalhes
                    # A página de detalhes deve ter "rich-stglpanel-body" e labels específicos
                    try:
                        # Procurar por elementos que só existem na página de detalhes
                        elementos_detalhes = self.driver.find_elements(By.XPATH, "//div[@class='rich-stglpanel-body']")
                        labels_detalhes = self.driver.find_elements(By.XPATH, "//label[contains(text(), 'Número Processo')]")
                        
                        print(f"Elementos rich-stglpanel-body: {len(elementos_detalhes)}")
                        print(f"Labels 'Número Processo': {len(labels_detalhes)}")
                        
                        if len(elementos_detalhes) == 0 and len(labels_detalhes) == 0:
                            print("ERRO: Não estamos na página de detalhes! Tentando encontrar o link novamente...")
                            
                            # Tentar encontrar e clicar no link novamente de forma diferente
                            try:
                                # Procurar por qualquer link que contenha o número do processo
                                links = self.driver.find_elements(By.XPATH, f"//a[contains(text(), '{numero_processo}')] | //b[contains(text(), '{numero_processo}')]")
                                if links:
                                    print(f"Encontrados {len(links)} links com o número do processo")
                                    # Tentar clicar no primeiro link encontrado
                                    self.driver.execute_script("arguments[0].click();", links[0])
                                    time.sleep(5)
                                    
                                    # Verificar novamente
                                    elementos_detalhes = self.driver.find_elements(By.XPATH, "//div[@class='rich-stglpanel-body']")
                                    labels_detalhes = self.driver.find_elements(By.XPATH, "//label[contains(text(), 'Número Processo')]")
                                    print(f"Após segundo clique - rich-stglpanel-body: {len(elementos_detalhes)}, Labels: {len(labels_detalhes)}")
                            except Exception as e:
                                print(f"Erro ao tentar clicar novamente: {e}")
                    except Exception as e:
                        print(f"Erro ao verificar elementos: {e}")
                    
                    # Extrair dados do processo
                    print("Extraindo dados...")
                    dados = self._extrair_dados_processo()
                    
                    # Após extrair os dados, fechar abas extras e voltar para a aba principal
                    self._fechar_abas_extras(aba_principal)
                    
                    return {
                        'sucesso': True,
                        'numero_processo': numero_processo,
                        'dados': dados
                    }
                else:
                    print("Link do processo não encontrado")
                    return {
                        'sucesso': False,
                        'numero_processo': numero_processo,
                        'erro': 'Link do processo não encontrado na página de resultados'
                    }
                
            except TimeoutException as e:
                print(f"Timeout ao procurar link: {str(e)}")
                return {
                    'sucesso': False,
                    'numero_processo': numero_processo,
                    'erro': f'Timeout ao procurar link do processo: {str(e)}'
                }
            except Exception as e:
                print(f"Erro ao clicar no link: {str(e)}")
                print(traceback.format_exc())
                return {
                    'sucesso': False,
                    'numero_processo': numero_processo,
                    'erro': f'Erro ao acessar detalhes: {str(e)}'
                }
                
        except Exception as e:
            # Em caso de erro, também fechar abas extras
            if self.driver:
                self._fechar_abas_extras(aba_principal)
            
            error_msg = str(e)
            error_trace = traceback.format_exc()
            print(f"Erro geral no scraping: {error_msg}")
            print(error_trace)
            return {
                'sucesso': False,
                'numero_processo': numero_processo,
                'erro': error_msg,
                'traceback': error_trace
            }
        finally:
            time.sleep(DELAY_ENTRE_PROCESSOS)
    
    def _extrair_dados_processo(self) -> dict:
        """Extrai todos os dados da página de detalhes do processo"""
        dados = {}
        
        try:
            # Aguardar conteúdo principal carregar - tentar múltiplas condições
            print("Aguardando página de detalhes carregar...")
            
            # Esperar por qualquer um dos elementos que indicam que a página carregou
            try:
                WebDriverWait(self.driver, 15).until(
                    lambda driver: (
                        len(driver.find_elements(By.CLASS_NAME, "rich-stglpanel-body")) > 0 or
                        len(driver.find_elements(By.CLASS_NAME, "propertyView")) > 0 or
                        "DetalheProcesso" in driver.current_url
                    )
                )
            except TimeoutException:
                print("Timeout aguardando elementos principais, mas continuando...")
            
            print("Página carregada!")
            
            # Aguardar mais tempo para garantir que todo o JavaScript carregou
            time.sleep(3)
            
            # Rolar a página para o topo para garantir que elementos estão visíveis
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
            # Debug: Verificar quantos elementos propertyView existem
            try:
                property_views = self.driver.find_elements(By.CLASS_NAME, "propertyView")
                print(f"DEBUG: Encontrados {len(property_views)} elementos propertyView")
                
                # Listar os labels encontrados para debug
                for i, pv in enumerate(property_views[:6]):  # Primeiros 6
                    try:
                        label = pv.find_element(By.TAG_NAME, "label")
                        print(f"  - propertyView {i+1}: {label.text.strip()}")
                    except:
                        pass
            except Exception as e:
                print(f"Erro ao verificar propertyViews: {e}")
            
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
            print(traceback.format_exc())
            dados['erro_extracao'] = error_msg
        
        return dados
    
    def _extrair_dados_basicos(self) -> dict:
        """Extrai dados básicos do processo"""
        dados_basicos = {}
        
        try:
            # Primeiro, verificar se estamos na página de detalhes
            # A página de detalhes deve ter o div "rich-stglpanel-body"
            try:
                panel_body = self.driver.find_element(By.CLASS_NAME, "rich-stglpanel-body")
                print("Página de detalhes confirmada - rich-stglpanel-body encontrado")
            except:
                print("AVISO: rich-stglpanel-body não encontrado! Pode não estar na página de detalhes.")
                return dados_basicos
            
            # Aguardar um pouco mais para garantir renderização
            time.sleep(2)
            
            # Procurar todos os propertyView dentro do rich-stglpanel-body
            try:
                panel_body = self.driver.find_element(By.CLASS_NAME, "rich-stglpanel-body")
                property_views = panel_body.find_elements(By.CLASS_NAME, "propertyView")
                print(f"Total de propertyView encontrados dentro do panel: {len(property_views)}")
            except:
                # Se não encontrar dentro do panel, procurar em toda a página
                property_views = self.driver.find_elements(By.CLASS_NAME, "propertyView")
                print(f"Total de propertyView encontrados na página: {len(property_views)}")
            
            # Extrair dados de cada propertyView
            for pv in property_views:
                try:
                    # Encontrar o label
                    label_elem = pv.find_element(By.TAG_NAME, "label")
                    label_text = label_elem.text.strip()
                    
                    # Encontrar o valor
                    value_div = pv.find_element(By.XPATH, ".//div[contains(@class, 'value')]")
                    
                    # Extrair texto do valor
                    try:
                        inner_div = value_div.find_element(By.XPATH, ".//div[@class='col-sm-12']")
                        valor = inner_div.text.strip()
                    except:
                        valor = value_div.text.strip()
                    
                    # Mapear labels para campos
                    if 'Número Processo' in label_text:
                        dados_basicos['numero'] = valor
                        print(f"Número encontrado: {valor}")
                    elif 'Data da Distribuição' in label_text:
                        dados_basicos['data_distribuicao'] = valor
                        print(f"Data encontrada: {valor}")
                    elif 'Classe Judicial' in label_text:
                        dados_basicos['classe_judicial'] = valor
                        print(f"Classe encontrada: {valor}")
                    elif 'Assunto' in label_text:
                        dados_basicos['assunto'] = valor
                        print(f"Assunto encontrado: {valor}")
                    elif 'Jurisdição' in label_text:
                        dados_basicos['jurisdicao'] = valor
                        print(f"Jurisdição encontrada: {valor}")
                    elif 'Órgão Julgador' in label_text:
                        dados_basicos['orgao_julgador'] = valor
                        print(f"Órgão encontrado: {valor}")
                except Exception as e:
                    print(f"Erro ao processar propertyView: {e}")
                    continue
            
            # Garantir que todos os campos existam
            if 'numero' not in dados_basicos:
                dados_basicos['numero'] = None
            if 'data_distribuicao' not in dados_basicos:
                dados_basicos['data_distribuicao'] = None
            if 'classe_judicial' not in dados_basicos:
                dados_basicos['classe_judicial'] = None
            if 'assunto' not in dados_basicos:
                dados_basicos['assunto'] = None
            if 'jurisdicao' not in dados_basicos:
                dados_basicos['jurisdicao'] = None
            if 'orgao_julgador' not in dados_basicos:
                dados_basicos['orgao_julgador'] = None
                
        except Exception as e:
            print(f"Erro geral em dados básicos: {e}")
            print(traceback.format_exc())
            dados_basicos['erro'] = str(e)
        
        return dados_basicos
    
    def _extrair_polo_ativo(self) -> list:
        """Extrai participantes do polo ativo"""
        participantes = []
        
        try:
            print("Extraindo polo ativo...")
            
            # Aguardar o panel carregar
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//table[contains(@id, 'processoPartesPoloAtivoResumidoList')]"))
                )
            except TimeoutException:
                print("Tabela de polo ativo não encontrada")
                return participantes
            
            # Aguardar um pouco mais para garantir renderização
            time.sleep(1)
            
            # Método 1: Procurar diretamente pela tabela usando ID parcial
            try:
                tabela = self.driver.find_element(By.XPATH, "//table[contains(@id, 'processoPartesPoloAtivoResumidoList')]")
                print("Tabela de polo ativo encontrada!")
            except NoSuchElementException:
                # Método 2: Procurar pelo panel header
                try:
                    panel_header = self.driver.find_element(By.XPATH, "//div[contains(@class, 'rich-panel-header') and (contains(text(), 'Polo ativo') or contains(text(), 'Polo Ativo'))]")
                    panel = panel_header.find_element(By.XPATH, "./ancestor::div[contains(@class, 'rich-panel')]")
                    tabela = panel.find_element(By.XPATH, ".//table[contains(@id, 'processoPartesPoloAtivoResumidoList')]")
                    print("Tabela de polo ativo encontrada via panel header!")
                except:
                    print("Erro: Tabela de polo ativo não encontrada")
                    return participantes
            
            # Encontrar o tbody - pode ter ID específico ou ser apenas tbody
            try:
                tbody = tabela.find_element(By.XPATH, ".//tbody[@id[contains(., 'tb')]]")
            except:
                tbody = tabela.find_element(By.TAG_NAME, "tbody")
            
            # Encontrar todas as linhas (incluindo rich-table-firstrow)
            linhas = tbody.find_elements(By.XPATH, ".//tr[contains(@class, 'rich-table-row')]")
            print(f"Encontradas {len(linhas)} linhas no polo ativo")
            
            for linha in linhas:
                try:
                    celulas = linha.find_elements(By.TAG_NAME, "td")
                    if len(celulas) >= 1:
                        # Pegar o texto da primeira célula
                        # O texto está dentro de span.text-bold ou span normal
                        try:
                            # Tentar pegar o span com text-bold primeiro
                            span_bold = celulas[0].find_element(By.XPATH, ".//span[contains(@class, 'text-bold')]")
                            texto_completo = span_bold.text.strip()
                        except:
                            # Se não encontrar, pegar todo o texto da célula
                            texto_completo = celulas[0].text.strip()
                        
                        if not texto_completo:
                            continue
                        
                        # Extrair nome (remover CPF, CNPJ, OAB, etc. do nome principal)
                        nome = texto_completo.split(' - ')[0].strip() if ' - ' in texto_completo else texto_completo
                        
                        # Extrair CPF/CNPJ/OAB se presente
                        cpf_match = re.search(r'CPF:\s*([\d\.\-]+)', texto_completo)
                        cnpj_match = re.search(r'CNPJ:\s*([\d/\.\-]+)', texto_completo)
                        oab_match = re.search(r'OAB\s+([A-Z]{2}\d+)', texto_completo)
                        
                        # Extrair tipo (AUTOR, ADVOGADO, etc.)
                        tipo_match = re.search(r'\(([^)]+)\)', texto_completo)
                        
                        situacao = celulas[1].text.strip() if len(celulas) > 1 else "Ativo"
                        
                        participantes.append({
                            'nome': nome,
                            'nome_completo': texto_completo,
                            'situacao': situacao,
                            'cpf': cpf_match.group(1) if cpf_match else None,
                            'cnpj': cnpj_match.group(1) if cnpj_match else None,
                            'oab': oab_match.group(1) if oab_match else None,
                            'tipo': tipo_match.group(1) if tipo_match else None
                        })
                        print(f"Participante ativo extraído: {nome}")
                except Exception as e:
                    print(f"Erro ao processar linha do polo ativo: {e}")
                    continue
                    
        except Exception as e:
            print(f"Erro ao extrair polo ativo: {e}")
            print(traceback.format_exc())
        
        print(f"Total de participantes ativos extraídos: {len(participantes)}")
        return participantes
    
    def _extrair_polo_passivo(self) -> list:
        """Extrai participantes do polo passivo"""
        participantes = []
        
        try:
            print("Extraindo polo passivo...")
            
            # Aguardar o panel carregar
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//table[contains(@id, 'processoPartesPoloPassivoResumidoList')]"))
                )
            except TimeoutException:
                print("Tabela de polo passivo não encontrada")
                return participantes
            
            # Aguardar um pouco mais para garantir renderização
            time.sleep(1)
            
            # Método 1: Procurar diretamente pela tabela usando ID parcial
            try:
                tabela = self.driver.find_element(By.XPATH, "//table[contains(@id, 'processoPartesPoloPassivoResumidoList')]")
                print("Tabela de polo passivo encontrada!")
            except NoSuchElementException:
                # Método 2: Procurar pelo panel header
                try:
                    panel_header = self.driver.find_element(By.XPATH, "//div[contains(@class, 'rich-panel-header') and contains(text(), 'Polo Passivo')]")
                    panel = panel_header.find_element(By.XPATH, "./ancestor::div[contains(@class, 'rich-panel')]")
                    tabela = panel.find_element(By.XPATH, ".//table[contains(@id, 'processoPartesPoloPassivoResumidoList')]")
                    print("Tabela de polo passivo encontrada via panel header!")
                except:
                    print("Erro: Tabela de polo passivo não encontrada")
                    return participantes
            
            # Encontrar o tbody
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
                        # Pegar o texto da primeira célula
                        try:
                            # Tentar pegar o span com text-bold primeiro
                            span_bold = celulas[0].find_element(By.XPATH, ".//span[contains(@class, 'text-bold')]")
                            texto_completo = span_bold.text.strip()
                        except:
                            # Se não encontrar, pegar todo o texto da célula
                            texto_completo = celulas[0].text.strip()
                        
                        if not texto_completo:
                            continue
                        
                        # Extrair nome (remover CPF, CNPJ, etc. do nome principal)
                        nome = texto_completo.split(' - ')[0].strip() if ' - ' in texto_completo else texto_completo
                        
                        # Extrair CPF/CNPJ se presente
                        cpf_match = re.search(r'CPF:\s*([\d\.\-]+)', texto_completo)
                        cnpj_match = re.search(r'CNPJ:\s*([\d/\.\-]+)', texto_completo)
                        
                        # Extrair tipo (RÉU, etc.)
                        tipo_match = re.search(r'\(([^)]+)\)', texto_completo)
                        
                        situacao = celulas[1].text.strip() if len(celulas) > 1 else "Ativo"
                        
                        participantes.append({
                            'nome': nome,
                            'nome_completo': texto_completo,
                            'situacao': situacao,
                            'cpf': cpf_match.group(1) if cpf_match else None,
                            'cnpj': cnpj_match.group(1) if cnpj_match else None,
                            'tipo': tipo_match.group(1) if tipo_match else None
                        })
                        print(f"Participante passivo extraído: {nome}")
                except Exception as e:
                    print(f"Erro ao processar linha do polo passivo: {e}")
                    continue
                    
        except Exception as e:
            print(f"Erro ao extrair polo passivo: {e}")
            print(traceback.format_exc())
        
        print(f"Total de participantes passivos extraídos: {len(participantes)}")
        return participantes
    
    def _extrair_movimentacoes(self) -> list:
        """Extrai movimentações do processo"""
        movimentacoes = []
        
        try:
            print("Extraindo movimentações...")
            
            # Aguardar o panel carregar
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//table[contains(@id, 'processoEvento')]"))
                )
            except TimeoutException:
                print("Tabela de movimentações não encontrada")
                return movimentacoes
            
            # Aguardar um pouco mais para garantir renderização
            time.sleep(1)
            
            # Método 1: Procurar diretamente pela tabela usando ID parcial
            try:
                tabela = self.driver.find_element(By.XPATH, "//table[contains(@id, 'processoEvento')]")
                print("Tabela de movimentações encontrada!")
            except NoSuchElementException:
                # Método 2: Procurar pelo panel header
                try:
                    panel_header = self.driver.find_element(By.XPATH, "//div[contains(@class, 'rich-panel-header') and contains(text(), 'Movimentações do Processo')]")
                    panel = panel_header.find_element(By.XPATH, "./ancestor::div[contains(@class, 'rich-panel')]")
                    tabela = panel.find_element(By.XPATH, ".//table[contains(@id, 'processoEvento')]")
                    print("Tabela de movimentações encontrada via panel header!")
                except:
                    print("Erro: Tabela de movimentações não encontrada")
                    return movimentacoes
            
            # Encontrar o tbody
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
                        # Pegar o texto da primeira célula (movimento)
                        # O texto está dentro de span com id contendo j_id494
                        try:
                            # Tentar encontrar o span específico
                            span = celulas[0].find_element(By.XPATH, ".//span[@id[contains(., 'j_id')]]")
                            movimento_texto = span.text.strip()
                        except:
                            # Se não encontrar, pegar o texto do div
                            try:
                                div = celulas[0].find_element(By.XPATH, ".//div[@class='col-sm-12']")
                                movimento_texto = div.text.strip()
                            except:
                                # Último recurso: pegar todo o texto da célula
                                movimento_texto = celulas[0].text.strip()
                        
                        if not movimento_texto:
                            continue
                        
                        # Extrair data e hora se presente
                        data_match = re.search(r'(\d{2}/\d{2}/\d{4})\s+(\d{2}:\d{2}:\d{2})', movimento_texto)
                        
                        # Remover data/hora do texto do movimento para obter apenas a descrição
                        descricao = re.sub(r'\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}\s*-\s*', '', movimento_texto).strip()
                        
                        documento = celulas[1].text.strip() if len(celulas) > 1 else ""
                        
                        movimentacoes.append({
                            'movimento': movimento_texto,
                            'descricao': descricao,
                            'documento': documento,
                            'data': data_match.group(1) if data_match else None,
                            'hora': data_match.group(2) if data_match else None
                        })
                        print(f"Movimentação extraída: {descricao[:50]}...")
                except Exception as e:
                    print(f"Erro ao processar linha de movimentação: {e}")
                    continue
                    
        except Exception as e:
            print(f"Erro ao extrair movimentações: {e}")
            print(traceback.format_exc())
        
        print(f"Total de movimentações extraídas: {len(movimentacoes)}")
        return movimentacoes
    
    def _extrair_documentos(self) -> list:
        """Extrai documentos juntados ao processo"""
        documentos = []
        
        try:
            # Procurar pela tabela de documentos
            tabela = None
            
            # Método 1: Procurar pelo ID que contém "processoDocumento"
            try:
                tabela = self.driver.find_element(By.XPATH, "//table[contains(@id, 'processoDocumento')]")
                print("Tabela de documentos encontrada por ID")
            except:
                # Método 2: Procurar pela div que contém "Documento" no header
                try:
                    header = self.driver.find_element(By.XPATH, "//th[contains(text(), 'Documento')]")
                    tabela = header.find_element(By.XPATH, "./ancestor::table")
                    print("Tabela de documentos encontrada por header")
                except:
                    pass
            
            if tabela:
                # Encontrar o tbody
                tbody = tabela.find_element(By.XPATH, ".//tbody[@id]")
                linhas = tbody.find_elements(By.TAG_NAME, "tr")
                
                for linha in linhas:
                    try:
                        celulas = linha.find_elements(By.TAG_NAME, "td")
                        if len(celulas) >= 1:
                            documento = celulas[0].text.strip()
                            certidao = celulas[1].text.strip() if len(celulas) > 1 else ""
                            
                            documentos.append({
                                'documento': documento,
                                'certidao': certidao
                            })
                            print(f"Documento extraído: {documento[:50]}...")
                    except Exception as e:
                        print(f"Erro ao processar linha de documento: {e}")
                        continue
            else:
                print("Tabela de documentos não encontrada (pode não haver documentos)")
                    
        except Exception as e:
            print(f"Erro ao extrair documentos: {e}")
            # Não adicionar erro se não houver documentos (é normal)
            if "não encontrada" not in str(e).lower():
                documentos.append({'erro': str(e)})
        
        return documentos
    
    def _fechar_abas_extras(self, aba_principal=None):
        """Fecha todas as abas extras, mantendo apenas a aba principal"""
        if not self.driver:
            return
        
        try:
            # Se não especificou aba principal, usar a primeira
            if aba_principal is None and self.driver.window_handles:
                aba_principal = self.driver.window_handles[0]
            
            # Fechar todas as outras abas
            for handle in self.driver.window_handles:
                if handle != aba_principal:
                    try:
                        self.driver.switch_to.window(handle)
                        self.driver.close()
                        print(f"Aba extra fechada: {handle}")
                    except Exception as e:
                        print(f"Erro ao fechar aba {handle}: {e}")
            
            # Voltar para a aba principal
            if aba_principal and aba_principal in self.driver.window_handles:
                self.driver.switch_to.window(aba_principal)
                print("Voltou para a aba principal")
        except Exception as e:
            print(f"Erro ao fechar abas extras: {e}")
    
    def fechar_todas_abas(self):
        """Fecha todas as abas do navegador"""
        if not self.driver:
            return
        
        try:
            # Fechar todas as abas
            handles = list(self.driver.window_handles)
            for handle in handles:
                try:
                    self.driver.switch_to.window(handle)
                    self.driver.close()
                    print(f"Aba fechada: {handle}")
                except Exception as e:
                    print(f"Erro ao fechar aba {handle}: {e}")
        except Exception as e:
            print(f"Erro ao fechar todas as abas: {e}")
