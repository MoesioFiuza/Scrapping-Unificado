from flask import Blueprint, request, jsonify, send_file
import pandas as pd
import os
from datetime import datetime
import traceback
from pathlib import Path

bp = Blueprint('resultados', __name__, url_prefix='/api')

@bp.route('/resultados/exportar', methods=['POST'])
def exportar_resultados():
    data = request.get_json()
    resultados = data.get('resultados', [])
    
    if not resultados:
        return jsonify({'error': 'Nenhum resultado para exportar'}), 400
    
    try:
        dados_export = []
        for resultado in resultados:
            if resultado.get('status') == 'sucesso' and resultado.get('dados'):
                dados = resultado['dados']
                dados_processo = dados.get('dados_processo', {})
                polo_ativo = dados.get('polo_ativo', [])
                polo_passivo = dados.get('polo_passivo', [])
                movimentacoes = dados.get('movimentacoes', [])
                texto_movimentacoes = '\n'.join([
                    mov.get('movimento', '') or mov.get('descricao', '')
                    for mov in movimentacoes
                    if mov.get('movimento') or mov.get('descricao')
                ])
                
                dados_export.append({
                    'Numero Processo': resultado.get('numero_processo', ''),
                    'Tribunal': resultado.get('tribunal', ''),
                    'Data Distribuicao': dados_processo.get('data_distribuicao', ''),
                    'Classe Judicial': dados_processo.get('classe_judicial', ''),
                    'Assunto': dados_processo.get('assunto', ''),
                    'Jurisdicao': dados_processo.get('jurisdicao', ''),
                    'Orgao Julgador': dados_processo.get('orgao_julgador', ''),
                    'Polo Ativo': '; '.join([p.get('nome', '') for p in polo_ativo]),
                    'Polo Passivo': '; '.join([p.get('nome', '') for p in polo_passivo]),
                    'Movimentacoes': texto_movimentacoes,
                    'Total Movimentacoes': len(movimentacoes),
                    'Total Documentos': len(dados.get('documentos', []))
                })
        
        if not dados_export:
            return jsonify({'error': 'Nenhum resultado com sucesso para exportar'}), 400
        df = pd.DataFrame(dados_export)
        downloads_path = Path.home() / 'Downloads'
        downloads_path.mkdir(exist_ok=True)
        
        filename = f"resultados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        filepath = downloads_path / filename
        with pd.ExcelWriter(str(filepath), engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Resultados')
            worksheet = writer.sheets['Resultados']
            worksheet.column_dimensions['A'].width = 20  # Numero Processo
            worksheet.column_dimensions['B'].width = 15  # Tribunal
            worksheet.column_dimensions['C'].width = 15  # Data Distribuicao
            worksheet.column_dimensions['D'].width = 40  # Classe Judicial
            worksheet.column_dimensions['E'].width = 50  # Assunto
            worksheet.column_dimensions['F'].width = 30  # Jurisdicao
            worksheet.column_dimensions['G'].width = 40  # Orgao Julgador
            worksheet.column_dimensions['H'].width = 40  # Polo Ativo
            worksheet.column_dimensions['I'].width = 40  # Polo Passivo
            worksheet.column_dimensions['J'].width = 80  # Movimentacoes (mais larga para o texto)
            worksheet.column_dimensions['K'].width = 15  # Total Movimentacoes
            worksheet.column_dimensions['L'].width = 15  # Total Documentos
            from openpyxl.styles import Alignment
            for row in worksheet.iter_rows(min_row=2, max_row=worksheet.max_row):
                for cell in row:
                    cell.alignment = Alignment(wrap_text=True, vertical='top')
        
        return send_file(
            str(filepath), 
            as_attachment=True, 
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Erro ao exportar resultados: {error_trace}")
        return jsonify({'error': f'Erro ao exportar resultados: {str(e)}'}), 500