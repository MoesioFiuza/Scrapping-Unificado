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

class PJeScraperTJCE(BaseScraper):
    
    def __init__(self, config):
        super().__init__(config)
        self.url_consulta = config.get('url_consulta', 'https://pje-consulta.tjce.jus.br/pje1grau/ConsultaPublica/listView.seam')
        self.headless = config.get('headless', False)
    
    def setup_driver(self):
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
                campo_processo = self.driver.find_element(By.NAME, campo_processo_id)
            
            campo_processo.clear()
            campo_processo.send_keys(numero_processo)
            print(f"Número do processo preenchido: {numero_processo}")
            campo_processo.send_keys(Keys.RETURN)
            
            print("Aguardando resultados...")
            time.sleep(5)
            try:
                print("Procurando link do processo...")
                
                xpath_options = [
                    f"//b[@class='btn-block' and contains(text(), '{numero_processo}')]",
                    f"//a[contains(@onclick, 'openPopUp')]//b[contains(text(), '{numero_processo}')]",
                    f"//a[contains(@onclick, 'DetalheProcesso')]//b[contains(text(), '{numero_processo}')]",
                    f"//b[contains(text(), '{numero_processo.split('-')[0]}')]",
                    f"//a[contains(text(), '{numero_processo}')]",
                    f"//*[contains(text(), '{numero_processo}')]"
                ]
                
                link_processo = None
                for xpath in xpath_options:
                    try:
                        elemento = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, xpath))
                        )
                        if elemento.tag_name == 'b':
                            link_processo = elemento.find_element(By.XPATH, "./ancestor::a")
                        else:
                            link_processo = elemento
                        print(f"Link encontrado com XPath: {xpath}")
                        break
                    except TimeoutException:
                        continue
                
                if not link_processo:
                    try:
                        tabela_resultados = self.driver.find_element(By.XPATH, "//table[contains(@class, 'rich-table')]")
                        link_processo = tabela_resultados.find_element(By.XPATH, ".//a[contains(@onclick, 'openPopUp')]")
                        print("Link encontrado na tabela")
                    except:
                        pass
                
                if link_processo:
                    url_antes = self.driver.current_url
                    print(f"URL antes do clique: {url_antes}")
                    try:
                        link_processo.click()
                        print("Link clicado (método normal)!")
                    except:
                        try:
                            self.driver.execute_script("arguments[0].click();", link_processo)
                            print("Link clicado (método JavaScript)!")
                        except:
                            try:
                                onclick = link_processo.get_attribute('onclick')
                                if onclick:
                                    import re
                                    url_match = re.search(r"openPopUp\('.*?','([^']+)'\)", onclick)
                                    if url_match:
                                        url_detalhes = url_match.group(1)
                                        if not url_detalhes.startswith('http'):
                                            url_detalhes = f"https://pje-consulta.tjce.jus.br{url_detalhes}"
                                        self.driver.get(url_detalhes)
                                        print(f"Navegando diretamente para: {url_detalhes}")
                            except Exception as e:
                                print(f"Erro ao extrair URL do onclick: {e}")
                    
                    time.sleep(2)
                    if len(self.driver.window_handles) > 1:
                        print("Nova aba/popup detectada! Mudando para a nova aba...")
                        self.driver.switch_to.window(self.driver.window_handles[-1])
                        print("Mudado para nova aba")
                    
                    print("Aguardando página de detalhes carregar...")
                    try:
                        WebDriverWait(self.driver, 15).until(
                            lambda driver: (
                                "DetalheProcesso" in driver.current_url or
                                driver.current_url != url_antes or
                                len(driver.find_elements(By.CLASS_NAME, "rich-stglpanel-body")) > 0
                            )
                        )
                        print(f"URL mudou para: {self.driver.current_url}")
                    except TimeoutException:
                        print("URL não mudou, mas verificando se conteúdo carregou via AJAX...")
                    
                    time.sleep(5)
                    
                    print("Extraindo dados...")
                    dados = self._extrair_dados_processo()
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
        dados = {}
        
        try:
            print("Aguardando página de detalhes carregar...")
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
            time.sleep(3)
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
            dados['dados_processo'] = self._extrair_dados_basicos()
            dados['polo_ativo'] = self._extrair_polo_ativo()
            dados['polo_passivo'] = self._extrair_polo_passivo()
            dados['outros_interessados'] = self._extrair_outros_interessados()
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
            try:
                panel_body = self.driver.find_element(By.CLASS_NAME, "rich-stglpanel-body")
                print("Página de detalhes confirmada - rich-stglpanel-body encontrado")
            except:
                print("AVISO: rich-stglpanel-body não encontrado! Pode não estar na página de detalhes.")
                return dados_basicos
            
            time.sleep(2)
            
            try:
                panel_body = self.driver.find_element(By.CLASS_NAME, "rich-stglpanel-body")
                property_views = panel_body.find_elements(By.CLASS_NAME, "propertyView")
                print(f"Total de propertyView encontrados dentro do panel: {len(property_views)}")
            except:
                property_views = self.driver.find_elements(By.CLASS_NAME, "propertyView")
                print(f"Total de propertyView encontrados na página: {len(property_views)}")
            
            for pv in property_views:
                try:
                    label_elem = pv.find_element(By.TAG_NAME, "label")
                    label_text = label_elem.text.strip()
                    
                    if not label_text:  
                        continue
                    
                    value_div = pv.find_element(By.XPATH, ".//div[contains(@class, 'value')]")
                    
                    try:
                        inner_div = value_div.find_element(By.XPATH, ".//div[@class='col-sm-12']")
                        valor = inner_div.text.strip()
                    except:
                        valor = value_div.text.strip()
                    
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
            
            campos = ['numero', 'data_distribuicao', 'classe_judicial', 'assunto', 'jurisdicao', 'orgao_julgador']
            for campo in campos:
                if campo not in dados_basicos:
                    dados_basicos[campo] = None
                    
        except Exception as e:
            print(f"Erro geral em dados básicos: {e}")
            print(traceback.format_exc())
            dados_basicos['erro'] = str(e)
        
        return dados_basicos
    
    def _extrair_polo_ativo(self) -> list:
        participantes = []
        
        try:
            print("Extraindo polo ativo...")
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//table[contains(@id, 'processoPartesPoloAtivoResumidoList')]"))
                )
            except TimeoutException:
                print("Tabela de polo ativo não encontrada")
                return participantes
            
            time.sleep(1)
            
            try:
                tabela = self.driver.find_element(By.XPATH, "//table[contains(@id, 'processoPartesPoloAtivoResumidoList')]")
                print("Tabela de polo ativo encontrada!")
            except NoSuchElementException:
                try:
                    panel_header = self.driver.find_element(By.XPATH, "//div[contains(@class, 'rich-panel-header') and (contains(text(), 'Polo ativo') or contains(text(), 'Polo Ativo'))]")
                    panel = panel_header.find_element(By.XPATH, "./ancestor::div[contains(@class, 'rich-panel')]")
                    tabela = panel.find_element(By.XPATH, ".//table[contains(@id, 'processoPartesPoloAtivoResumidoList')]")
                    print("Tabela de polo ativo encontrada via panel header!")
                except:
                    print("Erro: Tabela de polo ativo não encontrada")
                    return participantes
            
            try:
                tbody = tabela.find_element(By.XPATH, ".//tbody[@id[contains(., 'tb')]]")
            except:
                tbody = tabela.find_element(By.TAG_NAME, "tbody")
            
            linhas = tbody.find_elements(By.XPATH, ".//tr[contains(@class, 'rich-table-row')]")
            print(f"Encontradas {len(linhas)} linhas no polo ativo")
            
            for linha in linhas:
                try:
                    celulas = linha.find_elements(By.TAG_NAME, "td")
                    if len(celulas) >= 1:
                        try:
                            span_bold = celulas[0].find_element(By.XPATH, ".//span[contains(@class, 'text-bold')]")
                            texto_completo = span_bold.text.strip()
                        except:
                            texto_completo = celulas[0].text.strip()
                        
                        if not texto_completo:
                            continue
                        
                        nome = texto_completo.split(' - ')[0].strip() if ' - ' in texto_completo else texto_completo
                        
                        cpf_match = re.search(r'CPF:\s*([\d\.\-]+)', texto_completo)
                        cnpj_match = re.search(r'CNPJ:\s*([\d/\.\-]+)', texto_completo)
                        oab_match = re.search(r'OAB\s+([A-Z]{2}\d+[A-Z]?)', texto_completo)
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
        participantes = []
        
        try:
            print("Extraindo polo passivo...")
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//table[contains(@id, 'processoPartesPoloPassivoResumidoList')]"))
                )
            except TimeoutException:
                print("Tabela de polo passivo não encontrada")
                return participantes
            
            time.sleep(1)
            
            try:
                tabela = self.driver.find_element(By.XPATH, "//table[contains(@id, 'processoPartesPoloPassivoResumidoList')]")
                print("Tabela de polo passivo encontrada!")
            except NoSuchElementException:
                try:
                    panel_header = self.driver.find_element(By.XPATH, "//div[contains(@class, 'rich-panel-header') and contains(text(), 'Polo Passivo')]")
                    panel = panel_header.find_element(By.XPATH, "./ancestor::div[contains(@class, 'rich-panel')]")
                    tabela = panel.find_element(By.XPATH, ".//table[contains(@id, 'processoPartesPoloPassivoResumidoList')]")
                    print("Tabela de polo passivo encontrada via panel header!")
                except:
                    print("Erro: Tabela de polo passivo não encontrada")
                    return participantes
            
            try:
                tbody = tabela.find_element(By.XPATH, ".//tbody[@id[contains(., 'tb')]]")
            except:
                tbody = tabela.find_element(By.TAG_NAME, "tbody")
            
            linhas = tbody.find_elements(By.XPATH, ".//tr[contains(@class, 'rich-table-row')]")
            print(f"Encontradas {len(linhas)} linhas no polo passivo")
            
            for linha in linhas:
                try:
                    celulas = linha.find_elements(By.TAG_NAME, "td")
                    if len(celulas) >= 1:
                        try:
                            span_bold = celulas[0].find_element(By.XPATH, ".//span[contains(@class, 'text-bold')]")
                            texto_completo = span_bold.text.strip()
                        except:
                            texto_completo = celulas[0].text.strip()
                        
                        if not texto_completo:
                            continue
                        
                        nome = texto_completo.split(' - ')[0].strip() if ' - ' in texto_completo else texto_completo
                        
                        cpf_match = re.search(r'CPF:\s*([\d\.\-]+)', texto_completo)
                        cnpj_match = re.search(r'CNPJ:\s*([\d/\.\-]+)', texto_completo)
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
    
    def _extrair_outros_interessados(self) -> list:
        participantes = []
        
        try:
            print("Extraindo outros interessados...")
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//table[contains(@id, 'processoParteOutrosInteressadosResumidoList')]"))
                )
            except TimeoutException:
                print("Tabela de outros interessados não encontrada (pode não existir)")
                return participantes
            
            time.sleep(1)
            
            try:
                tabela = self.driver.find_element(By.XPATH, "//table[contains(@id, 'processoParteOutrosInteressadosResumidoList')]")
                print("Tabela de outros interessados encontrada!")
            except NoSuchElementException:
                return participantes
            
            try:
                tbody = tabela.find_element(By.XPATH, ".//tbody[@id[contains(., 'tb')]]")
            except:
                tbody = tabela.find_element(By.TAG_NAME, "tbody")
            
            linhas = tbody.find_elements(By.XPATH, ".//tr[contains(@class, 'rich-table-row')]")
            print(f"Encontradas {len(linhas)} linhas de outros interessados")
            
            for linha in linhas:
                try:
                    celulas = linha.find_elements(By.TAG_NAME, "td")
                    if len(celulas) >= 1:
                        try:
                            span_bold = celulas[0].find_element(By.XPATH, ".//span[contains(@class, 'text-bold')]")
                            texto_completo = span_bold.text.strip()
                        except:
                            texto_completo = celulas[0].text.strip()
                        
                        if not texto_completo:
                            continue
                        
                        nome = texto_completo.split(' - ')[0].strip() if ' - ' in texto_completo else texto_completo
                        
                        cpf_match = re.search(r'CPF:\s*([\d\.\-]+)', texto_completo)
                        cnpj_match = re.search(r'CNPJ:\s*([\d/\.\-]+)', texto_completo)
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
                        print(f"Outro interessado extraído: {nome}")
                except Exception as e:
                    print(f"Erro ao processar linha de outro interessado: {e}")
                    continue
                    
        except Exception as e:
            print(f"Erro ao extrair outros interessados: {e}")
            print(traceback.format_exc())
        
        print(f"Total de outros interessados extraídos: {len(participantes)}")
        return participantes
    
    def _extrair_movimentacoes(self) -> list:
        movimentacoes = []
        
        try:
            print("Extraindo movimentações...")
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//table[contains(@id, 'processoEvento')]"))
                )
            except TimeoutException:
                print("Tabela de movimentações não encontrada")
                return movimentacoes
            
            time.sleep(1)
            
            try:
                tabela = self.driver.find_element(By.XPATH, "//table[contains(@id, 'processoEvento')]")
                print("Tabela de movimentações encontrada!")
            except NoSuchElementException:
                try:
                    panel_header = self.driver.find_element(By.XPATH, "//div[contains(@class, 'rich-panel-header') and contains(text(), 'Movimentações do Processo')]")
                    panel = panel_header.find_element(By.XPATH, "./ancestor::div[contains(@class, 'rich-panel')]")
                    tabela = panel.find_element(By.XPATH, ".//table[contains(@id, 'processoEvento')]")
                    print("Tabela de movimentações encontrada via panel header!")
                except:
                    print("Erro: Tabela de movimentações não encontrada")
                    return movimentacoes
            
            try:
                tbody = tabela.find_element(By.XPATH, ".//tbody[@id[contains(., 'tb')]]")
            except:
                tbody = tabela.find_element(By.TAG_NAME, "tbody")
            
            linhas = tbody.find_elements(By.XPATH, ".//tr[contains(@class, 'rich-table-row')]")
            print(f"Encontradas {len(linhas)} linhas de movimentações")
            
            for linha in linhas:
                try:
                    celulas = linha.find_elements(By.TAG_NAME, "td")
                    if len(celulas) >= 1:
                        try:
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
                        
                        data_match = re.search(r'(\d{2}/\d{2}/\d{4})\s+(\d{2}:\d{2}:\d{2})', movimento_texto)
                        descricao = re.sub(r'\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}\s*-\s*', '', movimento_texto).strip()
                        
                        documento = ""
                        if len(celulas) > 1:
                            try:
                                doc_link = celulas[1].find_element(By.TAG_NAME, "a")
                                documento = doc_link.text.strip()
                            except:
                                documento = celulas[1].text.strip()
                        
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
        documentos = []
        
        try:
            tabela = None
            try:
                tabela = self.driver.find_element(By.XPATH, "//table[contains(@id, 'processoDocumento')]")
                print("Tabela de documentos encontrada por ID")
            except:
                try:
                    header = self.driver.find_element(By.XPATH, "//th[contains(text(), 'Documento')]")
                    tabela = header.find_element(By.XPATH, "./ancestor::table")
                    print("Tabela de documentos encontrada por header")
                except:
                    pass
            
            if tabela:
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
            if "não encontrada" not in str(e).lower():
                documentos.append({'erro': str(e)})
        
        return documentos
    
    def _fechar_abas_extras(self, aba_principal=None):
        if not self.driver:
            return
        
        try:
            if aba_principal is None and self.driver.window_handles:
                aba_principal = self.driver.window_handles[0]
            
            for handle in self.driver.window_handles:
                if handle != aba_principal:
                    try:
                        self.driver.switch_to.window(handle)
                        self.driver.close()
                        print(f"Aba extra fechada: {handle}")
                    except Exception as e:
                        print(f"Erro ao fechar aba {handle}: {e}")
            
            if aba_principal and aba_principal in self.driver.window_handles:
                self.driver.switch_to.window(aba_principal)
                print("Voltou para a aba principal")
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
