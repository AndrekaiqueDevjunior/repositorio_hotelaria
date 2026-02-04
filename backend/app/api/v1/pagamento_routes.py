from fastapi import APIRouter, Depends, HTTPException, Request, Header
from app.schemas.pagamento_schema import PagamentoCreate, PagamentoResponse, CieloWebhook
from app.services.pagamento_service import PagamentoService
from app.repositories.pagamento_repo import PagamentoRepository
from app.core.database import get_db
from app.middleware.auth_middleware import get_current_active_user, require_admin_or_manager
from app.core.security import User
from app.middleware.idempotency import check_idempotency, store_idempotency_result
from typing import List, Optional
from starlette.responses import JSONResponse
import os
import ipaddress

router = APIRouter(prefix="/pagamentos", tags=["pagamentos"])

# IPs autorizados da Cielo para webhooks (produção)
# Fonte: Documentação Cielo E-commerce
CIELO_ALLOWED_IPS = [
    "200.155.86.0/24",
    "200.155.87.0/24",
    "200.229.32.0/24",
]

def is_cielo_ip_allowed(client_ip: str) -> bool:
    """Verificar se IP do cliente está na lista de IPs autorizados da Cielo"""
    # Em desenvolvimento/sandbox, permitir qualquer IP
    if os.getenv("CIELO_MODE", "sandbox") == "sandbox":
        return True
    
    try:
        ip = ipaddress.ip_address(client_ip)
        for network in CIELO_ALLOWED_IPS:
            if ip in ipaddress.ip_network(network):
                return True
        return False
    except ValueError:
        return False

# Dependency injection
async def get_pagamento_service() -> PagamentoService:
    from app.repositories.reserva_repo import ReservaRepository
    db = get_db()
    return PagamentoService(
        PagamentoRepository(db),
        ReservaRepository(db)
    )

@router.get("", response_model=dict)
async def listar_pagamentos(
    service: PagamentoService = Depends(get_pagamento_service),
    current_user: User = Depends(get_current_active_user)
):
    """Listar todos os pagamentos - Requer autenticação"""
    return await service.list_all()

@router.post("", response_model=PagamentoResponse)
async def criar_pagamento(
    pagamento: PagamentoCreate,
    request: Request,
    service: PagamentoService = Depends(get_pagamento_service),
    current_user: User = Depends(get_current_active_user),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
):
    """
    Criar novo pagamento com proteção de idempotência - P0-003
    
    Headers:
        Idempotency-Key: UUID único (OBRIGATÓRIO para evitar pagamentos duplicados)
    
    Retorna:
        201 Created com dados do pagamento
    """
    
    # P0-003: CAMADA 1 - Verificar idempotência (CRÍTICO para pagamentos)
    if idempotency_key:
        cached = await check_idempotency(f"pag:{idempotency_key}")
        if cached:
            return JSONResponse(
                content=cached["body"],
                status_code=cached["status_code"]
            )
    
    # P0-003: CAMADA 2 - Criar pagamento
    try:
        resultado = await service.create(pagamento)
        
        # P0-003: CAMADA 3 - Cachear resultado da idempotência
        if idempotency_key:
            await store_idempotency_result(
                f"pag:{idempotency_key}", 
                resultado, 
                status_code=201
            )
        
        return JSONResponse(content=resultado, status_code=201)
        
    except Exception as e:
        # Mesmo em caso de erro, cachear para evitar retry infinito
        if idempotency_key:
            error_result = {"error": str(e), "success": False}
            await store_idempotency_result(
                f"pag:{idempotency_key}", 
                error_result, 
                status_code=400
            )
        raise

@router.get("/{pagamento_id}", response_model=PagamentoResponse)
async def obter_pagamento(
    pagamento_id: int,
    service: PagamentoService = Depends(get_pagamento_service),
    current_user: User = Depends(get_current_active_user)
):
    """Obter pagamento por ID - Requer autenticação"""
    return await service.get_by_id(pagamento_id)

@router.get("/cielo/{payment_id}", response_model=PagamentoResponse)
async def obter_pagamento_por_cielo_id(
    payment_id: str,
    service: PagamentoService = Depends(get_pagamento_service),
    current_user: User = Depends(get_current_active_user)
):
    """Obter pagamento pelo ID da Cielo - Requer autenticação"""
    return await service.get_by_payment_id(payment_id)

@router.get("/reserva/{reserva_id}", response_model=List[PagamentoResponse])
async def listar_pagamentos_reserva(
    reserva_id: int,
    service: PagamentoService = Depends(get_pagamento_service),
    current_user: User = Depends(get_current_active_user)
):
    """Listar pagamentos de uma reserva - Requer autenticação"""
    return await service.list_by_reserva(reserva_id)

@router.post("/{pagamento_id}/cancelar", response_model=PagamentoResponse, deprecated=True)
async def cancelar_pagamento_legacy(
    pagamento_id: int,
    service: PagamentoService = Depends(get_pagamento_service),
    current_user: User = Depends(require_admin_or_manager)
):
    """[DEPRECATED] Use PATCH /{pagamento_id} com status='CANCELADO'"""
    return await service.cancelar_pagamento(pagamento_id)

@router.get("/{pagamento_id}/status", response_model=dict)
async def verificar_status_pagamento(
    pagamento_id: int,
    service: PagamentoService = Depends(get_pagamento_service),
    current_user: User = Depends(get_current_active_user)
):
    """Verificar status de pagamento PIX - Requer autenticação"""
    return await service.verificar_status_pix(pagamento_id)

@router.post("/{pagamento_id}/confirmar-pix", response_model=dict)
async def confirmar_pix_manual(
    pagamento_id: int,
    service: PagamentoService = Depends(get_pagamento_service),
    current_user: User = Depends(require_admin_or_manager)
):
    """Confirmar pagamento PIX manualmente (sandbox/testes) - Requer ADMIN ou GERENTE"""
    return await service.confirmar_pix_manual(pagamento_id)

@router.patch("/{pagamento_id}", response_model=PagamentoResponse)
async def atualizar_pagamento_parcial(
    pagamento_id: int,
    pagamento_data: dict,
    service: PagamentoService = Depends(get_pagamento_service),
    current_user: User = Depends(require_admin_or_manager)
):
    """
    Atualizar pagamento parcialmente (REST-compliant)
    
    Operações suportadas:
    - {"status": "CANCELADO"} - Cancelar pagamento
    - {"status": "APROVADO"} - Aprovar pagamento e creditar pontos
    """
    if "status" in pagamento_data:
        status = pagamento_data["status"]
        if status == "CANCELADO":
            return await service.cancelar_pagamento(pagamento_id)
        elif status == "APROVADO":
            return await service.aprovar_pagamento(pagamento_id)
    
    raise HTTPException(status_code=400, detail="Operação não suportada. Use status='APROVADO' ou status='CANCELADO'")


@router.post("/{pagamento_id}/aprovar", response_model=PagamentoResponse)
async def aprovar_pagamento(
    pagamento_id: int,
    service: PagamentoService = Depends(get_pagamento_service),
    current_user: User = Depends(require_admin_or_manager)
):
    """
    Aprovar pagamento manualmente e creditar pontos automaticamente.
    
    Este endpoint:
    1. Atualiza o status do pagamento para APROVADO
    2. Confirma a reserva associada
    3. Credita pontos de fidelidade ao cliente (1 ponto por R$ 10)
    4. Gera voucher automaticamente
    
    Requer: ADMIN ou GERENTE
    """
    return await service.aprovar_pagamento(pagamento_id)

# Webhook da Cielo
@router.post("/webhook/cielo", response_model=PagamentoResponse)
async def cielo_webhook(
    request: Request,
    webhook_data: CieloWebhook,
    service: PagamentoService = Depends(get_pagamento_service)
):
    """
    Processar webhook da Cielo
    
    SEGURANÇA: Em produção, valida se a requisição vem de IPs autorizados da Cielo.
    Em sandbox, permite qualquer IP para facilitar testes.
    """
    client_ip = request.client.host if request.client else "unknown"
    
    if not is_cielo_ip_allowed(client_ip):
        raise HTTPException(
            status_code=403, 
            detail=f"IP {client_ip} não autorizado para webhooks Cielo"
        )
    
    return await service.process_webhook(webhook_data)