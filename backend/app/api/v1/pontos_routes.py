from fastapi import APIRouter, Depends, HTTPException, Request
from app.schemas.pontos_schema import (
    AjustarPontosRequest, SaldoResponse, TransacaoResponse,
    ValidarReservaRequest, ConfirmarLancamentoRequest,
    GerarConviteRequest, UsarConviteRequest,
    ValidarReservaResponse, ConviteResponse
)
from app.services.pontos_service import PontosService, get_pontos_service as _get_pontos_service
from app.services.real_points_service import RealPointsService
from app.repositories.pontos_repo import PontosRepository
from app.repositories.pontos_repo_atomic import PontosRepositoryAtomic
from app.repositories.reserva_repo import ReservaRepository
from app.repositories.cliente_repo import ClienteRepository
from app.core.database import get_db
from app.middleware.auth_middleware import get_current_active_user, require_admin_or_manager
from app.core.security import User
from app.middleware.rate_limit import rate_limit_strict, rate_limit_moderate
from typing import List, Optional
from datetime import datetime, timezone
from app.schemas.pontos_regras_schema import PontosRegraCreateRequest, PontosRegraUpdateRequest, PontosRegraResponse
from app.repositories.pontos_regras_repo import PontosRegrasRepository
import os
import httpx

router = APIRouter(prefix="/pontos", tags=["pontos"])

# Dependency injection
async def get_pontos_service() -> PontosService:
    return await _get_pontos_service()

async def _validar_recaptcha_publico(request: Request, action_esperada: str) -> None:
    secret = (os.getenv("RECAPTCHA_SECRET_KEY") or "").strip()
    if not secret:
        return

    token = (request.headers.get("X-Recaptcha-Token") or "").strip()
    action = (request.headers.get("X-Recaptcha-Action") or "").strip()

    if not token:
        raise HTTPException(status_code=403, detail="Antifraude: validação obrigatória")

    if action_esperada and action and action != action_esperada:
        raise HTTPException(status_code=403, detail="Antifraude: ação inválida")

    min_score_raw = (os.getenv("RECAPTCHA_MIN_SCORE") or "0.5").strip()
    try:
        min_score = float(min_score_raw)
    except Exception:
        min_score = 0.5

    data = {
        "secret": secret,
        "response": token,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post("https://www.google.com/recaptcha/api/siteverify", data=data)
        payload = resp.json() if resp.content else {}

    if not payload.get("success"):
        raise HTTPException(status_code=403, detail="Antifraude: validação falhou")

    if action_esperada:
        payload_action = payload.get("action")
        if payload_action and payload_action != action_esperada:
            raise HTTPException(status_code=403, detail="Antifraude: ação inválida")

    score = payload.get("score")
    if score is not None:
        try:
            score_f = float(score)
        except Exception:
            score_f = 0.0
        if score_f < min_score:
            raise HTTPException(status_code=403, detail="Antifraude: baixa confiança")

@router.get("/consultar/{documento}", response_model=dict)
async def consultar_pontos_publico(
    documento: str,
    request: Request,
    service: PontosService = Depends(get_pontos_service),
    _rate_limit: None = Depends(rate_limit_moderate)
):
    """
    Consulta pública de pontos por CPF/CNPJ (sem autenticação)
    
    - **documento**: CPF ou CNPJ do cliente (apenas números)
    
    **Retorna:**
    - Saldo de pontos
    - Nome do cliente
    - Histórico recente (últimas 10 transações)
    
    **Segurança:**
    - Rate limit: 20 consultas por minuto
    - Retorna apenas dados públicos
    """
    try:
        await _validar_recaptcha_publico(request, "consultar_pontos")
        # Remover caracteres não numéricos
        documento_limpo = ''.join(filter(str.isdigit, documento))
        
        if not documento_limpo or len(documento_limpo) not in [11, 14]:
            raise HTTPException(
                status_code=400,
                detail="CPF/CNPJ inválido. Deve conter 11 (CPF) ou 14 (CNPJ) dígitos."
            )
        
        # Buscar cliente por documento
        db = get_db()
        cliente_repo = ClienteRepository(db)
        try:
            cliente = await cliente_repo.get_by_documento(documento_limpo)
        except ValueError:
            cliente = None
        
        if not cliente:
            raise HTTPException(
                status_code=404,
                detail="Cliente não encontrado. Verifique o CPF/CNPJ informado."
            )
        
        # Buscar saldo e histórico
        saldo_data = await service.get_saldo(cliente['id'])
        historico_data = await service.get_historico(cliente['id'], limit=10)
        
        return {
            "success": True,
            "cliente": {
                "nome": cliente.get('nome_completo', 'Cliente'),
                "documento": documento_limpo
            },
            "saldo": saldo_data.get('saldo', 0),
            "historico": historico_data.get('transacoes', [])
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao consultar pontos: {str(e)}"
        )

@router.get("/saldo/{cliente_id}", response_model=SaldoResponse)
async def obter_saldo_cliente(
    cliente_id: int,
    service: PontosService = Depends(get_pontos_service),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obter saldo de pontos de um cliente específico
    
    - **cliente_id**: ID do cliente
    
    **Retorna:**
    - Saldo atual de pontos
    - Pontos pendentes
    - Pontos expirados
    
    **Segurança:**
    - Requer autenticação
    """
    try:
        saldo_data = await service.get_saldo(cliente_id)
        return saldo_data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter saldo: {str(e)}"
        )

@router.get("/historico/{cliente_id}", response_model=dict)
async def obter_historico_cliente(
    cliente_id: int,
    limit: int = 100,
    service: PontosService = Depends(get_pontos_service),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obter histórico de transações de pontos de um cliente
    
    - **cliente_id**: ID do cliente
    - **limit**: Número máximo de transações a retornar (padrão: 100)
    
    **Retorna:**
    - Lista de transações de pontos
    - Data, tipo, valor e descrição de cada transação
    
    **Segurança:**
    - Requer autenticação
    """
    try:
        historico_data = await service.get_historico(cliente_id, limit=limit)
        return historico_data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter histórico: {str(e)}"
        )

@router.get("/estatisticas", response_model=dict)
async def obter_estatisticas_pontos(
    service: PontosService = Depends(get_pontos_service),
    current_user: User = Depends(require_admin_or_manager)
):
    """Obter estatísticas gerais do sistema de pontos - Requer ADMIN ou GERENTE"""
    return await service.get_estatisticas()