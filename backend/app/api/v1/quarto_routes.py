from fastapi import APIRouter, Depends, HTTPException, Query
from app.schemas.quarto_schema import QuartoCreate, QuartoUpdate, QuartoResponse, StatusQuarto, TipoSuite
from app.services.quarto_service import QuartoService
from app.services.disponibilidade_service import DisponibilidadeService
from app.repositories.quarto_repo import QuartoRepository
from app.core.database import get_db
from app.middleware.auth_middleware import get_current_active_user, require_admin, require_admin_or_manager
from app.core.security import User

from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/quartos", tags=["quartos"])

# Dependency injection
async def get_quarto_service() -> QuartoService:
    db = get_db()
    return QuartoService(QuartoRepository(db))

async def get_disponibilidade_service() -> DisponibilidadeService:
    db = get_db()
    return DisponibilidadeService(db)

@router.get("", response_model=dict)
async def listar_quartos(
    service: QuartoService = Depends(get_quarto_service),
    current_user: User = Depends(get_current_active_user),

    search: Optional[str] = Query(None, description="Busca por número ou andar"),
    status: Optional[str] = Query(None, description="Filtrar por status"),
    tipo_suite: Optional[str] = Query(None, description="Filtrar por tipo de suíte"),
    limit: Optional[int] = Query(100, description="Limite de resultados"),
    offset: Optional[int] = Query(0, description="Offset para paginação")
):
    """Listar todos os quartos - Requer autenticação"""
    return await service.list_all(
        search=search,
        status=status,
        tipo_suite=tipo_suite,
        limit=limit,
        offset=offset
    )

@router.get("/disponiveis", response_model=List[QuartoResponse])
async def listar_quartos_disponiveis(service: QuartoService = Depends(get_quarto_service)):
    """Listar quartos disponíveis"""
    return await service.get_disponiveis()

@router.post("", response_model=QuartoResponse)
async def criar_quarto(
    quarto: QuartoCreate,
    service: QuartoService = Depends(get_quarto_service),
    current_user: User = Depends(require_admin_or_manager)
):
    """Criar novo quarto - Requer ADMIN ou GERENTE"""
    return await service.create(quarto)

@router.get("/{numero}", response_model=QuartoResponse)
async def obter_quarto(
    numero: str,
    service: QuartoService = Depends(get_quarto_service)
):
    """Obter quarto por número"""
    return await service.get_by_numero(numero)

@router.put("/{numero}", response_model=QuartoResponse)
async def atualizar_quarto(
    numero: str,
    quarto: QuartoUpdate,
    service: QuartoService = Depends(get_quarto_service),
    current_user: User = Depends(require_admin_or_manager)
):
    """Atualizar quarto - Requer ADMIN ou GERENTE"""
    return await service.update(numero, quarto)

@router.patch("/{numero}/status", response_model=QuartoResponse)
async def atualizar_status_quarto(
    numero: str,
    status: StatusQuarto,
    service: QuartoService = Depends(get_quarto_service)
):
    """Atualizar apenas o status do quarto"""
    return await service.update_status(numero, status)

@router.get("/status/{status}", response_model=List[QuartoResponse])
async def listar_quartos_por_status(
    status: StatusQuarto,
    service: QuartoService = Depends(get_quarto_service)
):
    """Listar quartos por status"""
    return await service.list_by_status(status)

@router.get("/tipo/{tipo}", response_model=List[QuartoResponse])
async def listar_quartos_por_tipo(
    tipo: TipoSuite,
    service: QuartoService = Depends(get_quarto_service)
):
    """Listar quartos por tipo"""
    return await service.list_by_tipo(tipo)

@router.delete("/{numero}", status_code=204)
async def deletar_quarto(
    numero: str,
    service: QuartoService = Depends(get_quarto_service),
    current_user: User = Depends(require_admin)
):
    """Deletar quarto - Requer ADMIN"""
    await service.delete(numero)

@router.get("/{numero}/historico", response_model=dict)
async def obter_historico_quarto(
    numero: str,
    service: QuartoService = Depends(get_quarto_service),
    limit: Optional[int] = Query(50, description="Limite de reservas no histórico")
):
    """Obter histórico de ocupação do quarto"""
    return await service.get_historico(numero, limit)

@router.get("/{numero}/reserva-atual", response_model=dict)
async def obter_reserva_atual_quarto(
    numero: str,
    service: QuartoService = Depends(get_quarto_service)
):
    """Obter reserva atual/ativa do quarto"""
    return await service.get_reserva_atual(numero)

@router.get("/{numero}/disponibilidade", response_model=dict)
async def verificar_disponibilidade_quarto(
    numero: str,
    checkin: datetime = Query(..., description="Data/hora de check-in (ISO 8601)"),
    checkout: datetime = Query(..., description="Data/hora de check-out (ISO 8601)"),
    reserva_id_excluir: Optional[int] = Query(None, description="ID da reserva a excluir (para edição)"),
    service: DisponibilidadeService = Depends(get_disponibilidade_service)
):
    """
    Verificar disponibilidade de um quarto específico no período
    
    Retorna:
    - disponivel: bool
    - motivo: string
    - conflitos: lista de reservas conflitantes
    """
    return await service.verificar_disponibilidade(
        numero,
        checkin,
        checkout,
        reserva_id_excluir
    )

@router.get("/disponiveis/periodo", response_model=list)
async def listar_quartos_disponiveis_periodo(
    checkin: datetime = Query(..., description="Data/hora de check-in (ISO 8601)"),
    checkout: datetime = Query(..., description="Data/hora de check-out (ISO 8601)"),
    tipo_suite: Optional[str] = Query(None, description="Filtrar por tipo de suíte"),
    service: DisponibilidadeService = Depends(get_disponibilidade_service)
):
    """
    Listar quartos disponíveis em um período específico
    
    Útil para:
    - Agenda pública (mostrar apenas quartos disponíveis)
    - Sistema de reservas (validar antes de criar)
    """
    return await service.listar_quartos_disponiveis(
        checkin,
        checkout,
        tipo_suite
    )

@router.get("/disponibilidade/resumo", response_model=dict)
async def obter_resumo_disponibilidade(
    checkin: datetime = Query(..., description="Data/hora de check-in (ISO 8601)"),
    checkout: datetime = Query(..., description="Data/hora de check-out (ISO 8601)"),
    service: DisponibilidadeService = Depends(get_disponibilidade_service)
):
    """
    Obter resumo de disponibilidade de todos os quartos no período
    
    Retorna:
    - total_quartos: int
    - disponiveis: int
    - ocupados: int
    - quartos: lista detalhada com status de cada quarto
    """
    return await service.verificar_multiplos_quartos(checkin, checkout)