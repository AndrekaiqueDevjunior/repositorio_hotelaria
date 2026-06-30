"""
Rotas de Vouchers
Gerencia vouchers de confirmação de reserva
"""

from fastapi import APIRouter, HTTPException, Depends, Body, Response
from pydantic import BaseModel
from datetime import datetime
from typing import Any, Optional
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
    cpf_titular: str = None
    confirmar_divergencia_cpf: bool = False


def _format_datetime(value: Any) -> str:
    if not value:
        return "-"
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return value
    try:
        return value.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return str(value)


def _valor_total_reserva(reserva) -> float:
    valor_total = getattr(reserva, "valorTotal", None)
    if valor_total is not None:
        return float(valor_total)
    return float(getattr(reserva, "valorDiaria", 0) or 0) * int(getattr(reserva, "numDiarias", 0) or 0)


def _ultimo_pagamento_confirmado(reserva) -> Optional[Any]:
    pagamentos = getattr(reserva, "pagamentos", None) or []
    for pagamento in pagamentos:
        if getattr(pagamento, "statusPagamento", None) in ("PAGO", "CONFIRMADO", "APROVADO"):
            return pagamento
    return pagamentos[0] if pagamentos else None


def _forma_pagamento_reserva(reserva) -> str:
    forma = getattr(reserva, "formaPagamento", None)
    if forma:
        return str(forma)
    pagamento = _ultimo_pagamento_confirmado(reserva)
    if pagamento:
        metodo = getattr(pagamento, "metodo", None)
        status = getattr(pagamento, "statusPagamento", None)
        return f"{metodo or '-'} ({status or '-'})"
    return "-"


def _email_contato(reserva) -> Optional[str]:
    return getattr(reserva, "emailContato", None) or getattr(getattr(reserva, "cliente", None), "email", None)


def _telefone_contato(reserva) -> Optional[str]:
    return getattr(reserva, "telefoneContato", None) or getattr(getattr(reserva, "cliente", None), "telefone", None)


@router.get("/reserva/{reserva_id}")
async def obter_voucher_por_reserva(
    reserva_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Obter voucher de uma reserva"""
    
    db = get_db()
    
    voucher = await db.voucher.find_first(
        where={'reservaId': reserva_id},
        include={
            'reserva': {
                'include': {
                    'cliente': True,
                    'pagamentos': True,
                    'hospedagem': True
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
                "valorTotal": _valor_total_reserva(voucher.reserva),
                "formaPagamento": _forma_pagamento_reserva(voucher.reserva),
                "origem": getattr(voucher.reserva, "origem", None),
                "responsavelNome": getattr(voucher.reserva, "responsavelNome", None),
                "observacoes": getattr(voucher.reserva, "observacoes", None),
                "status": getattr(voucher.reserva, "statusReserva", None) or getattr(voucher.reserva, "status", None),
                "cliente": {
                    "nomeCompleto": voucher.reserva.cliente.nomeCompleto,
                    "email": _email_contato(voucher.reserva),
                    "telefone": _telefone_contato(voucher.reserva)
                },
                "hospedagem": {
                    "checkinRealizadoEm": getattr(getattr(voucher.reserva, "hospedagem", None), "checkinRealizadoEm", None),
                    "checkoutRealizadoEm": getattr(getattr(voucher.reserva, "hospedagem", None), "checkoutRealizadoEm", None),
                    "assinaturaCheckinRegistrada": bool(getattr(getattr(voucher.reserva, "hospedagem", None), "assinaturaCheckin", None)),
                    "assinaturaCheckoutRegistrada": bool(getattr(getattr(voucher.reserva, "hospedagem", None), "assinaturaCheckout", None))
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
                    'pagamentos': True,
                    'hospedagem': True
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
                "valorTotal": _valor_total_reserva(voucher.reserva),
                "formaPagamento": _forma_pagamento_reserva(voucher.reserva),
                "origem": getattr(voucher.reserva, "origem", None),
                "responsavelNome": getattr(voucher.reserva, "responsavelNome", None),
                "observacoes": getattr(voucher.reserva, "observacoes", None),
                "status": getattr(voucher.reserva, "statusReserva", None) or getattr(voucher.reserva, "status", None),
                "cliente": {
                    "nomeCompleto": voucher.reserva.cliente.nomeCompleto,
                    "email": _email_contato(voucher.reserva),
                    "telefone": _telefone_contato(voucher.reserva)
                },
                "hospedagem": {
                    "checkinRealizadoEm": getattr(getattr(voucher.reserva, "hospedagem", None), "checkinRealizadoEm", None),
                    "checkoutRealizadoEm": getattr(getattr(voucher.reserva, "hospedagem", None), "checkoutRealizadoEm", None),
                    "assinaturaCheckinRegistrada": bool(getattr(getattr(voucher.reserva, "hospedagem", None), "assinaturaCheckin", None)),
                    "assinaturaCheckoutRegistrada": bool(getattr(getattr(voucher.reserva, "hospedagem", None), "assinaturaCheckout", None))
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
    try:
        await hospedagem_repo.checkout(
            reserva_id=voucher_data['reservaId'],
            funcionario_id=request.funcionario_id,
            cpf_titular=request.cpf_titular,
            confirmar_divergencia_cpf=request.confirmar_divergencia_cpf,
        )
    except ValueError as e:
        mensagem = str(e)
        if mensagem.startswith("CPF_DIVERGENTE:"):
            raise HTTPException(
                status_code=409,
                detail={
                    "codigo": "CPF_DIVERGENTE",
                    "mensagem": mensagem.replace("CPF_DIVERGENTE: ", ""),
                    "requer_confirmacao": True,
                },
            )
        raise HTTPException(status_code=400, detail=mensagem)
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
    funcionario_id: int = Body(..., embed=True),
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
    offset: int = 0,
    current_user: User = Depends(get_current_active_user)
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
                    'pagamentos': True,
                    'hospedagem': True
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
        ['Reserva feita por:', getattr(voucher.reserva, "responsavelNome", None) or "-"],
        ['Origem:', getattr(voucher.reserva, "origem", None) or "-"],
        ['Observacao:', getattr(voucher.reserva, "observacoes", None) or "-"],
        ['Código Reserva:', voucher.reserva.codigoReserva],
        ['Hóspede:', voucher.reserva.clienteNome],
        ['Tipo Suíte:', voucher.reserva.tipoSuite],
        ['Quarto:', voucher.reserva.quartoNumero],
        ['Check-in:', _format_datetime(voucher.reserva.checkinPrevisto)],
        ['Check-out:', _format_datetime(voucher.reserva.checkoutPrevisto)],
        ['Forma de pagamento:', _forma_pagamento_reserva(voucher.reserva)],
        ['Valor Total:', f"R$ {_valor_total_reserva(voucher.reserva):.2f}"],
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
            ['Email:', _email_contato(voucher.reserva) or "-"],
            ['Telefone:', _telefone_contato(voucher.reserva) or "-"],
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
    
    hospedagem = getattr(voucher.reserva, "hospedagem", None)
    checkin_realizado = getattr(hospedagem, "checkinRealizadoEm", None) or getattr(voucher, "checkinRealizadoEm", None)
    checkout_realizado = getattr(hospedagem, "checkoutRealizadoEm", None) or getattr(voucher, "checkoutRealizadoEm", None)
    controle_data = [
        ['Emissao:', _format_datetime(voucher.dataEmissao)],
        ['Check-in:', _format_datetime(checkin_realizado) if checkin_realizado else 'Aguardando'],
        ['Assinatura check-in:', 'Registrada' if getattr(hospedagem, "assinaturaCheckin", None) else 'Pendente'],
        ['Check-out:', _format_datetime(checkout_realizado) if checkout_realizado else 'Aguardando'],
        ['Assinatura check-out:', 'Registrada' if getattr(hospedagem, "assinaturaCheckout", None) else 'Pendente'],
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
