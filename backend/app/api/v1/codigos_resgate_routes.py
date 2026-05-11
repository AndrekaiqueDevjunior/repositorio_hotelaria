from fastapi import APIRouter, Depends, HTTPException

from app.core.database import get_db
from app.core.security import User
from app.middleware.auth_middleware import require_staff
from app.middleware.rate_limit import rate_limit_moderate, rate_limit_strict
from app.repositories.premio_repo_atomic import PremioRepositoryAtomic

router = APIRouter(prefix="/codigos", tags=["codigos-resgate"])


def get_repo() -> PremioRepositoryAtomic:
    return PremioRepositoryAtomic(get_db())


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
    if not resultado.get("valido"):
        raise HTTPException(status_code=400, detail=resultado.get("error"))
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
