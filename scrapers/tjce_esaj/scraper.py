from scrapers.base import BaseScraper
from scrapers.consulta_cli_common import (
    MENSAGEM_ESAJ_SEM_INFORMACOES,
    esaj_resposta_sem_informacoes,
)
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from config.settings import (
    CHROME_DRIVER_PATH,
    CHROME_PROFILE_DIRECTORY,
    CHROME_USER_DATA_DIR,
    DELAY_ENTRE_PROCESSOS,
    HEADLESS_MODE,
    SCRAPER_PROXY_CE,
)
import time
import re
import traceback
from bs4 import BeautifulSoup


class ESAJScraperTJCE(BaseScraper):
    """eSAJ TJCE (1º grau) — mesma estrutura de página/campos que o eSAJ TJSP/TJAL."""

    def __init__(self, config):
        super().__init__(config)
        self.url_consulta = config.get(
            "url_consulta",
            "https://esaj.tjce.jus.br/cpopg/open.do?servico=190101",
        )
        self.headless = config.get("headless", False)

    def setup_driver(self):
        """Configura o driver do Chrome"""
        from selenium.webdriver.chrome.options import Options
        from scrapers.driver_utils import apply_chrome_proxy, create_chrome_driver

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
                chrome_options.add_argument(
                    "--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
                )
                print("Modo headless ativado")
            else:
                if CHROME_USER_DATA_DIR:
                    chrome_options.add_argument(f"--user-data-dir={CHROME_USER_DATA_DIR}")
                    chrome_options.add_argument(f"--profile-directory={CHROME_PROFILE_DIRECTORY}")
                chrome_options.add_experimental_option("detach", True)

            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option("useAutomationExtension", False)
            apply_chrome_proxy(chrome_options, SCRAPER_PROXY_CE)

            self.driver = create_chrome_driver(
                chrome_options,
                driver_path=CHROME_DRIVER_PATH,
            )

            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.execute_cdp_cmd(
                "Network.setUserAgentOverride",
                {
                    "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                },
            )

            if not use_headless:
                self.driver.maximize_window()

            print("Driver do Chrome configurado com sucesso")
            return self.driver
        except Exception as e:
            print(f"Erro ao configurar driver: {str(e)}")
            print(traceback.format_exc())
            raise

    def raspar_processo(self, numero_processo: str) -> dict:
        """Raspa os dados de um processo do eSAJ TJCE (consulta pública 1º grau)."""
        print(f"Iniciando scraping do processo: {numero_processo}")

        self.ensure_driver()

        try:
            print(f"Acessando: {self.url_consulta}")
            self.driver.get(self.url_consulta)
            time.sleep(3)

            if self._verificar_bloqueio():
                return {
                    "sucesso": False,
                    "numero_processo": numero_processo,
                    "erro": "Sistema bloqueado - múltiplas consultas simultâneas",
                }

            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.ID, "numeroDigitoAnoUnificado"))
            )

            partes = re.findall(r"\d+", numero_processo)
            if len(partes) < 5:
                return {
                    "sucesso": False,
                    "numero_processo": numero_processo,
                    "erro": f"Formato inválido: {numero_processo}",
                }

            numero_13_digitos = "".join(partes[0:3])
            foro = partes[-1]

            campo_numero = self.driver.find_element(By.ID, "numeroDigitoAnoUnificado")
            campo_numero.clear()
            campo_numero.send_keys(numero_13_digitos)

            campo_foro = self.driver.find_element(By.ID, "foroNumeroUnificado")
            campo_foro.clear()
            campo_foro.send_keys(foro)

            self.driver.find_element(By.ID, "botaoConsultarProcessos").click()

            time.sleep(2)

            page_source = self.driver.page_source.lower()
            if "múltiplas consultas simultâneas" in page_source or "foram identificadas múltiplas" in page_source:
                print("⚠️ Bloqueio detectado após consulta. Aguardando 3 minutos...")
                time.sleep(180)
                self.driver.refresh()
                return {
                    "sucesso": False,
                    "numero_processo": numero_processo,
                    "erro": "Sistema bloqueado - múltiplas consultas simultâneas",
                }

            if self._verificar_modal_senha():
                return {
                    "sucesso": False,
                    "numero_processo": numero_processo,
                    "erro": "Processo requer senha",
                }

            if esaj_resposta_sem_informacoes(self.driver.page_source):
                print(MENSAGEM_ESAJ_SEM_INFORMACOES)
                return {
                    "sucesso": False,
                    "numero_processo": numero_processo,
                    "erro": MENSAGEM_ESAJ_SEM_INFORMACOES,
                }

            WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, "row")))

            self._expandir_dados_secundarios()

            dados = self._extrair_dados_processo()

            return {"sucesso": True, "numero_processo": numero_processo, "dados": dados}

        except Exception as e:
            error_msg = str(e)
            error_trace = traceback.format_exc()
            print(f"Erro geral no scraping: {error_msg}")
            print(error_trace)
            return {
                "sucesso": False,
                "numero_processo": numero_processo,
                "erro": error_msg,
                "traceback": error_trace,
            }
        finally:
            time.sleep(DELAY_ENTRE_PROCESSOS)

    def _verificar_bloqueio(self):
        """Verifica se o sistema bloqueou o acesso"""
        try:
            page_source = self.driver.page_source.lower()
            bloqueios = [
                "múltiplas consultas simultâneas",
                "muitas consultas",
                "acesso temporariamente indisponível",
                "tente novamente mais tarde",
            ]

            for bloqueio in bloqueios:
                if bloqueio in page_source:
                    print(f"Sistema bloqueado: '{bloqueio}'. Aguardando 3 minutos...")
                    time.sleep(180)
                    self.driver.refresh()
                    return True
        except Exception:
            pass
        return False

    def _verificar_modal_senha(self):
        """Verifica e fecha modal de senha se aparecer"""
        try:
            time.sleep(0.3)
            try:
                modal = self.driver.find_element(By.ID, "popupSenha")
                style = modal.get_attribute("style") or ""
                if modal.is_displayed() or "display: block" in style:
                    try:
                        botao_cancelar = WebDriverWait(self.driver, 1).until(
                            EC.element_to_be_clickable((By.ID, "botaoFecharPopupSenha"))
                        )
                        botao_cancelar.click()
                        return True
                    except Exception:
                        try:
                            self.driver.execute_script(
                                "document.getElementById('popupSenha').style.display = 'none';"
                            )
                            return True
                        except Exception:
                            pass
            except Exception:
                pass
        except Exception:
            pass
        return False

    def _expandir_dados_secundarios(self):
        """Expande dados secundários se necessário"""
        try:
            botao_mais = WebDriverWait(self.driver, 3).until(
                EC.element_to_be_clickable((By.ID, "botaoExpandirDadosSecundarios"))
            )
            botao_mais.click()
            time.sleep(0.3)
        except Exception:
            try:
                span_mais = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "span.unj-link-collapse__show"))
                )
                span_mais.click()
                time.sleep(0.3)
            except Exception:
                pass

    def _extrair_dados_processo(self) -> dict:
        """Extrai todos os dados da página do processo"""
        dados = {}

        try:
            dados["dados_processo"] = self._extrair_dados_basicos()
            polo_ativo, polo_passivo = self._extrair_partes()
            dados["polo_ativo"] = polo_ativo
            dados["polo_passivo"] = polo_passivo
            dados["movimentacoes"] = self._extrair_movimentacoes()
            dados["documentos"] = []

            print("Dados extraídos com sucesso!")
        except Exception as e:
            error_msg = str(e)
            print(f"Erro ao extrair dados: {error_msg}")
            print(traceback.format_exc())
            dados["erro_extracao"] = error_msg

        return dados

    def _extrair_dados_basicos(self) -> dict:
        """Extrai dados básicos do processo"""
        dados_basicos = {}

        try:
            try:
                classe = self.driver.find_element(By.ID, "classeProcesso").text
                dados_basicos["classe_judicial"] = classe
            except Exception:
                dados_basicos["classe_judicial"] = None

            try:
                assunto = self.driver.find_element(By.ID, "assuntoProcesso").text
                dados_basicos["assunto"] = assunto
            except Exception:
                dados_basicos["assunto"] = None

            try:
                foro_text = self.driver.find_element(By.ID, "foroProcesso").text
                dados_basicos["jurisdicao"] = foro_text
            except Exception:
                dados_basicos["jurisdicao"] = None

            try:
                vara = self.driver.find_element(By.ID, "varaProcesso").text
                dados_basicos["orgao_julgador"] = vara
            except Exception:
                dados_basicos["orgao_julgador"] = None

            try:
                distribuicao = (
                    self.driver.find_element(By.ID, "dataHoraDistribuicaoProcesso")
                    .get_attribute("innerText")
                    .strip()
                )
                dados_basicos["data_distribuicao"] = distribuicao
            except Exception:
                dados_basicos["data_distribuicao"] = None

            try:
                valor_elem = WebDriverWait(self.driver, 3).until(
                    EC.presence_of_element_located((By.ID, "valorAcaoProcesso"))
                )
                valor_acao = valor_elem.get_attribute("innerText").strip()
                dados_basicos["valor_acao"] = valor_acao
            except Exception:
                dados_basicos["valor_acao"] = None

            dados_basicos["numero"] = None

        except Exception as e:
            print(f"Erro ao extrair dados básicos: {e}")
            print(traceback.format_exc())
            dados_basicos["erro"] = str(e)

        return dados_basicos

    def _extrair_partes(self):
        """Extrai partes do processo (polo ativo e passivo)"""
        polo_ativo = []
        polo_passivo = []

        try:
            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            todas_partes = soup.select("#tablePartesPrincipais tbody tr")

            for row in todas_partes:
                try:
                    tipo_parte = row.select_one("span.tipoDeParticipacao")
                    nome_parte = row.select_one("td.nomeParteEAdvogado")

                    if not tipo_parte or not nome_parte:
                        continue

                    tipo = tipo_parte.get_text(strip=True).replace("\xa0", " ")
                    nomes = list(nome_parte.stripped_strings)
                    nome = nomes[0] if nomes else ""

                    advogado = ""
                    if "Advogado:" in nomes or "Advogada:" in nomes:
                        idx = nomes.index("Advogado:") if "Advogado:" in nomes else nomes.index("Advogada:")
                        advogado_lista = [n for n in nomes[idx + 1 :] if n.strip() and n.strip() != "&nbsp;"]
                        advogado = ", ".join(advogado_lista).strip()

                    texto_completo = nome_parte.get_text()
                    cpf_match = re.search(r"CPF:\s*([\d\.\-]+)", texto_completo)
                    cnpj_match = re.search(r"CNPJ:\s*([\d/\.\-]+)", texto_completo)
                    oab_match = re.search(r"OAB\s+([A-Z]{2}\d+[A-Z]?)", texto_completo)

                    participante = {
                        "nome": nome,
                        "nome_completo": texto_completo,
                        "situacao": "Ativo",
                        "cpf": cpf_match.group(1) if cpf_match else None,
                        "cnpj": cnpj_match.group(1) if cnpj_match else None,
                        "oab": oab_match.group(1) if oab_match else None,
                        "tipo": tipo,
                    }

                    tipo_lower = tipo.lower()
                    if "autor" in tipo_lower or "requerente" in tipo_lower or "exequente" in tipo_lower:
                        polo_ativo.append(participante)
                    elif "réu" in tipo_lower or "requerido" in tipo_lower or "executado" in tipo_lower:
                        polo_passivo.append(participante)
                    else:
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
        """Extrai movimentações do processo"""
        movimentacoes = []

        try:
            while True:
                try:
                    botao_mais = WebDriverWait(self.driver, 2).until(
                        EC.element_to_be_clickable((By.ID, "linkmovimentacoes"))
                    )
                    if "Mais" in botao_mais.text or "Recolher" not in botao_mais.text:
                        botao_mais.click()
                        time.sleep(0.5)
                    else:
                        break
                except Exception:
                    break

            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            rows = soup.select("tbody#tabelaTodasMovimentacoes tr.containerMovimentacao")
            if not rows:
                rows = soup.select("tr.containerMovimentacao")

            for row in rows:
                try:
                    data_td = row.select_one("td.dataMovimentacao")
                    mov_td = row.select_one("td.descricaoMovimentacao")
                    data = data_td.get_text(strip=True) if data_td else ""
                    movimento_texto = mov_td.get_text(separator=" ", strip=True).replace("\n", " ") if mov_td else ""

                    if data and movimento_texto:
                        movimentacoes.append(
                            {
                                "movimento": f"{data} - {movimento_texto}",
                                "descricao": movimento_texto,
                                "data": data,
                                "hora": None,
                            }
                        )
                except Exception as e:
                    print(f"Erro ao processar movimentação: {e}")
                    continue

            print(f"Total de movimentações extraídas: {len(movimentacoes)}")

        except Exception as e:
            print(f"Erro ao extrair movimentações: {e}")
            print(traceback.format_exc())

        return movimentacoes
