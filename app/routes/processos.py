from flask import Blueprint, request, jsonify
from app.services.scraper_service import ScraperService
from app.utils.auth_decorator import login_required
import asyncio
import traceback
import uuid
import threading
from collections import defaultdict

bp = Blueprint('processos', __name__, url_prefix='/api')

scraper_service = ScraperService()

scraping_sessions = {}

def processar_scraping_async(session_id, processos):
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        session_data = scraping_sessions[session_id]
        session_data['status'] = 'processing'
        session_data['resultados_parciais'] = {}
        
        total = len(processos)
        processos_por_tribunal = defaultdict(list)
        processos_sem_tribunal = []
        
        for idx, processo in enumerate(processos):
            if session_data.get('aborted', False):
                break
                
            tribunal = processo.get('tribunal')
            if tribunal:
                processos_por_tribunal[tribunal].append((idx, processo))
            else:
                processos_sem_tribunal.append((idx, processo))
        
        resultados_dict = {}
        
        for tribunal_key, lista_processos in processos_por_tribunal.items():
            if session_data.get('aborted', False):
                break
                
            for idx, processo in lista_processos:
                if session_data.get('aborted', False):
                    break
                
                numero_processo = processo['numero_processo']                
                resultado_temp = {
                    'numero_processo': numero_processo,
                    'tribunal': tribunal_key,
                    'status': 'processando',
                    'dados': None,
                    'erro': None
                }
                resultados_dict[idx] = resultado_temp
                session_data['resultados_parciais'][numero_processo] = resultado_temp
                
                resultado = loop.run_until_complete(
                    scraper_service.processar_processo(
                        numero_processo,
                        tribunal_key
                    )
                )
                resultados_dict[idx] = resultado
                session_data['resultados_parciais'][numero_processo] = resultado
            
            if not session_data.get('aborted', False):
                scraper_service._fechar_abas_tribunal(tribunal_key)
        
        for idx, processo in processos_sem_tribunal:
            if session_data.get('aborted', False):
                break
            numero_processo = processo.get('numero_processo', '')
            resultado = {
                'numero_processo': numero_processo,
                'tribunal': None,
                'status': 'erro',
                'erro': 'Tribunal não identificado'
            }
            resultados_dict[idx] = resultado
            session_data['resultados_parciais'][numero_processo] = resultado
        
        if not session_data.get('aborted', False):
            resultados = [resultados_dict[idx] for idx in range(len(processos))]
            session_data['resultados'] = resultados
            session_data['status'] = 'completed'
        else:
            session_data['status'] = 'aborted'
        
        scraper_service.fechar_scrapers()
        
        loop.close()
    except Exception as e:
        session_data['status'] = 'error'
        mensagem_amigavel = scraper_service._obter_mensagem_amigavel(e)
        session_data['error'] = mensagem_amigavel
        traceback.print_exc()
        try:
            scraper_service.fechar_scrapers()
        except:
            pass

@bp.route('/processos/scraper', methods=['POST'])
@login_required
def iniciar_scraping():
    data = request.get_json()
    processos = data.get('processos', [])
    if not processos:
        return jsonify({'error': 'Nenhum processo fornecido'}), 400
    
    try:
        session_id = str(uuid.uuid4())
        session_data = {
            'status': 'starting',
            'resultados_parciais': {},
            'resultados': None,
            'aborted': False
        }
        scraping_sessions[session_id] = session_data
        
        thread = threading.Thread(
            target=processar_scraping_async,
            args=(session_id, processos),
            daemon=True
        )
        thread.start()
        
        return jsonify({
            'success': True,
            'session_id': session_id
        })
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Erro completo ao processar scraping:")
        print(error_trace)
        return jsonify({
            'error': 'Erro ao processar scraping. Tente novamente.'
        }), 500

@bp.route('/processos/status/<session_id>', methods=['GET'])
@login_required
def status_processos(session_id):
    if session_id not in scraping_sessions:
        return jsonify({
            'status': 'error',
            'error': 'Sessão não encontrada ou expirada. O servidor pode ter reiniciado.',
            'resultados_parciais': []
        }), 200
    
    session_data = scraping_sessions[session_id]
    
    response = {
        'status': session_data['status'],
        'resultados_parciais': list(session_data.get('resultados_parciais', {}).values())
    }
    
    if session_data['status'] == 'completed':
        response['resultados'] = session_data.get('resultados', [])
    elif session_data['status'] == 'error':
        response['error'] = session_data.get('error', 'Erro desconhecido')
    
    return jsonify(response)

@bp.route('/processos/abort/<session_id>', methods=['POST'])
@login_required
def abortar_scraping(session_id):
    if session_id not in scraping_sessions:
        return jsonify({'error': 'Sessão não encontrada'}), 404
    
    session_data = scraping_sessions[session_id]
    
    if session_data['status'] in ['completed', 'aborted']:
        return jsonify({'error': 'Sessão já finalizada'}), 400
    
    session_data['aborted'] = True
    session_data['status'] = 'aborting'
    
    return jsonify({
        'success': True,
        'message': 'Scraping será abortado'
    })

@bp.route('/processos/status', methods=['GET'])
@login_required
def status_geral():
    return jsonify({'status': 'ok'})