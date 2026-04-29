from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.database import get_db
from app.core.security import User
from app.middleware.auth_middleware import get_current_active_user, require_admin
from app.schemas.indicacao_schema import (
    IndicacaoCreateRequest,
    IndicacaoReprocessarResponse,
    IndicacaoResponse,
    IndicacaoStatusResponse,
)
from app.services.indicacao_service import IndicacaoService


router = APIRouter(prefix="/indicacoes", tags=["indicacoes"])


def get_indicacao_service() -> IndicacaoService:
    return IndicacaoService(get_db())


@router.post("", response_model=IndicacaoResponse, status_code=201)
async def criar_indicacao(
    payload: IndicacaoCreateRequest,
    service: IndicacaoService = Depends(get_indicacao_service),
    current_user: User = Depends(get_current_active_user),
):
    return await service.criar_indicacao(
        cliente_indicador_id=payload.cliente_indicador_id,
        cpf_indicado=payload.cpf_indicado,
    )


@router.get("/me")
async def listar_minhas_indicacoes(
    cliente_id: int = Query(..., ge=1),
    service: IndicacaoService = Depends(get_indicacao_service),
    current_user: User = Depends(get_current_active_user),
):
    return await service.listar_indicacoes_cliente(cliente_id)


@router.get("/status", response_model=IndicacaoStatusResponse)
async def obter_status_indicacoes(
    cliente_id: int = Query(..., ge=1),
    service: IndicacaoService = Depends(get_indicacao_service),
    current_user: User = Depends(get_current_active_user),
):
    return await service.obter_status_cliente(cliente_id)


@router.post("/reprocessar", response_model=IndicacaoReprocessarResponse)
async def reprocessar_indicacoes_pendentes(
    limit: int = Query(100, ge=1, le=500),
    service: IndicacaoService = Depends(get_indicacao_service),
    current_user: User = Depends(require_admin),
):
    return await service.reprocessar_creditos_pendentes(
        limit=limit,
        funcionario_id=current_user.id,
    )


@router.post("/reprocessar/{reserva_id}")
async def reprocessar_indicacao_reserva(
    reserva_id: int,
    service: IndicacaoService = Depends(get_indicacao_service),
    current_user: User = Depends(require_admin),
):
    resultado = await service.processar_credito_indicacao_apos_checkout(
        reserva_id=reserva_id,
        funcionario_id=current_user.id,
    )
    if not resultado.get("success"):
        raise HTTPException(status_code=400, detail=resultado.get("motivo") or resultado.get("error"))
    return resultado
