from scrapers.base import BaseScraper
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from config.settings import CHROME_DRIVER_PATH, CHROME_USER_DATA_DIR, CHROME_PROFILE_DIRECTORY, DELAY_ENTRE_PROCESSOS, HEADLESS_MODE
import time
import re
import traceback
import os

class ESAJScraperTJMS(BaseScraper):
    
    def __init__(self, config):
        super().__init__(config)
        self.url_consulta = config.get('url_consulta', 'https://esaj.tjms.jus.br/cpopg5/open.do')
        self.headless = config.get('headless', False)
    
    def setup_driver(self):
        """Configura o driver do Chrome"""
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        
        try:
            chrome_options = Options()
            # TEMPORÁRIO: Desabilitar headless para debug
            use_headless = False  # Mudar para False para ver o navegador
            # use_headless = self.headless or HEADLESS_MODE  # Comentar esta linha
            
            if use_headless:
                chrome_options.add_argument("--headless=new")
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
            
            # Priorizar webdriver-manager (sempre baixa a versão correta)
            service = None
            if CHROME_DRIVER_PATH:
                service = Service(CHROME_DRIVER_PATH)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                # Usar webdriver-manager como fallback
                try:
                    from webdriver_manager.chrome import ChromeDriverManager
                    from webdriver_manager.core.os_manager import ChromeType
                    
                    # Limpar cache se necessário e obter o caminho correto
                    driver_path = ChromeDriverManager().install()
                    
                    # Se o caminho retornado não for válido, procurar manualmente
                    if driver_path and os.path.exists(driver_path):
                        # Normalizar caminho
                        driver_path = os.path.normpath(driver_path)
                        
                        # Se não for .exe, procurar no diretório
                        if not driver_path.endswith('.exe'):
                            base_dir = os.path.dirname(driver_path) if os.path.isfile(driver_path) else driver_path
                            # Procurar chromedriver.exe recursivamente
                            for root, dirs, files in os.walk(base_dir):
                                if 'chromedriver.exe' in files:
                                    driver_path = os.path.join(root, 'chromedriver.exe')
                                    break
                    
                    service = Service(driver_path)
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                except Exception as e:
                    # Último recurso: deixar Selenium encontrar automaticamente
                    print(f"Aviso: Erro ao usar webdriver-manager: {e}. Tentando sem Service...")
                    self.driver = webdriver.Chrome(options=chrome_options)
            
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            })
            
            if not use_headless:
                self.driver.maximize_window()
            
            print("Driver do Chrome configurado com sucesso")
            return self.driver
        except Exception as e:
            print(f"Erro ao configurar driver: {str(e)}")
            print(traceback.format_exc())
            raise
    
    def raspar_processo(self, numero_processo: str) -> dict:
        """Raspa os dados de um processo do TJMS"""
        print(f"Iniciando scraping do processo: {numero_processo}")
        
        # Garantir que o driver está válido
        self.ensure_driver()
        
        try:
            # Acessar página de consulta
            print(f"Acessando: {self.url_consulta}")
            self.driver.get(self.url_consulta)
            time.sleep(3)
            
            # Verificar se já está na página correta
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.ID, "numeroDigitoAnoUnificado"))
                )
            except TimeoutException:
                self.driver.get(self.url_consulta)
                time.sleep(3)
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "numeroDigitoAnoUnificado"))
                )
            
            # Verificar bloqueio ANTES de preencher (igual ao script de SP)
            if self._verificar_bloqueio():
                return {
                    'sucesso': False,
                    'numero_processo': numero_processo,
                    'erro': 'Sistema bloqueado - múltiplas consultas simultâneas'
                }
            
            # Extrair partes do número do processo
            partes = re.findall(r'\d+', numero_processo)
            if len(partes) < 5:
                return {
                    'sucesso': False,
                    'numero_processo': numero_processo,
                    'erro': f'Formato inválido: {numero_processo}'
                }
            
            numero_13_digitos = ''.join(partes[0:3])
            foro = partes[-1]
            
            # Preencher campos com delay aleatório (igual ao script de SP)
            import random
            campo_numero = self.driver.find_element(By.ID, "numeroDigitoAnoUnificado")
            campo_numero.clear()
            time.sleep(random.uniform(0.2, 0.5))
            campo_numero.send_keys(numero_13_digitos)
            time.sleep(random.uniform(0.2, 0.5))
            
            campo_foro = self.driver.find_element(By.ID, "foroNumeroUnificado")
            campo_foro.clear()
            time.sleep(random.uniform(0.2, 0.5))
            campo_foro.send_keys(foro)
            time.sleep(random.uniform(0.5, 1.0))
            
            # Clicar em consultar
            self.driver.find_element(By.ID, "botaoConsultarProcessos").click()
            
            # Aguardar processamento
            time.sleep(2)
            
            # Verificar bloqueio APÓS clicar (quando a mensagem aparece)
            page_source = self.driver.page_source.lower()
            if "múltiplas consultas simultâneas" in page_source or "foram identificadas múltiplas" in page_source:
                print("⚠️ Bloqueio detectado após consulta. Aguardando 2 minutos...")
                time.sleep(120)
                self.driver.refresh()
                time.sleep(3)
                return {
                    'sucesso': False,
                    'numero_processo': numero_processo,
                    'erro': 'Sistema bloqueado - múltiplas consultas simultâneas. Aguarde antes de tentar novamente.'
                }
            
            # Aguardar carregamento da página de resultados
            try:
                WebDriverWait(self.driver, 15).until(
                    lambda driver: driver.execute_script("return document.readyState") == "complete"
                )
                time.sleep(2)
                
                # Verificar novamente se há bloqueio
                page_source = self.driver.page_source.lower()
                if "múltiplas consultas simultâneas" in page_source or "foram identificadas múltiplas" in page_source:
                    return {
                        'sucesso': False,
                        'numero_processo': numero_processo,
                        'erro': 'Sistema bloqueado - múltiplas consultas simultâneas'
                    }
                
                # Verificar se processo não foi encontrado
                if any(palavra in page_source for palavra in [
                    "processo não encontrado",
                    "não foi possível localizar",
                    "nenhum processo encontrado"
                ]):
                    return {
                        'sucesso': False,
                        'numero_processo': numero_processo,
                        'erro': 'Processo não encontrado no sistema'
                    }
                
                # Tentar encontrar elementos que indicam que a página carregou
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.any_of(
                            EC.presence_of_element_located((By.CLASS_NAME, "row")),
                            EC.presence_of_element_located((By.ID, "classeProcesso")),
                            EC.presence_of_element_located((By.ID, "dadosProcesso")),
                            EC.presence_of_element_located((By.CSS_SELECTOR, "[id*='Processo']"))
                        )
                    )
                except TimeoutException:
                    if "numeroDigitoAnoUnificado" in self.driver.page_source:
                        if "múltiplas consultas simultâneas" in page_source:
                            return {
                                'sucesso': False,
                                'numero_processo': numero_processo,
                                'erro': 'Sistema bloqueado - múltiplas consultas simultâneas'
                            }
                        return {
                            'sucesso': False,
                            'numero_processo': numero_processo,
                            'erro': 'Página não carregou os resultados. Verifique se o processo existe.'
                        }
                
            except TimeoutException as e:
                page_source = self.driver.page_source.lower()
                if "múltiplas consultas simultâneas" in page_source:
                    return {
                        'sucesso': False,
                        'numero_processo': numero_processo,
                        'erro': 'Sistema bloqueado - múltiplas consultas simultâneas'
                    }
                return {
                    'sucesso': False,
                    'numero_processo': numero_processo,
                    'erro': f'Timeout ao aguardar resultado: {str(e)}'
                }
            
            # Extrair dados
            dados = self._extrair_dados_processo()
            
            return {
                'sucesso': True,
                'numero_processo': numero_processo,
                'dados': dados
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
            # Delay aleatório entre processos (igual ao script de SP)
            import random
            time.sleep(random.uniform(0.5, 1.5))
    
    def _verificar_bloqueio(self):
        """Verifica se o sistema bloqueou o acesso (igual ao script de SP)"""
        try:
            page_source = self.driver.page_source.lower()
            bloqueios = [
                "múltiplas consultas simultâneas",
                "foram identificadas múltiplas",
                "muitas consultas",
                "acesso temporariamente indisponível",
                "tente novamente mais tarde"
            ]
            
            for bloqueio in bloqueios:
                if bloqueio in page_source:
                    print(f"⚠️ Sistema bloqueado: '{bloqueio}'. Aguardando 2 minutos...")
                    time.sleep(120)
                    self.driver.refresh()
                    time.sleep(2)
                    return True
        except:
            pass
        return False
    
    def _extrair_dados_processo(self) -> dict:
        """Extrai todos os dados da página do processo"""
        dados = {}
        
        try:
            # 1. DADOS BÁSICOS
            dados['dados_processo'] = self._extrair_dados_basicos()
            
            # 2. PARTES (POLO ATIVO E PASSIVO)
            polo_ativo, polo_passivo = self._extrair_partes()
            dados['polo_ativo'] = polo_ativo
            dados['polo_passivo'] = polo_passivo
            
            # 3. MOVIMENTAÇÕES
            dados['movimentacoes'] = self._extrair_movimentacoes()
            
            # 4. DOCUMENTOS (extrair das movimentações)
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
            # Classe
            try:
                classe = self.driver.find_element(By.ID, "classeProcesso").text
                dados_basicos['classe_judicial'] = classe
            except:
                dados_basicos['classe_judicial'] = None
            
            # Assunto
            try:
                assunto = self.driver.find_element(By.ID, "assuntoProcesso").text
                dados_basicos['assunto'] = assunto
            except:
                dados_basicos['assunto'] = None
            
            # Foro
            try:
                foro_text = self.driver.find_element(By.ID, "foroProcesso").text
                dados_basicos['jurisdicao'] = foro_text
            except:
                dados_basicos['jurisdicao'] = None
            
            # Vara
            try:
                vara = self.driver.find_element(By.ID, "varaProcesso").text
                dados_basicos['orgao_julgador'] = vara
            except:
                dados_basicos['orgao_julgador'] = None
            
            # Juiz
            try:
                juiz = self.driver.find_element(By.ID, "juizProcesso").text
                dados_basicos['juiz'] = juiz
            except:
                dados_basicos['juiz'] = None
            
            # Área
            try:
                area = self.driver.find_element(By.ID, "areaProcesso").find_element(By.TAG_NAME, "span").get_attribute("title").strip()
                dados_basicos['area'] = area
            except:
                dados_basicos['area'] = None
            
            # Data de distribuição
            try:
                distribuicao = self.driver.find_element(By.ID, "dataHoraDistribuicaoProcesso").get_attribute("innerText").strip()
                dados_basicos['data_distribuicao'] = distribuicao
            except:
                dados_basicos['data_distribuicao'] = None
            
            # Número de controle
            try:
                controle = self.driver.find_element(By.ID, "numeroControleProcesso").get_attribute("innerText").strip()
                dados_basicos['numero_controle'] = controle
            except:
                dados_basicos['numero_controle'] = None
            
            # Valor da ação
            try:
                valor_acao = self.driver.find_element(By.ID, "valorAcaoProcesso").get_attribute("innerText").strip()
                dados_basicos['valor_acao'] = valor_acao
            except:
                dados_basicos['valor_acao'] = None
            
            # Número do processo (padrão do projeto)
            dados_basicos['numero'] = None  # Será preenchido pelo número passado
            
        except Exception as e:
            print(f"Erro ao extrair dados básicos: {e}")
            print(traceback.format_exc())
            dados_basicos['erro'] = str(e)
        
        return dados_basicos
    
    def _extrair_partes(self):
        """Extrai partes do processo (polo ativo e passivo) usando apenas Selenium"""
        polo_ativo = []
        polo_passivo = []
        
        try:
            # Aguardar tabela de partes aparecer
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "tableTodasPartes"))
                )
            except TimeoutException:
                print("Tabela de partes não encontrada")
                return polo_ativo, polo_passivo
            
            # Encontrar a tabela
            tabela = self.driver.find_element(By.ID, "tableTodasPartes")
            linhas = tabela.find_elements(By.TAG_NAME, "tr")
            
            for linha in linhas:
                try:
                    # Encontrar tipo de participação
                    try:
                        tipo_elem = linha.find_element(By.CSS_SELECTOR, "span.tipoDeParticipacao")
                        tipo = tipo_elem.text.strip().replace("\xa0", " ")
                    except:
                        continue
                    
                    # Encontrar célula com nome e advogado
                    try:
                        nome_celula = linha.find_element(By.CSS_SELECTOR, "td.nomeParteEAdvogado")
                        texto_completo = nome_celula.text.strip()
                    except:
                        continue
                    
                    if not texto_completo:
                        continue
                    
                    # Extrair nome (primeira linha)
                    linhas_texto = texto_completo.split('\n')
                    nome = linhas_texto[0].strip() if linhas_texto else texto_completo
                    
                    # Extrair advogado
                    advogado = ""
                    for i, linha_texto in enumerate(linhas_texto):
                        if "Advogado:" in linha_texto or "Advogada:" in linha_texto:
                            advogado = " ".join(linhas_texto[i+1:]).strip()
                            break
                    
                    # Extrair CPF/CNPJ/OAB
                    cpf_match = re.search(r'CPF:\s*([\d\.\-]+)', texto_completo)
                    cnpj_match = re.search(r'CNPJ:\s*([\d/\.\-]+)', texto_completo)
                    oab_match = re.search(r'OAB\s+([A-Z]{2}\d+)', texto_completo)
                    
                    participante = {
                        'nome': nome,
                        'nome_completo': texto_completo,
                        'situacao': 'Ativo',
                        'cpf': cpf_match.group(1) if cpf_match else None,
                        'cnpj': cnpj_match.group(1) if cnpj_match else None,
                        'oab': oab_match.group(1) if oab_match else None,
                        'tipo': tipo
                    }
                    
                    # Classificar em polo ativo ou passivo
                    tipo_lower = tipo.lower()
                    if 'autor' in tipo_lower or 'requerente' in tipo_lower or 'exequente' in tipo_lower:
                        polo_ativo.append(participante)
                    elif 'réu' in tipo_lower or 'requerido' in tipo_lower or 'executado' in tipo_lower:
                        polo_passivo.append(participante)
                    else:
                        # Se não conseguir classificar, adicionar ao polo ativo por padrão
                        polo_ativo.append(participante)
                    
                except Exception as e:
                    print(f"Erro ao processar parte: {e}")
                    continue
            
            print(f"Polo ativo: {len(polo_ativo)} participantes")
            print(f"Polo passivo: {len(polo_passivo)} participantes")
            
        except Exception as e:
            print(f"Erro ao extrair partes: {e}")
            print(traceback.format_exc())
        
        return polo_ativo, polo_passivo
    
    def _extrair_movimentacoes(self) -> list:
        """Extrai movimentações do processo usando apenas Selenium (igual ao script de SP)"""
        movimentacoes = []
        
        try:
            # Clicar no botão "mais" até não haver mais (EXATAMENTE como no script de SP)
            while True:
                try:
                    botao_mais = WebDriverWait(self.driver, 2).until(
                        EC.element_to_be_clickable((By.ID, "linkmovimentacoes"))
                    )
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", botao_mais)
                    time.sleep(0.3)
                    botao_mais.click()
                    time.sleep(1)
                except:
                    # Qualquer exceção (incluindo TimeoutException) quebra o loop
                    break
            
            # Extrair as movimentações (usando Selenium ao invés de BeautifulSoup)
            try:
                linhas = self.driver.find_elements(By.CSS_SELECTOR, "tr.containerMovimentacao")
            except:
                print("Nenhuma movimentação encontrada")
                return movimentacoes
            
            for linha in linhas:
                try:
                    # Extrair data
                    try:
                        data_td = linha.find_element(By.CSS_SELECTOR, "td.dataMovimentacao")
                        data = data_td.text.strip()
                    except:
                        data = ""
                    
                    # Extrair descrição (usando text ao invés de BeautifulSoup)
                    try:
                        mov_td = linha.find_element(By.CSS_SELECTOR, "td.descricaoMovimentacao")
                        # Usar get_attribute("innerText") ou text e substituir quebras de linha
                        movimento_texto = mov_td.get_attribute("innerText") or mov_td.text
                        movimento_texto = movimento_texto.strip().replace("\n", " ").replace("\r", " ")
                    except:
                        movimento_texto = ""
                    
                    if data and movimento_texto:
                        movimentacoes.append({
                            "Data": data,
                            "Movimento": movimento_texto
                        })
                        
                except Exception as e:
                    print(f"Erro ao processar movimentação: {e}")
                    continue
            
            print(f"Total de movimentações extraídas: {len(movimentacoes)}")
            
        except Exception as e:
            print(f"Erro ao extrair movimentações: {e}")
            print(traceback.format_exc())
        
        return movimentacoes
    
    def _extrair_documentos(self) -> list:
        """Extrai documentos juntados ao processo"""
        documentos = []
        
        try:
            # Os documentos podem estar nas movimentações ou em uma seção separada
            # Por enquanto, retornar lista vazia (pode ser implementado depois)
            pass
        except Exception as e:
            print(f"Erro ao extrair documentos: {e}")
        
        return documentos
