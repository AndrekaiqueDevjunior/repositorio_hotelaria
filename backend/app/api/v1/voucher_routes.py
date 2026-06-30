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
    """Gerar PDF do voucher no formato padrao do Hotel Real"""

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
        raise HTTPException(status_code=404, detail=f"Voucher {codigo} nao encontrado")

    reserva = voucher.reserva
    hospedagem = getattr(reserva, "hospedagem", None)

    # Dados da reserva
    responsavel = getattr(reserva, "responsavelNome", None) or reserva.clienteNome or "-"
    quarto = reserva.quartoNumero or "-"
    tipo_suite = reserva.tipoSuite or "-"
    obs = getattr(reserva, "observacoes", None) or "Particular"
    valor = _valor_total_reserva(reserva)
    valor_fmt = f"R${valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def fmt_date_only(val):
        s = _format_datetime(val)
        return s.split(" ")[0] if " " in s else s

    def fmt_time_only(val):
        s = _format_datetime(val)
        parts = s.split(" ")
        return parts[1] if len(parts) > 1 else "-"

    checkin_data = fmt_date_only(reserva.checkinPrevisto)
    checkout_data = fmt_date_only(reserva.checkoutPrevisto)

    checkin_realizado_em = getattr(hospedagem, "checkinRealizadoEm", None) or getattr(voucher, "checkinRealizadoEm", None)
    checkout_realizado_em = getattr(hospedagem, "checkoutRealizadoEm", None) or getattr(voucher, "checkoutRealizadoEm", None)
    horario_checkin = fmt_time_only(checkin_realizado_em) if checkin_realizado_em else "-"

    guest_name = reserva.clienteNome or (reserva.cliente.nomeCompleto if reserva.cliente else "-")

    # --- Build PDF ---
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=2*cm, bottomMargin=2*cm,
        leftMargin=2.5*cm, rightMargin=2.5*cm
    )

    styles = getSampleStyleSheet()

    s_hotel_name = ParagraphStyle('HN', parent=styles['Normal'],
        fontSize=16, fontName='Helvetica-Bold', spaceAfter=4)
    s_info = ParagraphStyle('HI', parent=styles['Normal'],
        fontSize=9, fontName='Helvetica-Bold', leading=14)
    s_title = ParagraphStyle('TI', parent=styles['Normal'],
        fontSize=14, fontName='Helvetica-Bold', alignment=1,
        spaceBefore=18, spaceAfter=14)
    s_field = ParagraphStyle('FI', parent=styles['Normal'],
        fontSize=10, fontName='Helvetica', leading=16)
    s_bold = ParagraphStyle('FB', parent=styles['Normal'],
        fontSize=10, fontName='Helvetica-Bold', leading=16)
    s_guest_label = ParagraphStyle('GL', parent=styles['Normal'],
        fontSize=11, fontName='Helvetica-Bold', spaceBefore=14, spaceAfter=2)
    s_guest_name = ParagraphStyle('GN', parent=styles['Normal'],
        fontSize=11, fontName='Helvetica', spaceAfter=20)
    s_section = ParagraphStyle('SC', parent=styles['Normal'],
        fontSize=11, fontName='Helvetica-Bold', spaceBefore=14, spaceAfter=6)
    s_line = ParagraphStyle('LN', parent=styles['Normal'],
        fontSize=10, fontName='Helvetica', spaceAfter=6)

    story = []

    # ── CABECALHO ──
    story.append(Paragraph("Hotel Real", s_hotel_name))
    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>Endereco:</b> Rua Enfermeiro Ricardo Sanches- 22", s_info))
    story.append(Paragraph("<b>Bairro:</b> Braga- <b>Cidade:</b> Cabo Frio- <b>Estado:</b> RJ", s_info))
    story.append(Paragraph("<b>CEP:</b> 28.908-040  <b>CNPJ:</b> 29.269.359/0001-40", s_info))
    story.append(Paragraph("<b>Fone:</b> (22) 2648-5900", s_info))
    story.append(Paragraph("<b>E-mail:</b> Contato@hotelrealcabofrio.com.br", s_info))

    # ── TITULO ──
    story.append(Paragraph("Informacoes referentes a reserva individual", s_title))

    # ── DADOS DA RESERVA (layout em tabela 2 colunas para alinhar Apto a direita) ──
    page_w = A4[0] - 5*cm  # largura util
    col_left = page_w * 0.7
    col_right = page_w * 0.3

    row1 = [
        Paragraph(f"<b>Reserva feita por:</b> {responsavel}", s_field),
        Paragraph(f"<b>Apto:</b> {quarto}", s_field),
    ]
    row2 = [
        Paragraph(f"<b>Tipo de suite:</b> {tipo_suite}", s_field),
        Paragraph("", s_field),
    ]
    row3 = [
        Paragraph(f"<b>Entrada:</b> {checkin_data}    <b>Saida:</b> {checkout_data}", s_field),
        Paragraph("", s_field),
    ]
    row4 = [
        Paragraph(f"<b>Valor Total:</b> {valor_fmt}", s_field),
        Paragraph("", s_field),
    ]
    row5 = [
        Paragraph(f"<b>Obs:</b> {obs}", s_field),
        Paragraph("", s_field),
    ]
    row6 = [
        Paragraph(f"Check-in Por:                          Horario: {horario_checkin}", s_field),
        Paragraph("", s_field),
    ]

    tbl = Table([row1, row2, row3, row4, row5, row6], colWidths=[col_left, col_right])
    tbl.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(tbl)

    # ── HOSPEDE ──
    story.append(Paragraph("<b>Hospede:</b>", s_guest_label))
    story.append(Paragraph(guest_name, s_guest_name))

    # ── CARRO ──
    car_data = [
        [Paragraph("Carro  □ Sim  □ Nao", s_field)],
        [Paragraph("Placa________________", s_field)],
    ]
    car_tbl = Table(car_data, colWidths=[8*cm])
    car_tbl.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.75, colors.black),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(car_tbl)

    # ── CHECK-IN ──
    story.append(Paragraph("<b>Check-in</b>", s_section))
    story.append(Paragraph("Ass:______________________________________________________________________________", s_line))
    story.append(Paragraph("Data:___/___/_____", s_line))
    story.append(Spacer(1, 14))

    # ── CHECK-OUT ──
    story.append(Paragraph("<b>Check-out</b>", s_section))
    story.append(Paragraph("Ass:______________________________________________________________________________", s_line))
    story.append(Paragraph("Data:___/___/_____    Hora: ___:___", s_line))

    doc.build(story)
    buffer.seek(0)

    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename=voucher_{reserva.codigoReserva}.pdf"}
    )
