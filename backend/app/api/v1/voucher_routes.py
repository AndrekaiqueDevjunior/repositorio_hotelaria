"""
Rotas de Vouchers
Gerencia vouchers de confirmação de reserva
"""

from fastapi import APIRouter, HTTPException, Depends, Body, Response
from pydantic import BaseModel
from datetime import datetime
from app.utils.datetime_utils import now_utc, to_utc
from app.core.database import get_db
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
import os
from app.services.voucher_service import (
    gerar_voucher,
    validar_voucher_checkin,
    validar_voucher_checkout
)
from app.middleware.auth_middleware import get_current_active_user
from app.core.security import User
from app.repositories.hospedagem_repo import HospedagemRepository

router = APIRouter(prefix="/vouchers", tags=["vouchers"])


class CheckinRequest(BaseModel):
    funcionario_id: int


@router.get("/reserva/{reserva_id}")
async def obter_voucher_por_reserva(reserva_id: int):
    """Obter voucher de uma reserva"""
    
    db = get_db()
    
    voucher = await db.voucher.find_first(
        where={'reservaId': reserva_id},
        include={
            'reserva': {
                'include': {
                    'cliente': True,
                    'pagamentos': True
                }
            }
        }
    )
    
    if not voucher:
        raise HTTPException(
            status_code=404,
            detail="Voucher não encontrado para esta reserva"
        )
    
    return {
        "success": True,
        "data": {
            "id": voucher.id,
            "codigo": voucher.codigo,
            "status": voucher.status,
            "dataEmissao": voucher.dataEmissao,
            "checkinRealizadoEm": voucher.checkinRealizadoEm,
            "checkoutRealizadoEm": voucher.checkoutRealizadoEm,
            "reserva": {
                "id": voucher.reserva.id,
                "codigoReserva": voucher.reserva.codigoReserva,
                "clienteNome": voucher.reserva.clienteNome,
                "quartoNumero": voucher.reserva.quartoNumero,
                "tipoSuite": voucher.reserva.tipoSuite,
                "checkinPrevisto": voucher.reserva.checkinPrevisto,
                "checkoutPrevisto": voucher.reserva.checkoutPrevisto,
                "valorTotal": float(voucher.reserva.valorDiaria) * voucher.reserva.numDiarias if voucher.reserva.valorDiaria else 0,
                "status": voucher.reserva.status,
                "cliente": {
                    "nomeCompleto": voucher.reserva.cliente.nomeCompleto,
                    "email": voucher.reserva.cliente.email,
                    "telefone": voucher.reserva.cliente.telefone
                }
            }
        }
    }


@router.get("/{codigo}")
async def obter_voucher(codigo: str):
    """Obter voucher por código"""
    
    db = get_db()
    
    voucher = await db.voucher.find_first(
        where={'codigo': codigo.upper()},
        include={
            'reserva': {
                'include': {
                    'cliente': True,
                    'pagamentos': True
                }
            }
        }
    )
    
    if not voucher:
        raise HTTPException(
            status_code=404,
            detail=f"Voucher {codigo} não encontrado"
        )
    
    return {
        "success": True,
        "data": {
            "id": voucher.id,
            "codigo": voucher.codigo,
            "status": voucher.status,
            "dataEmissao": voucher.dataEmissao,
            "checkinRealizadoEm": voucher.checkinRealizadoEm,
            "checkoutRealizadoEm": voucher.checkoutRealizadoEm,
            "reserva": {
                "id": voucher.reserva.id,
                "codigoReserva": voucher.reserva.codigoReserva,
                "clienteNome": voucher.reserva.clienteNome,
                "quartoNumero": voucher.reserva.quartoNumero,
                "tipoSuite": voucher.reserva.tipoSuite,
                "checkinPrevisto": voucher.reserva.checkinPrevisto,
                "checkoutPrevisto": voucher.reserva.checkoutPrevisto,
                "status": voucher.reserva.status,
                "cliente": {
                    "nomeCompleto": voucher.reserva.cliente.nomeCompleto,
                    "email": voucher.reserva.cliente.email,
                    "telefone": voucher.reserva.cliente.telefone
                }
            }
        }
    }


@router.patch("/{codigo}/checkin")
async def realizar_checkin(
    codigo: str,
    request: CheckinRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Realizar check-in via voucher
    
    Reutiliza a lógica existente de check-in da reserva
    """
    
    db = get_db()
    
    # 1. Validar voucher
    voucher_data = await validar_voucher_checkin(codigo)
    
    # 2. Delegar para fluxo operacional (único caminho autoritativo)
    hospedagem_repo = HospedagemRepository(db)
    await hospedagem_repo.checkin(
        reserva_id=voucher_data['reservaId'],
        funcionario_id=request.funcionario_id
    )
    reserva = await db.reserva.find_unique(where={"id": voucher_data['reservaId']})
    
    # 3. Atualizar voucher
    voucher_atualizado = await db.voucher.update(
        where={'id': voucher_data['id']},
        data={
            'status': 'CHECKIN_REALIZADO',
            'checkinRealizadoEm': now_utc(),
            'checkinRealizadoPor': request.funcionario_id
        }
    )
    
    # 4. Registrar auditoria
    try:
        await db.auditoria.create(
            data={
                'usuarioId': request.funcionario_id,
                'acao': 'CHECKIN_VOUCHER',
                'entidade': 'VOUCHER',
                'entidadeId': voucher_data['id'],
                'detalhes': f'Check-in realizado via voucher {codigo}',
                'sucesso': True
            }
        )
    except Exception as e:
        print(f"[VOUCHER] Erro ao registrar auditoria: {e}")
    
    return {
        "success": True,
        "message": "Check-in realizado com sucesso",
        "data": {
            "voucher": {
                "codigo": voucher_atualizado.codigo,
                "status": voucher_atualizado.status,
                "checkinRealizadoEm": voucher_atualizado.checkinRealizadoEm
            },
            "reserva": reserva
        }
    }


@router.patch("/{codigo}/checkout")
async def realizar_checkout(
    codigo: str,
    request: CheckinRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Realizar check-out via voucher
    
    Reutiliza a lógica existente de check-out da reserva
    + CREDITA PONTOS AUTOMATICAMENTE
    """
    
    db = get_db()
    
    # 1. Validar voucher
    voucher_data = await validar_voucher_checkout(codigo)
    
    # 2. Delegar para fluxo operacional (único caminho autoritativo)
    hospedagem_repo = HospedagemRepository(db)
    await hospedagem_repo.checkout(
        reserva_id=voucher_data['reservaId'],
        funcionario_id=request.funcionario_id
    )
    reserva = await db.reserva.find_unique(where={"id": voucher_data['reservaId']})
    
    # 3. Atualizar voucher
    voucher_atualizado = await db.voucher.update(
        where={'id': voucher_data['id']},
        data={
            'status': 'FINALIZADO',
            'checkoutRealizadoEm': now_utc(),
            'checkoutRealizadoPor': request.funcionario_id
        }
    )
    
    # 4. Registrar auditoria
    try:
        await db.auditoria.create(
            data={
                'usuarioId': request.funcionario_id,
                'acao': 'CHECKOUT_VOUCHER',
                'entidade': 'VOUCHER',
                'entidadeId': voucher_data['id'],
                'detalhes': f'Check-out realizado via voucher {codigo}',
                'sucesso': True
            }
        )
    except Exception as e:
        print(f"[VOUCHER] Erro ao registrar auditoria: {e}")
    
    return {
        "success": True,
        "message": "Check-out realizado com sucesso",
        "data": {
            "voucher": {
                "codigo": voucher_atualizado.codigo,
                "status": voucher_atualizado.status,
                "checkoutRealizadoEm": voucher_atualizado.checkoutRealizadoEm
            },
            "reserva": reserva
        }
    }


@router.post("/gerar/{reserva_id}")
async def gerar_voucher_manual(
    reserva_id: int,
    funcionario_id: int = Body(...),
    current_user: User = Depends(get_current_active_user)
):
    """
    Gerar voucher manualmente para uma reserva
    
    Normalmente o voucher é gerado automaticamente após pagamento,
    mas esta rota permite geração manual se necessário
    """
    
    voucher = await gerar_voucher(reserva_id, funcionario_id)
    
    return {
        "success": True,
        "message": f"Voucher {voucher['codigo']} gerado com sucesso",
        "data": voucher
    }


@router.get("")
async def listar_vouchers(
    status: str = None,
    limit: int = 100,
    offset: int = 0
):
    """Listar vouchers com filtros"""
    
    db = get_db()
    
    where = {}
    if status:
        where['status'] = status
    
    vouchers = await db.voucher.find_many(
        where=where,
        include={
            'reserva': {
                'include': {
                    'cliente': True
                }
            }
        },
        order_by={'dataEmissao': 'desc'},
        take=limit,
        skip=offset
    )
    
    total = await db.voucher.count(where=where)
    
    return {
        "success": True,
        "data": vouchers,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/{codigo}/pdf")
async def gerar_pdf_voucher(codigo: str):
    """Gerar PDF do voucher para impressão/download"""
    
    db = get_db()
    
    # Buscar voucher completo
    voucher = await db.voucher.find_first(
        where={'codigo': codigo.upper()},
        include={
            'reserva': {
                'include': {
                    'cliente': True,
                    'pagamentos': True
                }
            }
        }
    )
    
    if not voucher:
        raise HTTPException(
            status_code=404,
            detail=f"Voucher {codigo} não encontrado"
        )
    
    # Criar PDF em memória
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=1,  # center
        textColor=colors.darkblue
    )
    
    code_style = ParagraphStyle(
        'CodeStyle',
        parent=styles['Heading2'],
        fontSize=32,
        spaceAfter=20,
        alignment=1,
        textColor=colors.red,
        borderWidth=2,
        borderColor=colors.red,
        borderRadius=10,
        backColor=colors.lightgrey
    )
    
    # Conteúdo do PDF
    story = []
    
    # Cabeçalho
    story.append(Paragraph("🏨 Hotel Real - Cabo Frio", title_style))
    story.append(Spacer(1, 20))
    
    # Código do Voucher (CENTRALIZADO E DESTACADO)
    story.append(Paragraph("VOUCHER DE CONFIRMAÇÃO", styles['Heading2']))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"<b>{voucher.codigo}</b>", code_style))
    story.append(Spacer(1, 20))
    
    # Status
    status_color = {
        'EMITIDO': colors.green,
        'CHECKIN_REALIZADO': colors.blue,
        'FINALIZADO': colors.grey,
        'CANCELADO': colors.red
    }.get(voucher.status, colors.black)
    
    status_style = ParagraphStyle(
        'StatusStyle',
        parent=styles['Normal'],
        fontSize=14,
        alignment=1,
        textColor=status_color,
        borderWidth=1,
        borderColor=status_color,
        borderRadius=5,
        backColor=colors.lightgrey
    )
    
    story.append(Paragraph(f"<b>STATUS: {voucher.status}</b>", status_style))
    story.append(Spacer(1, 20))
    
    # Dados da Reserva
    story.append(Paragraph("DADOS DA RESERVA", styles['Heading2']))
    story.append(Spacer(1, 12))
    
    reserva_data = [
        ['Código Reserva:', voucher.reserva.codigoReserva],
        ['Hóspede:', voucher.reserva.clienteNome],
        ['Tipo Suíte:', voucher.reserva.tipoSuite],
        ['Quarto:', voucher.reserva.quartoNumero],
        ['Check-in:', datetime.fromisoformat(voucher.reserva.checkinPrevisto).strftime('%d/%m/%Y %H:%M')],
        ['Check-out:', datetime.fromisoformat(voucher.reserva.checkoutPrevisto).strftime('%d/%m/%Y %H:%M')],
        ['Valor Total:', f"R$ {float(voucher.reserva.valorDiaria or 0) * voucher.reserva.numDiarias:.2f}"],
    ]
    
    tabela_reserva = Table(reserva_data, colWidths=[4*cm, 8*cm])
    tabela_reserva.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    
    story.append(tabela_reserva)
    story.append(Spacer(1, 20))
    
    # Dados do Cliente
    if voucher.reserva.cliente:
        story.append(Paragraph("DADOS DO HÓSPEDE", styles['Heading2']))
        story.append(Spacer(1, 12))
        
        cliente_data = [
            ['Nome Completo:', voucher.reserva.cliente.nomeCompleto],
            ['Email:', voucher.reserva.cliente.email],
            ['Telefone:', voucher.reserva.cliente.telefone],
        ]
        
        tabela_cliente = Table(cliente_data, colWidths=[4*cm, 8*cm])
        tabela_cliente.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        story.append(tabela_cliente)
        story.append(Spacer(1, 20))
    
    # Controle de Check-in/Check-out
    story.append(Paragraph("CONTROLE DE ACESSO", styles['Heading2']))
    story.append(Spacer(1, 12))
    
    controle_data = [
        ['Emissão:', datetime.fromisoformat(voucher.dataEmissao).strftime('%d/%m/%Y %H:%M')],
        ['Check-in:', voucher.checkinRealizadoEm and datetime.fromisoformat(voucher.checkinRealizadoEm).strftime('%d/%m/%Y %H:%M') or '⏳ Aguardando'],
        ['Check-out:', voucher.checkoutRealizadoEm and datetime.fromisoformat(voucher.checkoutRealizadoEm).strftime('%d/%m/%Y %H:%M') or '⏳ Aguardando'],
    ]
    
    tabela_controle = Table(controle_data, colWidths=[4*cm, 8*cm])
    tabela_controle.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.lightgreen),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    
    story.append(tabela_controle)
    story.append(Spacer(1, 30))
    
    # Rodapé
    story.append(Paragraph("📍 Endereço: Av. do Mar, 1234 - Cabo Frio, RJ", styles['Normal']))
    story.append(Paragraph("📞 Telefone: (22) 1234-5678 | 📧 contato@hotelreal.com.br", styles['Normal']))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Este voucher é válido apenas para a reserva identificada acima.", styles['Normal']))
    story.append(Paragraph("Apresente este voucher no momento do check-in.", styles['Normal']))
    
    # Gerar PDF
    doc.build(story)
    
    # Preparar resposta
    buffer.seek(0)
    
    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=voucher_{voucher.codigo}.pdf"
        }
    )
