from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, Optional
from pydantic import BaseModel, validator
from datetime import date, datetime
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.overbooking_service import OverbookingService
from app.middleware.auth_middleware import get_current_active_user, require_admin_or_manager
from app.core.security import User
from app.core.exceptions import ValidationError, BusinessRuleViolation


router = APIRouter(prefix="/overbooking", tags=["overbooking"])


class ReservaComLockRequest(BaseModel):
    cliente_id: int
    quarto_id: int
    checkin_previsto: datetime
    checkout_previsto: datetime
    valor_diaria: float
    num_diarias_previstas: int
    valor_previsto: float
    observacoes: str = None
    permitir_overbooking: bool = False
    
    @validator('checkin_previsto', 'checkout_previsto')
    def validate_datas(cls, v):
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except:
                raise ValueError('Formato de data inválido')
        return v
    
    @validator('checkout_previsto')
    def validate_checkout_depois_checkin(cls, v, values):
        if 'checkin_previsto' in values and v <= values['checkin_previsto']:
            raise ValueError('Checkout deve ser posterior ao check-in')
        return v


@router.post("/verificar-disponibilidade/{quarto_id}")
async def verificar_disponibilidade(
    quarto_id: int,
    checkin_inicio: datetime,
    checkout_fim: datetime,
    excluir_reserva_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Verifica disponibilidade rigorosa de um quarto
    Com análise de conflitos detalhada
    """
    try:
        service = OverbookingService(db)
        
        resultado = service.verificar_disponibilidade(
            quarto_id=quarto_id,
            checkin_inicio=checkin_inicio,
            checkout_fim=checkout_fim,
            excluir_reserva_id=excluir_reserva_id
        )
        
        return resultado
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}"
        )


@router.post("/reservar-com-lock")
async def reservar_com_lock_transacional(
    dados: ReservaComLockRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Cria reserva com controle rigoroso de concorrência
    Usa locks transacionais para prevenir race conditions
    """
    try:
        service = OverbookingService(db)
        
        # Converter para dicionário
        dados_dict = {
            "cliente_id": dados.cliente_id,
            "quarto_id": dados.quarto_id,
            "checkin_previsto": dados.checkin_previsto,
            "checkout_previsto": dados.checkout_previsto,
            "valor_diaria": dados.valor_diaria,
            "num_diarias_previstas": dados.num_diarias_previstas,
            "valor_previsto": dados.valor_previsto,
            "observacoes": dados.observacoes
        }
        
        resultado = service.reservar_com_lock_transacional(
            dados_reserva=dados_dict,
            usuario_id=current_user["id"],
            permitir_overbooking=dados.permitir_overbooking
        )
        
        return resultado
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except BusinessRuleViolation as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}"
        )


@router.get("/analisar/{data_inicio}/{data_fim}")
async def analisar_overbooking_hotel(
    data_inicio: date,
    data_fim: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_manager)
):
    """
    Análise completa de overbooking do hotel por período
    Identifica todos os conflitos e riscos operacionais
    """
    try:
        service = OverbookingService(db)
        
        analise = service.analisar_overbooking_hotel(data_inicio, data_fim)
        
        return analise
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}"
        )


@router.post("/resolver-conflito/{conflito_id}")
async def resolver_overbooking(
    conflito_id: str,
    solucao: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_manager)
):
    """
    Resolve um caso específico de overbooking
    Implementa soluções como upgrade, realocação, cancelamento
    """
    try:
        service = OverbookingService(db)
        
        resultado = service.resolver_overbooking(
            conflito_id=conflito_id,
            solucao=solucao,
            usuario_id=current_user["id"]
        )
        
        return resultado
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}"
        )


@router.get("/lock-status")
async def verificar_status_locks(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_manager)
):
    """
    Verifica status atual dos locks de overbooking
    Para diagnóstico e monitoramento
    """
    try:
        from app.services.overbooking_service import OverbookingLock
        
        with OverbookingLock._lock:
            locks_ativos = list(OverbookingLock._locks.keys())
            
        return {
            "locks_ativos": len(locks_ativos),
            "quartos_bloqueados": locks_ativos,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}"
        )


@router.get("/estatisticas")
async def obter_estatisticas_overbooking(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_manager)
):
    """
    Estatísticas gerais de overbooking do sistema
    """
    try:
        service = OverbookingService(db)
        
        # Análise dos últimos 30 dias
        hoje = date.today()
        inicio = hoje - datetime.timedelta(days=30)
        
        analise = service.analisar_overbooking_hotel(inicio, hoje)
        
        return {
            "periodo_analisado": f"{inicio.strftime('%d/%m/%Y')} a {hoje.strftime('%d/%m/%Y')}",
            "estatisticas": analise.get("estatisticas", {}),
            "recomendacoes": analise.get("recomendacoes", []),
            "quartos_com_problema": len(analise.get("quartos_com_conflito", []))
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}"
        )
