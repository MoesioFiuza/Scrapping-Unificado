import asyncio
from config.tribunais import TRIBUNAIS_MAP
import importlib
from typing import List, Dict, Any
import traceback
import time

class ScraperService:
    def __init__(self):
        self.scrapers_instances = {}
    
    def get_scraper(self, tribunal_key: str):
        if tribunal_key not in TRIBUNAIS_MAP:
            raise ValueError(f"Tribunal {tribunal_key} não encontrado")
        if tribunal_key not in self.scrapers_instances:
            tribunal_config = TRIBUNAIS_MAP[tribunal_key]
            module_path = tribunal_config['modulo_scraper']
            class_name = tribunal_config['classe_scraper']
            try:
                module = importlib.import_module(module_path)
                scraper_class = getattr(module, class_name)
                self.scrapers_instances[tribunal_key] = scraper_class(tribunal_config)
                print(f"Configurando driver para {tribunal_key}...")
                self.scrapers_instances[tribunal_key].setup_driver()
                print(f"Driver configurado com sucesso para {tribunal_key}")
            except Exception as e:
                print(f"Erro ao criar scraper para {tribunal_key}: {str(e)}")
                print(traceback.format_exc())
                raise
        
        return self.scrapers_instances[tribunal_key]
    
    async def processar_processo(self, numero_processo: str, tribunal_key: str) -> Dict[str, Any]:
        print(f"Processando processo: {numero_processo} - Tribunal: {tribunal_key}")
        try:
            scraper = self.get_scraper(tribunal_key)
            loop = asyncio.get_event_loop()
            resultado = await loop.run_in_executor(
                None, 
                scraper.raspar_processo, 
                numero_processo
            )
            
            print(f"Resultado para {numero_processo}: {resultado.get('sucesso', False)}")
            
            return {
                'numero_processo': numero_processo,
                'tribunal': tribunal_key,
                'status': 'sucesso' if resultado.get('sucesso') else 'erro',
                'dados': resultado.get('dados') if resultado.get('sucesso') else None,
                'erro': resultado.get('erro') if not resultado.get('sucesso') else None
            }
        except Exception as e:
            error_trace = traceback.format_exc()
            print(f"Erro completo ao processar {numero_processo}:")
            print(error_trace)
            mensagem_amigavel = self._obter_mensagem_amigavel(e)
            
            return {
                'numero_processo': numero_processo,
                'tribunal': tribunal_key,
                'status': 'erro',
                'erro': mensagem_amigavel
            }
    
    async def processar_lote(self, processos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        resultados = []
        total = len(processos)
        processos_por_tribunal = {}
        processos_sem_tribunal = []
        ordem_original = []
        
        for idx, processo in enumerate(processos):
            tribunal = processo.get('tribunal')
            if tribunal:
                if tribunal not in processos_por_tribunal:
                    processos_por_tribunal[tribunal] = []
                processos_por_tribunal[tribunal].append((idx, processo))
            else:
                processos_sem_tribunal.append((idx, processo))
            ordem_original.append((idx, processo))
        resultados_dict = {}
        for tribunal_key, lista_processos in processos_por_tribunal.items():
            print(f"\n{'='*50}")
            print(f"Processando {len(lista_processos)} processos do {TRIBUNAIS_MAP.get(tribunal_key, {}).get('nome', tribunal_key)}")
            print(f"{'='*50}\n")
            
            for idx, processo in lista_processos:
                print(f"Processando {idx+1}/{total}: {processo.get('numero_processo')}")
                resultado = await self.processar_processo(
                    processo['numero_processo'],
                    processo['tribunal']
                )
                resultados_dict[idx] = resultado
            
            print(f"\nConcluído processamento do {TRIBUNAIS_MAP.get(tribunal_key, {}).get('nome', tribunal_key)}. Fechando abas...")
            self._fechar_abas_tribunal(tribunal_key)
        
        for idx, processo in processos_sem_tribunal:
            resultados_dict[idx] = {
                'numero_processo': processo.get('numero_processo', ''),
                'tribunal': None,
                'status': 'erro',
                'erro': 'Tribunal não identificado'
            }
        
        resultados = [resultados_dict[idx] for idx in range(len(processos))]
        
        return resultados
    
    def fechar_scrapers(self):
        for scraper in self.scrapers_instances.values():
            try:
                scraper.close()
            except:
                pass
        self.scrapers_instances.clear()

    def _fechar_abas_tribunal(self, tribunal_key: str):
        if tribunal_key in self.scrapers_instances:
            scraper = self.scrapers_instances[tribunal_key]
            try:
                if hasattr(scraper, 'fechar_todas_abas'):
                    scraper.fechar_todas_abas()
                elif hasattr(scraper, '_fechar_abas_extras'):
                    scraper._fechar_abas_extras(None)
            except Exception as e:
                print(f"Erro ao fechar abas do tribunal {tribunal_key}: {e}")

    def _obter_mensagem_amigavel(self, exception: Exception) -> str:
        error_str = str(exception).lower()
        
        if 'no such element' in error_str or 'unable to locate' in error_str:
            return 'Não foi possível localizar elementos na página.'
        elif 'timeout' in error_str:
            return 'Tempo de espera esgotado. Tente novamente.'
        elif 'session' in error_str or 'chrome' in error_str:
            return 'Erro na conexão com o navegador.'
        elif 'not found' in error_str:
            return 'Processo não encontrado.'
        elif 'network' in error_str or 'connection' in error_str:
            return 'Erro de conexão. Verifique sua internet.'
        else:
            return 'Erro ao processar o processo. Tente novamente.'