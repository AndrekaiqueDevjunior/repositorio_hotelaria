from datetime import date, datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.database import get_db
from app.middleware.auth_middleware import get_current_active_user, require_admin_or_manager
from app.core.security import User
from app.repositories.tarifa_suite_repo import TarifaSuiteRepository
from app.schemas.tarifa_suite_schema import (
    TarifaSuiteCreateRequest,
    TarifaSuiteUpdateRequest,
    TarifaSuiteResponse,
)


router = APIRouter(prefix="/tarifas", tags=["tarifas"])


def _parse_date(d: date) -> datetime:
    if isinstance(d, datetime):
        if d.tzinfo is None:
            return d.replace(tzinfo=timezone.utc)
        return d
    return datetime(d.year, d.month, d.day, tzinfo=timezone.utc)


async def get_tarifa_repo() -> TarifaSuiteRepository:
    from app.core.database import get_db_connected
    db = await get_db_connected()
    return TarifaSuiteRepository(db)


@router.get("", response_model=List[TarifaSuiteResponse])
async def listar_tarifas(
    ativo: Optional[bool] = None,
    suite_tipo: Optional[str] = None,
    data: Optional[date] = Query(None, description="Filtrar tarifas vigentes na data"),
    repo: TarifaSuiteRepository = Depends(get_tarifa_repo),
    current_user: User = Depends(get_current_active_user),
):
    return await repo.list_all(ativo=ativo, suite_tipo=suite_tipo, data=data)


@router.get("/ativa")
async def obter_tarifa_ativa(
    suite_tipo: str = Query(..., description="Tipo da suite"),
    data: date = Query(..., description="Data para consulta"),
    repo: TarifaSuiteRepository = Depends(get_tarifa_repo),
    current_user: User = Depends(get_current_active_user),
):
    tarifa = await repo.get_tarifa_ativa(suite_tipo, data)
    if not tarifa:
        raise HTTPException(status_code=404, detail="Tarifa ativa nao encontrada para esta suite e data")
    return tarifa


@router.get("/{tarifa_id}", response_model=TarifaSuiteResponse)
async def obter_tarifa(
    tarifa_id: int,
    repo: TarifaSuiteRepository = Depends(get_tarifa_repo),
    current_user: User = Depends(get_current_active_user),
):
    tarifa = await repo.get_by_id(tarifa_id)
    if not tarifa:
        raise HTTPException(status_code=404, detail="Tarifa nao encontrada")
    return tarifa


@router.post("", response_model=TarifaSuiteResponse, status_code=201)
async def criar_tarifa(
    request: TarifaSuiteCreateRequest,
    repo: TarifaSuiteRepository = Depends(get_tarifa_repo),
    current_user: User = Depends(require_admin_or_manager),
):
    if request.data_inicio > request.data_fim:
        raise HTTPException(status_code=400, detail="data_inicio nao pode ser maior que data_fim")

    if request.preco_diaria <= 0:
        raise HTTPException(status_code=400, detail="preco_diaria deve ser maior que zero")

    sobrepoe = await repo.verificar_sobreposicao(
        suite_tipo=request.suite_tipo,
        data_inicio=request.data_inicio,
        data_fim=request.data_fim,
        ignore_id=None,
    )
    if sobrepoe:
        raise HTTPException(status_code=409, detail="Ja existe tarifa ativa com vigencia sobreposta para esta suite")

    tarifa = await repo.create(
        {
            "suite_tipo": request.suite_tipo.value,
            "temporada": request.temporada,
            "data_inicio": _parse_date(request.data_inicio),
            "data_fim": _parse_date(request.data_fim),
            "preco_diaria": request.preco_diaria,
            "ativo": request.ativo,
        }
    )
    return tarifa


@router.put("/{tarifa_id}", response_model=TarifaSuiteResponse)
async def atualizar_tarifa(
    tarifa_id: int,
    request: TarifaSuiteUpdateRequest,
    repo: TarifaSuiteRepository = Depends(get_tarifa_repo),
    current_user: User = Depends(require_admin_or_manager),
):
    if request.data_inicio > request.data_fim:
        raise HTTPException(status_code=400, detail="data_inicio nao pode ser maior que data_fim")

    if request.preco_diaria <= 0:
        raise HTTPException(status_code=400, detail="preco_diaria deve ser maior que zero")

    existente = await repo.get_by_id(tarifa_id)
    if not existente:
        raise HTTPException(status_code=404, detail="Tarifa nao encontrada")

    sobrepoe = await repo.verificar_sobreposicao(
        suite_tipo=request.suite_tipo,
        data_inicio=request.data_inicio,
        data_fim=request.data_fim,
        ignore_id=tarifa_id,
    )
    if sobrepoe:
        raise HTTPException(status_code=409, detail="Ja existe tarifa ativa com vigencia sobreposta para esta suite")

    tarifa = await repo.update(
        tarifa_id,
        {
            "suite_tipo": request.suite_tipo.value,
            "temporada": request.temporada,
            "data_inicio": _parse_date(request.data_inicio),
            "data_fim": _parse_date(request.data_fim),
            "preco_diaria": request.preco_diaria,
            "ativo": request.ativo,
        },
    )

    if not tarifa:
        raise HTTPException(status_code=400, detail="Falha ao atualizar tarifa")
    return tarifa


@router.patch("/{tarifa_id}", response_model=TarifaSuiteResponse)
async def atualizar_status_tarifa(
    tarifa_id: int,
    request: dict,
    repo: TarifaSuiteRepository = Depends(get_tarifa_repo),
    current_user: User = Depends(require_admin_or_manager),
):
    """Atualizar apenas o status da tarifa (ativo/inativo)"""
    existente = await repo.get_by_id(tarifa_id)
    if not existente:
        raise HTTPException(status_code=404, detail="Tarifa nao encontrada")

    # Atualizar apenas o campo ativo
    tarifa = await repo.update(
        tarifa_id,
        {
            "ativo": request.get("ativo", existente["ativo"]),
        },
    )

    if not tarifa:
        raise HTTPException(status_code=400, detail="Falha ao atualizar status da tarifa")
    return tarifa


@router.delete("/{tarifa_id}", status_code=204)
async def deletar_tarifa(
    tarifa_id: int,
    repo: TarifaSuiteRepository = Depends(get_tarifa_repo),
    current_user: User = Depends(require_admin_or_manager),
):
    ok = await repo.soft_delete(tarifa_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Tarifa nao encontrada")
    return
