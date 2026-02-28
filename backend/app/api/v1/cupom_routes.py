from typing import Optional

from fastapi import APIRouter, Depends, Request

from app.core.database import get_db
from app.core.security import User
from app.middleware.auth_middleware import require_admin_or_manager
from app.middleware.rate_limit import rate_limit_moderate
from app.repositories.cupom_repo import CupomRepository
from app.schemas.cupom_schema import (
    CupomCreateRequest,
    CupomResponse,
    CupomStatusRequest,
    CupomUpdateRequest,
    CupomValidarRequest,
)
from app.services.cupom_service import CupomService


router = APIRouter(prefix="/cupons", tags=["cupons"])


async def get_cupom_service() -> CupomService:
    return CupomService(CupomRepository(get_db()))


@router.post("/validar", response_model=dict)
async def validar_cupom(
    payload: CupomValidarRequest,
    request: Request,
    service: CupomService = Depends(get_cupom_service),
    _rate_limit: None = Depends(rate_limit_moderate),
):
    return await service.validar(**payload.model_dump())


@router.get("", response_model=list[CupomResponse])
async def listar_cupons(
    apenas_ativos: bool = False,
    service: CupomService = Depends(get_cupom_service),
    current_user: User = Depends(require_admin_or_manager),
):
    return await service.list_all(apenas_ativos=apenas_ativos)


@router.get("/{cupom_id}", response_model=CupomResponse)
async def obter_cupom(
    cupom_id: int,
    service: CupomService = Depends(get_cupom_service),
    current_user: User = Depends(require_admin_or_manager),
):
    return await service.get_by_id(cupom_id)


@router.post("", response_model=CupomResponse, status_code=201)
async def criar_cupom(
    payload: CupomCreateRequest,
    service: CupomService = Depends(get_cupom_service),
    current_user: User = Depends(require_admin_or_manager),
):
    return await service.create(payload.model_dump(), criado_por=current_user.id)


@router.put("/{cupom_id}", response_model=CupomResponse)
async def atualizar_cupom(
    cupom_id: int,
    payload: CupomUpdateRequest,
    service: CupomService = Depends(get_cupom_service),
    current_user: User = Depends(require_admin_or_manager),
):
    return await service.update(cupom_id, payload.model_dump(exclude_unset=True))


@router.patch("/{cupom_id}/ativar", response_model=CupomResponse)
async def alterar_status_cupom(
    cupom_id: int,
    payload: CupomStatusRequest,
    service: CupomService = Depends(get_cupom_service),
    current_user: User = Depends(require_admin_or_manager),
):
    return await service.set_ativo(cupom_id, payload.ativo)


@router.delete("/{cupom_id}", response_model=dict)
async def excluir_cupom(
    cupom_id: int,
    service: CupomService = Depends(get_cupom_service),
    current_user: User = Depends(require_admin_or_manager),
):
    return await service.delete(cupom_id)
