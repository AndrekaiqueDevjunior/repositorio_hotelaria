from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List
from pydantic import BaseModel, validator
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.state_machine_service import StateMachineService, TransicaoEstado
from app.middleware.auth_middleware import get_current_active_user
from app.core.security import User
from app.core.exceptions import ValidationError, BusinessRuleViolation


router = APIRouter(prefix="/state-machine", tags=["state-machine"])


class TransicaoRequest(BaseModel):
    transicao: str
    motivo: str = None
    dados_contexto: Dict[str, Any] = None
    
    @validator('transicao')
    def validate_transicao(cls, v):
        try:
            TransicaoEstado(v)
            return v
        except ValueError:
            raise ValueError(f'Transição inválida: {v}')


@router.get("/{reserva_id}/validar/{transicao}")
async def validar_transicao(
    reserva_id: int,
    transicao: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Valida se uma transição é permitida para a reserva
    """
    try:
        service = StateMachineService(db)
        
        transicao_enum = TransicaoEstado(transicao)
        validacao = service.validar_transicao(reserva_id, transicao_enum, current_user["id"])
        
        return validacao
        
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


@router.post("/{reserva_id}/executar")
async def executar_transicao(
    reserva_id: int,
    dados: TransicaoRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Executa uma transição de estado
    """
    try:
        service = StateMachineService(db)
        
        transicao_enum = TransicaoEstado(dados.transicao)
        resultado = service.executar_transicao(
            reserva_id=reserva_id,
            transicao=transicao_enum,
            usuario_id=current_user["id"],
            motivo=dados.motivo,
            dados_contexto=dados.dados_contexto
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


@router.get("/{reserva_id}/historico")
async def obter_historico_estados(
    reserva_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtém histórico de mudanças de estado da reserva
    """
    try:
        service = StateMachineService(db)
        historico = service.obter_historico_estados(reserva_id)
        return historico
        
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


@router.get("/{reserva_id}/proximas-transicoes")
async def obter_proximas_transicoes(
    reserva_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Lista transições válidas para o estado atual da reserva
    """
    try:
        service = StateMachineService(db)
        transicoes = service.obter_proximas_transicoes(reserva_id)
        return transicoes
        
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


@router.get("/transicoes-disponiveis")
async def listar_transicoes_disponiveis(
    current_user: User = Depends(get_current_active_user)
):
    """
    Lista todas as transições disponíveis no sistema
    """
    transicoes = {
        transicao.value: {
            "nome": transicao.value.replace("_", " ").title(),
            "descricao": service._obter_descricao_transicao(transicao) if hasattr(service, '_obter_descricao_transicao') else transicao.value
        }
        for transicao in TransicaoEstado
    }
    
    return {
        "transicoes": transicoes,
        "total": len(transicoes)
    }


# Criar instância do serviço para descrições
service = StateMachineService(None)
