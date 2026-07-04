from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.database import get_db
from app.core.security import User
from app.middleware.auth_middleware import require_staff
from app.middleware.rate_limit import rate_limit_moderate, rate_limit_strict
from app.repositories.premio_repo_atomic import PremioRepositoryAtomic
from app.tasks.jornada_tasks import invalidar_codigos_vencidos_jornada

router = APIRouter(prefix="/codigos", tags=["codigos-resgate"])


def get_repo() -> PremioRepositoryAtomic:
    return PremioRepositoryAtomic(get_db())


@router.get("/pendentes", response_model=dict)
async def listar_resgates_pendentes(
    limit: int = Query(50, ge=1, le=200),
    repo: PremioRepositoryAtomic = Depends(get_repo),
    current_user: User = Depends(require_staff),
):
    resgates = await repo.listar_resgates_pendentes(limit=limit)
    return {"success": True, "total": len(resgates), "resgates": resgates}


@router.get("/{codigo}", response_model=dict)
async def obter_codigo_resgate(
    codigo: str,
    repo: PremioRepositoryAtomic = Depends(get_repo),
    _rate_limit: None = Depends(rate_limit_moderate),
):
    resultado = await repo.obter_codigo_resgate(codigo)
    if not resultado.get("success"):
        raise HTTPException(status_code=404, detail=resultado.get("error"))
    return resultado


@router.post("/{codigo}/validar", response_model=dict)
async def validar_codigo_resgate(
    codigo: str,
    repo: PremioRepositoryAtomic = Depends(get_repo),
    current_user: User = Depends(require_staff),
    _rate_limit: None = Depends(rate_limit_strict),
):
    resultado = await repo.validar_codigo_resgate(codigo)
    if not resultado.get("success"):
        raise HTTPException(status_code=404, detail=resultado.get("error"))
    # Codigo invalido/ja utilizado/expirado nao e erro HTTP: devolve 200 com
    # valido=false e o contexto do cliente/premio, para a tela de validacao
    # poder mostrar quem e o cliente e o que aconteceu com o codigo (em vez
    # de so um erro generico).
    return resultado


@router.post("/{codigo}/utilizar", response_model=dict)
async def utilizar_codigo_resgate(
    codigo: str,
    repo: PremioRepositoryAtomic = Depends(get_repo),
    current_user: User = Depends(require_staff),
    _rate_limit: None = Depends(rate_limit_strict),
):
    resultado = await repo.usar_codigo_resgate(
        codigo_resgate=codigo,
        funcionario_id=current_user.id if hasattr(current_user, "id") else None,
    )
    if not resultado.get("success"):
        raise HTTPException(status_code=400, detail=resultado.get("error"))
    return resultado


@router.post("/resgates/{resgate_id}/renovar", response_model=dict)
async def renovar_codigo_resgate(
    resgate_id: int,
    dias_validade: int = Query(30, ge=1, le=365),
    repo: PremioRepositoryAtomic = Depends(get_repo),
    current_user: User = Depends(require_staff),
    _rate_limit: None = Depends(rate_limit_strict),
):
    resultado = await repo.renovar_codigo_resgate(
        resgate_id=resgate_id,
        funcionario_id=current_user.id if hasattr(current_user, "id") else None,
        dias_validade=dias_validade,
    )
    if not resultado.get("success"):
        raise HTTPException(status_code=400, detail=resultado.get("error"))
    return resultado


@router.post("/maintenance/invalidar-vencidos", response_model=dict)
async def invalidar_codigos_vencidos(
    current_user: User = Depends(require_staff),
    _rate_limit: None = Depends(rate_limit_strict),
):
    return await invalidar_codigos_vencidos_jornada()
