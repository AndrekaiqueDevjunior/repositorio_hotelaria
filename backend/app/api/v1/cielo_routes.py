from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.core.database import get_db
from app.services.cielo_service import cielo_api

router = APIRouter(prefix="/cielo", tags=["cielo"])


@router.get("/status")
async def obter_status_cielo():
    """Retorna status básico da integração com a Cielo"""
    success = bool(cielo_api.merchant_id and cielo_api.merchant_key)
    return {
        "success": success,
        "mode": cielo_api.mode,
        "status": "Credenciais configuradas" if success else "Credenciais ausentes",
        "merchant_id": cielo_api.merchant_id,
        "api_base_url": cielo_api.base_url,
        "timeout": f"{cielo_api.timeout}s",
    }


async def _enriquecer_com_cliente(transacoes):
    """Adiciona dados reais do cliente às transações simuladas"""
    if not transacoes:
        return transacoes

    db = get_db()
    try:
        await db.connect()
    except Exception:
        pass

    # Cache simples para evitar buscar o mesmo cliente várias vezes
    cliente_cache = {}

    for tx in transacoes:
        if not isinstance(tx, dict):
            continue
        order_id = tx.get("MerchantOrderId")
        if not order_id:
            continue

        reserva = await db.reserva.find_unique(where={"codigoReserva": order_id})
        if not reserva:
            continue

        cliente = cliente_cache.get(reserva.clienteId)
        if not cliente:
            cliente = await db.cliente.find_unique(where={"id": reserva.clienteId})
            cliente_cache[reserva.clienteId] = cliente

        customer_name = reserva.clienteNome or (cliente.nomeCompleto if cliente else None)
        customer_identity = cliente.documento if cliente else None
        customer_email = cliente.email if cliente else None

        tx["Customer"] = {
            "Name": customer_name,
            "Identity": customer_identity,
            "Email": customer_email,
        }

    return transacoes


@router.get("/historico")
async def listar_transacoes_cielo(
    data_inicio: Optional[str] = Query(None),
    data_fim: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """Lista transações na Cielo (dados simulados em sandbox)"""
    resultado = cielo_api.consultar_vendas(data_inicio, data_fim, page, page_size)
    if not resultado.get("success"):
        raise HTTPException(status_code=400, detail=resultado.get("error", "Erro ao consultar Cielo"))

    resultado["data"] = await _enriquecer_com_cliente(resultado.get("data", []))
    return resultado


@router.get("/pagamento/{payment_id}")
async def consultar_pagamento_cielo(payment_id: str):
    """Consulta um pagamento específico na Cielo"""
    resultado = cielo_api.consultar_pagamento(payment_id)
    if not resultado.get("success"):
        raise HTTPException(status_code=400, detail=resultado.get("error", "Erro ao consultar pagamento na Cielo"))

    enriched = await _enriquecer_com_cliente([resultado.get("data", {})])
    resultado["data"] = enriched[0] if enriched else resultado.get("data")
    return resultado

