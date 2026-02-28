from fastapi import APIRouter, Depends, HTTPException, Query
from app.schemas.cliente_schema import ClienteCreate, ClienteResponse
from app.services.cliente_service import ClienteService
from app.repositories.cliente_repo import ClienteRepository
from app.core.database import get_db
from app.utils.export_utils import export_to_csv, export_to_pdf_simple
from app.middleware.auth_middleware import get_current_active_user, require_admin, require_admin_or_manager
from app.core.security import User
from typing import Optional

router = APIRouter(prefix="/clientes", tags=["clientes"])

# Dependency injection
async def get_cliente_service() -> ClienteService:
    db = get_db()
    return ClienteService(ClienteRepository(db))

@router.get("", response_model=dict)
async def listar_clientes(
    service: ClienteService = Depends(get_cliente_service),
    current_user: User = Depends(get_current_active_user),

    search: Optional[str] = Query(None, description="Busca por nome, documento ou email"),
    status: Optional[str] = Query(None, description="Filtrar por status (ATIVO, INATIVO)"),
    limit: Optional[int] = Query(100, description="Limite de resultados"),
    offset: Optional[int] = Query(0, description="Offset para paginação")
):
    """Listar todos os clientes com filtros e busca - Requer autenticação"""
    return await service.list_all(search=search, status=status, limit=limit, offset=offset)

@router.get("/export/csv")
async def exportar_clientes_csv(
    service: ClienteService = Depends(get_cliente_service),
    current_user: User = Depends(get_current_active_user),

    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None)
):
    """Exportar clientes para CSV"""
    result = await service.list_all(search=search, status=status, limit=10000, offset=0)
    return export_to_csv(result["clientes"], "clientes.csv")

@router.get("/export/pdf")
async def exportar_clientes_pdf(
    service: ClienteService = Depends(get_cliente_service),
    current_user: User = Depends(get_current_active_user),

    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None)
):
    """Exportar clientes para PDF"""
    result = await service.list_all(search=search, status=status, limit=10000, offset=0)
    return export_to_pdf_simple(result["clientes"], "clientes.pdf", "Relatório de Clientes")

@router.post("", response_model=ClienteResponse)
async def criar_cliente(
    cliente: ClienteCreate,
    service: ClienteService = Depends(get_cliente_service),
    current_user: User = Depends(get_current_active_user)
):

    """Criar novo cliente - Requer autenticação"""
    return await service.create(cliente)

@router.get("/{cliente_id}", response_model=ClienteResponse)
async def obter_cliente(
    cliente_id: int,
    service: ClienteService = Depends(get_cliente_service),
    current_user: User = Depends(get_current_active_user)
):

    """Obter cliente por ID"""
    return await service.get_by_id(cliente_id)

@router.get("/documento/{documento}", response_model=ClienteResponse)
async def obter_cliente_por_documento(
    documento: str,
    service: ClienteService = Depends(get_cliente_service),
    current_user: User = Depends(get_current_active_user)
):

    """Obter cliente por documento"""
    return await service.get_by_documento(documento)

@router.put("/{cliente_id}", response_model=ClienteResponse)
async def atualizar_cliente(
    cliente_id: int,
    cliente_data: dict,
    service: ClienteService = Depends(get_cliente_service),
    current_user: User = Depends(require_admin_or_manager)
):

    """Atualizar cliente - Requer ADMIN ou GERENTE"""
    return await service.update(cliente_id, cliente_data)

@router.delete("/{cliente_id}", status_code=204)
async def deletar_cliente(
    cliente_id: int,
    service: ClienteService = Depends(get_cliente_service),
    current_user: User = Depends(require_admin)
):
    """Deletar cliente - Requer ADMIN"""
    await service.delete(cliente_id)