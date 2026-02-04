"""
Rotas de Funcionários
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from app.core.database import get_db
from app.core.security import get_current_user
from pydantic import BaseModel
from prisma import Client
from app.repositories.funcionario_repo import FuncionarioRepository
from app.schemas.funcionario_schema import FuncionarioCreate, FuncionarioUpdate

router = APIRouter()

class FuncionarioResponse(BaseModel):
    id: int
    nome: str
    email: str
    perfil: str
    status: str
    fotoUrl: Optional[str] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

@router.get("/funcionarios", response_model=List[FuncionarioResponse])
async def listar_funcionarios(
    db: Client = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Listar todos os funcionários"""
    try:
        funcionarios = await db.funcionario.find_many(
            take=limit,
            skip=offset
        )
        
        return [
            FuncionarioResponse(
                id=f.id,
                nome=f.nome,
                email=f.email,
                perfil=f.perfil,
                status=f.status,
                fotoUrl=getattr(f, "fotoUrl", None),
                created_at=f.createdAt.isoformat(),
                updated_at=f.updatedAt.isoformat()
            )
            for f in funcionarios
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar funcionários: {str(e)}")


@router.post("/funcionarios", response_model=FuncionarioResponse)
async def criar_funcionario(
    funcionario: FuncionarioCreate,
    db: Client = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Criar novo funcionário"""
    perfil = str(getattr(current_user, "perfil", "") or "").upper()
    if perfil != "ADMIN":
        raise HTTPException(status_code=403, detail="Apenas ADMIN pode criar funcionários")

    try:
        repo = FuncionarioRepository(db)
        criado = await repo.create(funcionario)
        return FuncionarioResponse(**criado)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar funcionário: {str(e)}")

@router.get("/funcionarios/{funcionario_id}", response_model=FuncionarioResponse)
async def obter_funcionario(
    funcionario_id: int,
    db: Client = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Obter funcionário por ID"""
    try:
        funcionario = await db.funcionario.find_unique(where={'id': funcionario_id})
        
        if not funcionario:
            raise HTTPException(status_code=404, detail="Funcionário não encontrado")
        
        return FuncionarioResponse(
            id=funcionario.id,
            nome=funcionario.nome,
            email=funcionario.email,
            perfil=funcionario.perfil,
            status=funcionario.status,
            fotoUrl=getattr(funcionario, "fotoUrl", None),
            created_at=funcionario.createdAt.isoformat(),
            updated_at=funcionario.updatedAt.isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter funcionário: {str(e)}")


@router.put("/funcionarios/{funcionario_id}", response_model=FuncionarioResponse)
async def atualizar_funcionario(
    funcionario_id: int,
    funcionario: FuncionarioUpdate,
    db: Client = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Atualizar funcionário"""
    perfil = str(getattr(current_user, "perfil", "") or "").upper()
    if perfil != "ADMIN":
        raise HTTPException(status_code=403, detail="Apenas ADMIN pode editar funcionários")

    try:
        repo = FuncionarioRepository(db)
        atualizado = await repo.update(funcionario_id, funcionario)
        return FuncionarioResponse(**atualizado)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar funcionário: {str(e)}")


@router.delete("/funcionarios/{funcionario_id}", response_model=dict)
async def inativar_funcionario(
    funcionario_id: int,
    db: Client = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Inativar funcionário (soft delete)"""
    perfil = str(getattr(current_user, "perfil", "") or "").upper()
    if perfil != "ADMIN":
        raise HTTPException(status_code=403, detail="Apenas ADMIN pode inativar funcionários")

    try:
        repo = FuncionarioRepository(db)
        return await repo.delete(funcionario_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao inativar funcionário: {str(e)}")
