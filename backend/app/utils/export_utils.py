"""
Utilitários para exportação de dados em CSV e PDF
"""
import csv
import io
from typing import List, Dict, Any
from datetime import datetime
from app.utils.datetime_utils import now_utc, to_utc
from fastapi.responses import StreamingResponse


def export_to_csv(data: List[Dict[str, Any]], filename: str) -> StreamingResponse:
    """
    Exporta uma lista de dicionários para CSV
    
    Args:
        data: Lista de dicionários com os dados
        filename: Nome do arquivo para download
    
    Returns:
        StreamingResponse com o CSV
    """
    if not data:
        # Retornar CSV vazio com headers
        output = io.StringIO()
        output.write("No data available\n")
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    output = io.StringIO()
    
    # Pegar as chaves do primeiro item como headers
    headers = list(data[0].keys())
    
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    
    for row in data:
        # Converter valores complexos para string
        clean_row = {}
        for key, value in row.items():
            if isinstance(value, (datetime,)):
                clean_row[key] = value.isoformat() if value else ""
            elif isinstance(value, (dict, list)):
                clean_row[key] = str(value)
            else:
                clean_row[key] = value
        writer.writerow(clean_row)
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


def export_to_pdf_simple(data: List[Dict[str, Any]], filename: str, title: str) -> StreamingResponse:
    """
    Exporta dados para PDF simples (usando reportlab se disponível)
    
    Args:
        data: Lista de dicionários com os dados
        filename: Nome do arquivo para download
        title: Título do relatório
    
    Returns:
        StreamingResponse com o PDF
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import inch
        
        buffer = io.BytesIO()
        
        # Criar documento
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = styles['Heading1']
        
        # Adicionar título
        elements.append(Paragraph(title, title_style))
        elements.append(Spacer(1, 0.3 * inch))
        
        # Adicionar data de geração
        date_text = f"Gerado em: {now_utc().strftime('%d/%m/%Y %H:%M')}"
        elements.append(Paragraph(date_text, styles['Normal']))
        elements.append(Spacer(1, 0.2 * inch))
        
        if not data:
            elements.append(Paragraph("Nenhum dado disponível", styles['Normal']))
        else:
            # Preparar dados da tabela
            headers = list(data[0].keys())
            table_data = [headers]
            
            for row in data:
                table_row = []
                for key in headers:
                    value = row[key]
                    if isinstance(value, datetime):
                        table_row.append(value.strftime('%d/%m/%Y %H:%M') if value else "")
                    elif isinstance(value, (dict, list)):
                        table_row.append(str(value)[:50])  # Limitar tamanho
                    else:
                        table_row.append(str(value) if value is not None else "")
                table_data.append(table_row)
            
            # Criar tabela
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
            ]))
            
            elements.append(table)
        
        # Construir PDF
        doc.build(elements)
        buffer.seek(0)
        
        return StreamingResponse(
            iter([buffer.getvalue()]),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except ImportError:
        # Se reportlab não estiver instalado, retornar erro amigável
        raise ImportError(
            "reportlab não está instalado. "
            "Execute: pip install reportlab"
        )

