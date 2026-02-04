"""
Serviço de Vouchers
Gerencia geração e validação de vouchers de confirmação
"""

from datetime import datetime
from typing import Dict, Any
from fastapi import HTTPException
from app.core.database import get_db


async def gerar_voucher(reserva_id: int, emitido_por: int = None) -> Dict[str, Any]:
    """
    Gerar voucher para reserva confirmada
    
    Args:
        reserva_id: ID da reserva
        emitido_por: ID do funcionário que emitiu (opcional)
    
    Returns:
        Voucher criado
    """
    db = get_db()
    
    # Verificar se reserva existe
    reserva = await db.reserva.find_unique(
        where={'id': reserva_id},
        include={'cliente': True}
    )
    
    if not reserva:
        raise HTTPException(
            status_code=404,
            detail=f"Reserva {reserva_id} não encontrada"
        )
    
    # Verificar se já existe voucher
    voucher_existente = await db.voucher.find_first(
        where={'reservaId': reserva_id}
    )
    
    if voucher_existente:
        print(f"[VOUCHER] Voucher já existe para reserva {reserva_id}: {voucher_existente.codigo}")
        return {
            "id": voucher_existente.id,
            "codigo": voucher_existente.codigo,
            "reservaId": voucher_existente.reservaId,
            "status": voucher_existente.status,
            "dataEmissao": voucher_existente.dataEmissao,
            "reserva": reserva
        }
    
    # Gerar código único
    from app.utils.datetime_utils import now_utc
    ano = now_utc().year
    total_vouchers = await db.voucher.count()
    sequencial = total_vouchers + 1
    codigo = f"HR-{ano}-{sequencial:06d}"
    
    # Criar voucher
    voucher = await db.voucher.create(
        data={
            'codigo': codigo,
            'reservaId': reserva_id,
            'status': 'EMITIDO',
            'dataEmissao': now_utc(),
            'emitidoPor': emitido_por
        }
    )
    
    print(f"[VOUCHER] Voucher gerado: {codigo} para reserva {reserva_id}")
    
    return {
        "id": voucher.id,
        "codigo": voucher.codigo,
        "reservaId": voucher.reservaId,
        "status": voucher.status,
        "dataEmissao": voucher.dataEmissao,
        "reserva": reserva
    }


async def validar_voucher_checkin(codigo: str) -> Dict[str, Any]:
    """
    Validar voucher para check-in
    
    Args:
        codigo: Código do voucher
    
    Returns:
        Voucher validado com dados da reserva
    """
    db = get_db()
    
    # Buscar voucher
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
    
    # Verificar status do voucher
    if voucher.status == "CANCELADO":
        raise HTTPException(
            status_code=400,
            detail="Voucher cancelado"
        )
    
    if voucher.status == "FINALIZADO":
        raise HTTPException(
            status_code=400,
            detail="Voucher já finalizado"
        )
    
    if voucher.status == "CHECKIN_REALIZADO":
        raise HTTPException(
            status_code=400,
            detail="Check-in já realizado"
        )
    
    # Verificar pagamento - aceitar múltiplos status da Cielo
    reserva = voucher.reserva
    
    # Status aceitos: Cielo Sandbox e produção
    STATUS_PAGAMENTO_VALIDOS = (
        "APROVADO", "PAGO", "CONFIRMADO",  # Status genéricos
        "CAPTURED", "AUTHORIZED", "PAID",   # Status Cielo
        "PaymentConfirmed", "Authorized"    # Status Cielo API
    )
    
    pagamento_confirmado = any(
        (getattr(p, 'statusPagamento', None) in STATUS_PAGAMENTO_VALIDOS) or 
        (getattr(p, 'status', None) in STATUS_PAGAMENTO_VALIDOS) or
        (getattr(p, 'status_pagamento', None) in STATUS_PAGAMENTO_VALIDOS) or
        (getattr(p, 'payment_status', None) in STATUS_PAGAMENTO_VALIDOS)
        for p in reserva.pagamentos
    )
    
    if not pagamento_confirmado:
        # Log para debug - MELHORADO: Tratar diferentes estruturas de pagamento
        status_encontrados = []
        for p in reserva.pagamentos:
            # Tentar diferentes atributos de status
            status_valores = []
            
            # Verificar atributos possíveis
            if hasattr(p, 'status'):
                status_valores.append(("status", getattr(p, "status")))
            if hasattr(p, 'statusPagamento'):
                status_valores.append(("statusPagamento", getattr(p, "statusPagamento")))
            if hasattr(p, 'status_pagamento'):
                status_valores.append(("status_pagamento", getattr(p, "status_pagamento")))
            
            # Adicionar dicionário com todos os status encontrados
            status_dict = {}
            for attr_name, attr_value in status_valores:
                status_dict[attr_name] = attr_value
            
            # Se não encontrou nenhum status, adicionar indicador
            if not status_dict:
                status_dict = {"erro": "Nenhum atributo de status encontrado"}
            
            status_encontrados.append(status_dict)
        
        print(f"[VOUCHER] Pagamentos encontrados: {status_encontrados}")
        
        # Melhorar mensagem de erro
        if not status_encontrados:
            raise HTTPException(
                status_code=400,
                detail="Nenhum pagamento encontrado para esta reserva."
            )
        
        raise HTTPException(
            status_code=400,
            detail=f"Pagamento não confirmado. Status encontrados: {status_encontrados}. Regularize o pagamento antes do check-in."
        )
    
    # Verificar data (permitir check-in 1 dia antes ou depois)
    from app.utils.datetime_utils import now_utc
    hoje = now_utc().date()
    checkin_previsto = reserva.checkinPrevisto.date() if isinstance(reserva.checkinPrevisto, datetime) else reserva.checkinPrevisto
    
    diferenca = abs((checkin_previsto - hoje).days)
    if diferenca > 1:
        raise HTTPException(
            status_code=400,
            detail=f"Check-in previsto para {checkin_previsto}. Hoje é {hoje}."
        )
    
    return {
        "id": voucher.id,
        "codigo": voucher.codigo,
        "reservaId": voucher.reservaId,
        "status": voucher.status,
        "reserva": reserva
    }


async def validar_voucher_checkout(codigo: str) -> Dict[str, Any]:
    """
    Validar voucher para check-out
    
    Args:
        codigo: Código do voucher
    
    Returns:
        Voucher validado
    """
    db = get_db()
    
    voucher = await db.voucher.find_first(
        where={'codigo': codigo.upper()},
        include={'reserva': True}
    )
    
    if not voucher:
        raise HTTPException(
            status_code=404,
            detail=f"Voucher {codigo} não encontrado"
        )
    
    if voucher.status != "CHECKIN_REALIZADO":
        raise HTTPException(
            status_code=400,
            detail=f"Check-in não foi realizado. Status atual: {voucher.status}"
        )
    
    return {
        "id": voucher.id,
        "codigo": voucher.codigo,
        "reservaId": voucher.reservaId,
        "status": voucher.status,
        "reserva": voucher.reserva
    }
