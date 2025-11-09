from scrapers.base import BaseScraper
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from config.settings import CHROME_DRIVER_PATH, CHROME_USER_DATA_DIR, CHROME_PROFILE_DIRECTORY, DELAY_ENTRE_PROCESSOS, HEADLESS_MODE
import time
import re
import traceback

class PJeScraperTJPE(BaseScraper):
    
    def __init__(self, config):
        super().__init__(config)
        self.url_consulta = config.get('url_consulta', 'https://pje.cloud.tjpe.jus.br/1g/ConsultaPublica/listView.seam')
        self.headless = config.get('headless', False)
    
    def setup_driver(self):
        """Configura o driver do Chrome"""
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        
        try:
            chrome_options = Options()
            
            use_headless = self.headless or HEADLESS_MODE
            
            if use_headless:
                chrome_options.add_argument("--headless")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_argument("--window-size=1920,1080")
                chrome_options.add_argument("--start-maximized")
                chrome_options.add_argument("--disable-extensions")
                print("Modo headless ativado")
            else:
                if CHROME_USER_DATA_DIR:
                    chrome_options.add_argument(f"--user-data-dir={CHROME_USER_DATA_DIR}")
                    chrome_options.add_argument(f"--profile-directory={CHROME_PROFILE_DIRECTORY}")
                chrome_options.add_experimental_option("detach", True)
            
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            if CHROME_DRIVER_PATH:
                service = Service(CHROME_DRIVER_PATH)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
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
            print(f"Acessando: {self.url_consulta}")
            self.driver.get(self.url_consulta)
            time.sleep(3)
            
            campo_processo_id = "fPP:numProcesso-inputNumeroProcessoDecoration:numProcesso-inputNumeroProcesso"
            print(f"Procurando campo: {campo_processo_id}")
            
            try:
                campo_processo = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.ID, campo_processo_id))
                )
                print("Campo encontrado!")
            except TimeoutException:
                print("Campo não encontrado! Tentando alternativa...")
                try:
                    campo_processo = self.driver.find_element(By.NAME, campo_processo_id)
                except:
                    error_trace = traceback.format_exc()
                    print(f"Erro completo ao encontrar campo: {error_trace}")
                    self._fechar_abas_extras(aba_principal)
                    return {
                        'sucesso': False,
                        'numero_processo': numero_processo,
                        'erro': 'Não foi possível localizar o campo de busca na página'
                    }
            
            campo_processo.clear()
            campo_processo.send_keys(numero_processo)
            print(f"Número do processo inserido: {numero_processo}")
            time.sleep(1)
            
            try:
                botao_buscar = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//input[@type='submit' or @value='Buscar' or contains(@class, 'btn')]"))
                )
                botao_buscar.click()
                print("Botão buscar clicado!")
            except TimeoutException:
                campo_processo.send_keys(Keys.RETURN)
                print("Pressionado Enter para buscar")
            
            time.sleep(3)
            
            print("Procurando link do processo...")
            try:
                link_xpath = f"//a[contains(@onclick, 'openPopUp')]//b[contains(@class, 'btn-block') and contains(text(), '{numero_processo}')]"
                link_processo = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, link_xpath))
                )
                print("Link do processo encontrado!")
            except TimeoutException:
                link_xpath = f"//b[@class='btn-block' and contains(text(), '{numero_processo}')]"
                try:
                    link_processo = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, link_xpath))
                    )
                    print("Link encontrado por alternativa!")
                except:
                    error_trace = traceback.format_exc()
                    print(f"Erro completo ao encontrar link: {error_trace}")
                    self._fechar_abas_extras(aba_principal)
                    return {
                        'sucesso': False,
                        'numero_processo': numero_processo,
                        'erro': 'Processo não encontrado na lista de resultados'
                    }
            
            url_antes = self.driver.current_url
            print(f"URL antes do clique: {url_antes}")
            
            try:
                link_processo.click()
                print("Link clicado normalmente!")
            except:
                self.driver.execute_script("arguments[0].click();", link_processo)
                print("Link clicado via JavaScript!")
            
            time.sleep(2)
            
            abas_apos = self.driver.window_handles
            if len(abas_apos) > len([aba_principal]):
                print(f"Abriu nova aba! Total de abas: {len(abas_apos)}")
                nova_aba = [aba for aba in abas_apos if aba != aba_principal][0]
                self.driver.switch_to.window(nova_aba)
                print("Mudado para nova aba")
                time.sleep(3)
            else:
                print("Aguardando página de detalhes carregar...")
                try:
                    WebDriverWait(self.driver, 15).until(
                        lambda driver: (
                            "DetalheProcessoConsultaPublica" in driver.current_url or
                            len(driver.find_elements(By.CLASS_NAME, "rich-stglpanel-body")) > 0 or
                            len(driver.find_elements(By.CLASS_NAME, "propertyView")) > 0
                        )
                    )
                    print(f"URL após clique: {self.driver.current_url}")
                except TimeoutException:
                    print("Timeout aguardando página de detalhes, mas continuando...")
                
                time.sleep(3)
            
            url_atual = self.driver.current_url
            print(f"URL atual: {url_atual}")
            
            try:
                elementos_property = self.driver.find_elements(By.CLASS_NAME, "propertyView")
                print(f"Encontrados {len(elementos_property)} elementos propertyView na página")
                
                if len(elementos_property) == 0:
                    print("AVISO: Nenhum elemento propertyView encontrado! Aguardando mais...")
                    time.sleep(3)
                    elementos_property = self.driver.find_elements(By.CLASS_NAME, "propertyView")
                    print(f"Após espera adicional: {len(elementos_property)} elementos propertyView")
            except Exception as e:
                print(f"Erro ao verificar elementos: {e}")
            
            print("Extraindo dados...")
            dados = self._extrair_dados_processo()
            
            self._fechar_abas_extras(aba_principal)
            
            return {
                'sucesso': True,
                'numero_processo': numero_processo,
                'dados': dados
            }
            
        except Exception as e:
            error_trace = traceback.format_exc()
            print(f"Erro completo ao raspar processo {numero_processo}:")
            print(error_trace)
            
            self._fechar_abas_extras(aba_principal)
            
            mensagem_amigavel = self._obter_mensagem_amigavel(e)
            
            return {
                'sucesso': False,
                'numero_processo': numero_processo,
                'erro': mensagem_amigavel
            }
    
    def _fechar_abas_extras(self, aba_principal=None):
        try:
            if not self.driver:
                return
            
            if aba_principal is None and self.driver.window_handles:
                aba_principal = self.driver.window_handles[0]
            
            abas_atuais = self.driver.window_handles
            if len(abas_atuais) > 1 and aba_principal:
                for aba in abas_atuais:
                    if aba != aba_principal:
                        self.driver.switch_to.window(aba)
                        self.driver.close()
                
                if aba_principal in self.driver.window_handles:
                    self.driver.switch_to.window(aba_principal)
                    print("Fechadas abas extras, voltado para aba principal")
        except Exception as e:
            print(f"Erro ao fechar abas extras: {e}")
    
    def fechar_todas_abas(self):
        if not self.driver:
            return
        
        try:
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
    
    def _extrair_dados_processo(self) -> dict:
        dados = {}
        
        try:
            print("Aguardando página de detalhes carregar...")
            
            try:
                WebDriverWait(self.driver, 15).until(
                    lambda driver: (
                        len(driver.find_elements(By.CLASS_NAME, "rich-stglpanel-body")) > 0 or
                        len(driver.find_elements(By.CLASS_NAME, "propertyView")) > 0 or
                        "DetalheProcessoConsultaPublica" in driver.current_url
                    )
                )
            except TimeoutException:
                print("Timeout aguardando elementos principais, mas continuando...")
            
            print("Página carregada!")
            time.sleep(3)
            
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
            try:
                property_views = self.driver.find_elements(By.CLASS_NAME, "propertyView")
                print(f"DEBUG: Encontrados {len(property_views)} elementos propertyView")
            except Exception as e:
                print(f"Erro ao verificar propertyViews: {e}")
            
            dados['dados_processo'] = self._extrair_dados_basicos()
            dados['polo_ativo'] = self._extrair_polo_ativo()
            dados['polo_passivo'] = self._extrair_polo_passivo()
            dados['movimentacoes'] = self._extrair_movimentacoes()
            dados['documentos'] = self._extrair_documentos()
            
            print("Dados extraídos com sucesso!")
            
        except Exception as e:
            error_msg = str(e)
            print(f"Erro ao extrair dados: {error_msg}")
            print(traceback.format_exc())
            dados['erro_extracao'] = error_msg
        
        return dados
    
    def _extrair_dados_basicos(self) -> dict:
        dados_basicos = {}
        
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "rich-stglpanel-body"))
            )
            time.sleep(1)
            
            try:
                label = self.driver.find_element(By.XPATH, "//label[contains(text(), 'Número Processo')]")
                property_view = label.find_element(By.XPATH, "./ancestor::div[contains(@class, 'propertyView')]")
                value_div = property_view.find_element(By.XPATH, ".//div[contains(@class, 'value') and contains(@class, 'col-sm-12')]")
                try:
                    inner_div = value_div.find_element(By.XPATH, ".//div[contains(@class, 'col-sm-12')]")
                    dados_basicos['numero'] = inner_div.text.strip()
                except:
                    dados_basicos['numero'] = value_div.text.strip()
                print(f"Número encontrado: {dados_basicos['numero']}")
            except Exception as e:
                print(f"Erro ao extrair número: {e}")
                dados_basicos['numero'] = None
            
            try:
                label = self.driver.find_element(By.XPATH, "//label[contains(text(), 'Data da Distribuição')]")
                property_view = label.find_element(By.XPATH, "./ancestor::div[contains(@class, 'propertyView')]")
                value_div = property_view.find_element(By.XPATH, ".//div[contains(@class, 'value') and contains(@class, 'col-sm-12')]")
                texto_data = value_div.text.strip()
                dados_basicos['data_distribuicao'] = ' '.join(texto_data.split())
                print(f"Data encontrada: {dados_basicos['data_distribuicao']}")
            except Exception as e:
                print(f"Erro ao extrair data: {e}")
                print(traceback.format_exc())
                dados_basicos['data_distribuicao'] = None
            
            try:
                label = self.driver.find_element(By.XPATH, "//label[contains(text(), 'Classe Judicial')]")
                property_view = label.find_element(By.XPATH, "./ancestor::div[contains(@class, 'propertyView')]")
                value_div = property_view.find_element(By.XPATH, ".//div[contains(@class, 'value') and contains(@class, 'col-sm-12')]")
                texto_classe = value_div.text.strip()
                dados_basicos['classe_judicial'] = ' '.join(texto_classe.split())
                print(f"Classe encontrada: {dados_basicos['classe_judicial']}")
            except Exception as e:
                print(f"Erro ao extrair classe: {e}")
                dados_basicos['classe_judicial'] = None
            
            try:
                label = self.driver.find_element(By.XPATH, "//label[contains(text(), 'Assunto')]")
                property_view = label.find_element(By.XPATH, "./ancestor::div[contains(@class, 'propertyView')]")
                value_div = property_view.find_element(By.XPATH, ".//div[contains(@class, 'value') and contains(@class, 'col-sm-12')]")
                try:
                    inner_div = value_div.find_element(By.XPATH, ".//div[contains(@class, 'col-sm-12')]")
                    dados_basicos['assunto'] = inner_div.text.strip()
                except:
                    dados_basicos['assunto'] = value_div.text.strip()
                dados_basicos['assunto'] = ' '.join(dados_basicos['assunto'].split())
                print(f"Assunto encontrado: {dados_basicos['assunto']}")
            except Exception as e:
                print(f"Erro ao extrair assunto: {e}")
                dados_basicos['assunto'] = None
            
            try:
                label = self.driver.find_element(By.XPATH, "//label[contains(text(), 'Jurisdição')]")
                property_view = label.find_element(By.XPATH, "./ancestor::div[contains(@class, 'propertyView')]")
                value_div = property_view.find_element(By.XPATH, ".//div[contains(@class, 'value') and contains(@class, 'col-sm-12')]")
                texto_jurisdicao = value_div.text.strip()
                dados_basicos['jurisdicao'] = ' '.join(texto_jurisdicao.split())
                print(f"Jurisdição encontrada: {dados_basicos['jurisdicao']}")
            except Exception as e:
                print(f"Erro ao extrair jurisdição: {e}")
                dados_basicos['jurisdicao'] = None
            
            try:
                label = self.driver.find_element(By.XPATH, "//label[contains(text(), 'Órgão Julgador')]")
                property_view = label.find_element(By.XPATH, "./ancestor::div[contains(@class, 'propertyView')]")
                value_div = property_view.find_element(By.XPATH, ".//div[contains(@class, 'value') and contains(@class, 'col-sm-12')]")
                texto_orgao = value_div.text.strip()
                dados_basicos['orgao_julgador'] = ' '.join(texto_orgao.split())
                print(f"Órgão encontrado: {dados_basicos['orgao_julgador']}")
            except Exception as e:
                print(f"Erro ao extrair órgão: {e}")
                dados_basicos['orgao_julgador'] = None
                
        except Exception as e:
            print(f"Erro geral em dados básicos: {e}")
            dados_basicos['erro'] = str(e)
        
        return dados_basicos
    
    def _extrair_polo_ativo(self) -> list:
        polo_ativo = []
        
        try:
            print("Procurando polo ativo...")
            
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'rich-panel-header') and contains(text(), 'Polo ativo')]"))
                )
            except TimeoutException:
                print("Painel polo ativo não encontrado")
                return polo_ativo
            try:
                # Procurar tabela com ID que contém "processoPartesPoloAtivoResumidoList"
                tabela = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//table[contains(@id, 'processoPartesPoloAtivoResumidoList')]"))
                )
                
                tbody = tabela.find_element(By.XPATH, ".//tbody[@id]")
                linhas = tbody.find_elements(By.XPATH, ".//tr[contains(@class, 'rich-table-row')]")
                
                print(f"Encontradas {len(linhas)} linhas no polo ativo")
                
                for linha in linhas:
                    try:
                        nome_element = linha.find_element(By.XPATH, ".//span[contains(@class, 'text-bold')]")
                        nome = nome_element.text.strip()
                        cpf_cnpj = None
                        texto_completo = linha.text
                        match_cpf = re.search(r'CPF:\s*([\d\.\-/]+)', texto_completo)
                        match_cnpj = re.search(r'CNPJ:\s*([\d\.\-/]+)', texto_completo)
                        
                        if match_cnpj:
                            cpf_cnpj = match_cnpj.group(1)
                        elif match_cpf:
                            cpf_cnpj = match_cpf.group(1)
                        
                        polo_ativo.append({
                            'nome': nome,
                            'cpf_cnpj': cpf_cnpj,
                            'tipo': 'Ativo'
                        })
                        print(f"  - Polo ativo: {nome}")
                    except Exception as e:
                        print(f"Erro ao extrair linha do polo ativo: {e}")
                        continue
                        
            except Exception as e:
                print(f"Erro ao extrair tabela do polo ativo: {e}")
                
        except Exception as e:
            print(f"Erro geral ao extrair polo ativo: {e}")
        
        return polo_ativo
    
    def _extrair_polo_passivo(self) -> list:
        polo_passivo = []
        
        try:
            print("Procurando polo passivo...")
            
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'rich-panel-header') and contains(text(), 'Polo Passivo')]"))
                )
            except TimeoutException:
                print("Painel polo passivo não encontrado")
                return polo_passivo
            
            try:
                tabela = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//table[contains(@id, 'processoPartesPoloPassivoResumidoList')]"))
                )
                
                tbody = tabela.find_element(By.XPATH, ".//tbody[@id]")
                linhas = tbody.find_elements(By.XPATH, ".//tr[contains(@class, 'rich-table-row')]")
                
                print(f"Encontradas {len(linhas)} linhas no polo passivo")
                
                for linha in linhas:
                    try:
                        nome_element = linha.find_element(By.XPATH, ".//span[contains(@class, 'text-bold')]")
                        nome = nome_element.text.strip()
                        
                        cpf_cnpj = None
                        texto_completo = linha.text
                        match_cpf = re.search(r'CPF:\s*([\d\.\-/]+)', texto_completo)
                        match_cnpj = re.search(r'CNPJ:\s*([\d\.\-/]+)', texto_completo)
                        
                        if match_cnpj:
                            cpf_cnpj = match_cnpj.group(1)
                        elif match_cpf:
                            cpf_cnpj = match_cpf.group(1)
                        
                        polo_passivo.append({
                            'nome': nome,
                            'cpf_cnpj': cpf_cnpj,
                            'tipo': 'Passivo'
                        })
                        print(f"  - Polo passivo: {nome}")
                    except Exception as e:
                        print(f"Erro ao extrair linha do polo passivo: {e}")
                        continue
                        
            except Exception as e:
                print(f"Erro ao extrair tabela do polo passivo: {e}")
                
        except Exception as e:
            print(f"Erro geral ao extrair polo passivo: {e}")
        
        return polo_passivo
    
    def _extrair_movimentacoes(self) -> list:
        movimentacoes = []
        
        try:
            print("Procurando movimentações...")
            
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'rich-panel-header') and contains(text(), 'Movimentações do Processo')]"))
                )
            except TimeoutException:
                print("Painel de movimentações não encontrado")
                return movimentacoes
            
            try:
                tabela = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//table[contains(@id, 'processoEvento')]"))
                )
                
                tbody = tabela.find_element(By.XPATH, ".//tbody[@id]")
                linhas = tbody.find_elements(By.XPATH, ".//tr[contains(@class, 'rich-table-row')]")
                
                print(f"Encontradas {len(linhas)} movimentações")
                
                for linha in linhas:
                    try:
                        movimento_element = linha.find_element(By.XPATH, ".//td[contains(@class, 'text-break')]//span")
                        movimento = movimento_element.text.strip()
                        movimentacoes.append({
                            'movimento': movimento,
                            'data': None  
                        })
                        print(f"  - Movimentação: {movimento[:50]}...")
                    except Exception as e:
                        print(f"Erro ao extrair movimentação: {e}")
                        continue
                        
            except Exception as e:
                print(f"Erro ao extrair tabela de movimentações: {e}")
                
        except Exception as e:
            print(f"Erro geral ao extrair movimentações: {e}")
        
        return movimentacoes
    
    def _extrair_documentos(self) -> list:
        documentos = []
        
        try:
            tabela = self.driver.find_element(By.XPATH, "//table[contains(@id, 'processoEvento')]")
            tbody = tabela.find_element(By.XPATH, ".//tbody[@id]")
            linhas = tbody.find_elements(By.XPATH, ".//tr[contains(@class, 'rich-table-row')]")
            for linha in linhas:
                try:
                    doc_cell = linha.find_elements(By.XPATH, ".//td[2]//a")
                    if doc_cell:
                        doc_link = doc_cell[0]
                        doc_texto = doc_link.text.strip()
                        doc_url = doc_link.get_attribute('href')
                        
                        documentos.append({
                            'nome': doc_texto,
                            'url': doc_url
                        })
                except:
                    continue
                    
        except Exception as e:
            print(f"Erro ao extrair documentos: {e}")
        
        return documentos
    
    def close(self):
        if self.driver:
            try:
                self.driver.quit()
                print("Driver fechado com sucesso")
            except:
                pass
