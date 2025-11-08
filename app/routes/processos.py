from flask import Blueprint, request, jsonify
from app.services.scraper_service import ScraperService
import asyncio
import traceback

bp = Blueprint('processos', __name__, url_prefix='/api')

scraper_service = ScraperService()

@bp.route('/processos/scraper', methods=['POST'])
def iniciar_scraping():
    data = request.get_json()
    processos = data.get('processos', [])
    if not processos:
        return jsonify({'error': 'Nenhum processo fornecido'}), 400
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        resultados = loop.run_until_complete(
            scraper_service.processar_lote(processos)
        )
        loop.close()
        
        return jsonify({
            'success': True,
            'resultados': resultados,
            'total_processados': len(resultados)
        })
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Erro completo ao processar scraping:")
        print(error_trace)
        return jsonify({
            'error': 'Erro ao processar scraping. Tente novamente.'
        }), 500

@bp.route('/processos/status', methods=['GET'])
def status_processos():
    return jsonify({'status': 'ok'})