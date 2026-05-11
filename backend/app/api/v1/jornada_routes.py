from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.core.database import get_db
from app.core.security import User
from app.middleware.auth_middleware import get_current_active_user
from app.middleware.rate_limit import rate_limit_moderate
from app.services.jornada_service import JornadaService

router = APIRouter(tags=["jornada-real"])


def get_jornada_service() -> JornadaService:
    return JornadaService(get_db())


@router.get("/jornada/config", response_model=dict)
async def obter_config_jornada(
    service: JornadaService = Depends(get_jornada_service),
):
    return await service.get_config()


@router.get("/jornada/regras", response_model=dict)
async def obter_regras_jornada(
    service: JornadaService = Depends(get_jornada_service),
):
    return await service.get_regras()


@router.get("/jornada/consulta", response_model=dict)
async def consultar_jornada_por_cpf(
    request: Request,
    cpf: str = Query(..., min_length=11),
    service: JornadaService = Depends(get_jornada_service),
    _rate_limit: None = Depends(rate_limit_moderate),
):
    try:
        dashboard = await service.consultar_jornada_por_cpf(cpf)
        return dashboard
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar Jornada Real: {exc}")


@router.get("/clientes/{cliente_id}/jornada", response_model=dict)
async def obter_dashboard_jornada_cliente(
    cliente_id: int,
    service: JornadaService = Depends(get_jornada_service),
    current_user: User = Depends(get_current_active_user),
):
    return await service.montar_dashboard_jornada(cliente_id)


@router.get("/clientes/{cliente_id}/nivel", response_model=dict)
async def obter_nivel_jornada_cliente(
    cliente_id: int,
    service: JornadaService = Depends(get_jornada_service),
    current_user: User = Depends(get_current_active_user),
):
    return await service.obter_nivel_cliente(cliente_id)


@router.get("/clientes/{cliente_id}/beneficios", response_model=dict)
async def obter_beneficios_jornada_cliente(
    cliente_id: int,
    service: JornadaService = Depends(get_jornada_service),
    current_user: User = Depends(get_current_active_user),
):
    return await service.listar_beneficios(cliente_id)
