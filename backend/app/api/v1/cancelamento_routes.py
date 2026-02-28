from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from pydantic import BaseModel, validator
from datetime import date
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.cancelamento_service import CancelamentoService
from app.middleware.auth_middleware import get_current_active_user, require_admin_or_manager
from app.core.security import User
from app.core.exceptions import ValidationError, BusinessRuleViolation


router = APIRouter(prefix="/cancelamentos", tags=["cancelamentos"])


# Schemas
class CancelamentoRequest(BaseModel):
    motivo: str
    forcar_sem_multa: bool = False
    
    @validator('motivo')
    def validate_motivo(cls, v):
        if len(v.strip()) < 10:
            raise ValueError('Motivo deve ter pelo menos 10 caracteres')
        return v.strip()


class NoShowRequest(BaseModel):
    observacoes: str = None


@router.get("/{reserva_id}/validar")
async def validar_cancelamento(
    reserva_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Valida se a reserva pode ser cancelada e calcula multas aplicáveis
    Mostra impacto financeiro antes da confirmação
    """
    try:
        service = CancelamentoService(db)
        validacao = service.validar_cancelamento(reserva_id)
        return validacao
        
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


@router.post("/{reserva_id}/executar")
async def executar_cancelamento(
    reserva_id: int,
    dados: CancelamentoRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Executa o cancelamento aplicando políticas e multas
    
    forcar_sem_multa=True requer permissão de gerente/admin
    """
    try:
        service = CancelamentoService(db)
        
        # Verificar permissão para forçar sem multa
        if dados.forcar_sem_multa:
            # Requer permissão administrativa
            if current_user.get("perfil") not in ["GERENTE", "ADMIN"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Apenas gerentes/admins podem cancelar sem multa"
                )
        
        resultado = service.executar_cancelamento(
            reserva_id=reserva_id,
            motivo=dados.motivo,
            usuario_id=current_user["id"],
            forcar_sem_multa=dados.forcar_sem_multa
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


@router.post("/{reserva_id}/no-show")
async def processar_no_show(
    reserva_id: int,
    dados: NoShowRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Processa no-show (não comparecimento)
    Aplicação automática de política mais restritiva
    """
    try:
        service = CancelamentoService(db)
        
        resultado = service.cancelamento_no_show(
            reserva_id=reserva_id,
            usuario_id=current_user["id"]
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


@router.get("/relatorio/{data_inicio}/{data_fim}")
async def relatorio_cancelamentos(
    data_inicio: date,
    data_fim: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_manager)
):
    """
    Relatório de cancelamentos por período
    Análise de impacto financeiro - Restrito a gerência
    """
    try:
        service = CancelamentoService(db)
        relatorio = service.obter_historico_cancelamentos(data_inicio, data_fim)
        return relatorio
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}"
        )


@router.get("/politicas")
async def listar_politicas_cancelamento(
    current_user: User = Depends(get_current_active_user)
):
    """
    Lista as políticas de cancelamento disponíveis
    Para configuração de tarifas
    """
    politicas = {
        "FLEXIVEL": {
            "nome": "Flexível",
            "descricao": "Cancelamento gratuito até 24h antes",
            "regras": [
                "Mais de 24h: sem multa",
                "Menos de 24h: multa de 50%"
            ],
            "recomendado_para": "Tarifas promocionais, baixa temporada"
        },
        "MODERADA": {
            "nome": "Moderada",
            "descricao": "Cancelamento com multas progressivas",
            "regras": [
                "Mais de 48h: sem multa",
                "24-48h: multa de 30%",
                "Menos de 24h: multa de 70%"
            ],
            "recomendado_para": "Tarifas padrão"
        },
        "RIGIDA": {
            "nome": "Rígida",
            "descricao": "Multas altas para proteção da receita",
            "regras": [
                "Mais de 72h: multa de 20%",
                "24-72h: multa de 60%",
                "Menos de 24h: multa de 90%"
            ],
            "recomendado_para": "Alta temporada, eventos especiais"
        },
        "NAO_REEMBOLSAVEL": {
            "nome": "Não-reembolsável",
            "descricao": "Nenhum reembolso em qualquer situação",
            "regras": [
                "Sem reembolso",
                "Valor 100% retido"
            ],
            "recomendado_para": "Tarifas super promocionais"
        }
    }
    
    return {
        "politicas_disponiveis": politicas,
        "politica_padrao": "FLEXIVEL",
        "observacoes": [
            "No-show aplica sempre a política mais restritiva",
            "Gerentes podem forçar cancelamento sem multa",
            "Todos os cancelamentos são auditados"
        ]
    }
