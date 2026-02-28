from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List
from pydantic import BaseModel, validator
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.consumo_hospedagem_service import ConsumoHospedagemService
from app.middleware.auth_middleware import get_current_active_user
from app.core.security import User
from app.core.exceptions import ValidationError, BusinessRuleViolation


router = APIRouter(prefix="/consumos", tags=["consumos-hospedagem"])


# Schemas
class ItemFrigobarRequest(BaseModel):
    item: str
    quantidade: int
    valor_unitario: float
    
    @validator('quantidade')
    def validate_quantidade(cls, v):
        if v <= 0:
            raise ValueError('Quantidade deve ser positiva')
        return v
    
    @validator('valor_unitario')
    def validate_valor(cls, v):
        if v <= 0:
            raise ValueError('Valor deve ser positivo')
        return v


class ConsumoFrigobarRequest(BaseModel):
    itens: List[ItemFrigobarRequest]
    
    @validator('itens')
    def validate_itens(cls, v):
        if not v:
            raise ValueError('Deve haver pelo menos um item')
        return v


class ServicoExtraRequest(BaseModel):
    servico: str
    valor: float
    observacoes: str = None
    
    @validator('servico')
    def validate_servico(cls, v):
        if len(v.strip()) < 3:
            raise ValueError('Nome do serviço deve ter pelo menos 3 caracteres')
        return v.strip()
    
    @validator('valor')
    def validate_valor(cls, v):
        if v <= 0:
            raise ValueError('Valor deve ser positivo')
        return v


class MultaRequest(BaseModel):
    motivo: str
    valor: float
    
    @validator('motivo')
    def validate_motivo(cls, v):
        if len(v.strip()) < 10:
            raise ValueError('Motivo deve ter pelo menos 10 caracteres')
        return v.strip()
    
    @validator('valor')
    def validate_valor(cls, v):
        if v <= 0:
            raise ValueError('Valor deve ser positivo')
        return v


class DanoRequest(BaseModel):
    descricao_dano: str
    valor_reparo: float
    evidencias: str = None
    
    @validator('descricao_dano')
    def validate_descricao(cls, v):
        if len(v.strip()) < 10:
            raise ValueError('Descrição deve ter pelo menos 10 caracteres')
        return v.strip()
    
    @validator('valor_reparo')
    def validate_valor(cls, v):
        if v <= 0:
            raise ValueError('Valor deve ser positivo')
        return v


class LateCheckoutRequest(BaseModel):
    horas_excedidas: int
    valor_por_hora: float = 50.00
    
    @validator('horas_excedidas')
    def validate_horas(cls, v):
        if v <= 0 or v > 24:
            raise ValueError('Horas excedidas deve ser entre 1 e 24')
        return v
    
    @validator('valor_por_hora')
    def validate_valor(cls, v):
        if v <= 0:
            raise ValueError('Valor por hora deve ser positivo')
        return v


class DescontoRequest(BaseModel):
    motivo: str
    valor: float
    
    @validator('motivo')
    def validate_motivo(cls, v):
        if len(v.strip()) < 5:
            raise ValueError('Motivo deve ter pelo menos 5 caracteres')
        return v.strip()
    
    @validator('valor')
    def validate_valor(cls, v):
        if v <= 0:
            raise ValueError('Valor deve ser positivo')
        return v


class EstornoRequest(BaseModel):
    motivo: str
    
    @validator('motivo')
    def validate_motivo(cls, v):
        if len(v.strip()) < 5:
            raise ValueError('Motivo deve ter pelo menos 5 caracteres')
        return v.strip()


@router.post("/{reserva_id}/frigobar")
async def lancar_consumo_frigobar(
    reserva_id: int,
    dados: ConsumoFrigobarRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Lança consumo de frigobar
    Permite múltiplos itens em uma única operação
    """
    try:
        service = ConsumoHospedagemService(db)
        
        # Converter para formato esperado pelo serviço
        itens_consumidos = [
            {
                "item": item.item,
                "quantidade": item.quantidade,
                "valor_unitario": item.valor_unitario
            }
            for item in dados.itens
        ]
        
        resultado = service.lancar_consumo_frigobar(
            reserva_id=reserva_id,
            itens_consumidos=itens_consumidos,
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


@router.post("/{reserva_id}/servico-extra")
async def lancar_servico_extra(
    reserva_id: int,
    dados: ServicoExtraRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Lança serviço extra (lavanderia, room service, spa, etc.)
    """
    try:
        service = ConsumoHospedagemService(db)
        
        resultado = service.lancar_servico_extra(
            reserva_id=reserva_id,
            servico=dados.servico,
            valor=Decimal(str(dados.valor)),
            observacoes=dados.observacoes,
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


@router.post("/{reserva_id}/multa")
async def aplicar_multa(
    reserva_id: int,
    dados: MultaRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Aplica multa por infrações
    Requer justificativa detalhada
    """
    try:
        service = ConsumoHospedagemService(db)
        
        resultado = service.aplicar_multa(
            reserva_id=reserva_id,
            motivo=dados.motivo,
            valor=Decimal(str(dados.valor)),
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


@router.post("/{reserva_id}/dano")
async def registrar_dano(
    reserva_id: int,
    dados: DanoRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Registra dano ao quarto/propriedade
    Crítico para controle de patrimônio
    """
    try:
        service = ConsumoHospedagemService(db)
        
        resultado = service.registrar_dano(
            reserva_id=reserva_id,
            descricao_dano=dados.descricao_dano,
            valor_reparo=Decimal(str(dados.valor_reparo)),
            evidencias=dados.evidencias,
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


@router.post("/{reserva_id}/late-checkout")
async def aplicar_taxa_late_checkout(
    reserva_id: int,
    dados: LateCheckoutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Aplica taxa de late checkout
    Padrão: R$ 50,00 por hora excedida
    """
    try:
        service = ConsumoHospedagemService(db)
        
        resultado = service.aplicar_taxa_late_checkout(
            reserva_id=reserva_id,
            horas_excedidas=dados.horas_excedidas,
            valor_por_hora=Decimal(str(dados.valor_por_hora))
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


@router.post("/{reserva_id}/desconto")
async def aplicar_desconto(
    reserva_id: int,
    dados: DescontoRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Aplica desconto (cortesia, compensação, etc.)
    Requer aprovação e rastreamento
    """
    try:
        service = ConsumoHospedagemService(db)
        
        resultado = service.aplicar_desconto(
            reserva_id=reserva_id,
            motivo=dados.motivo,
            valor=Decimal(str(dados.valor)),
            usuario_id=current_user["id"],
            requer_aprovacao=True
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


@router.get("/{reserva_id}")
async def obter_consumos_hospedagem(
    reserva_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Consulta todos os consumos da hospedagem atual
    """
    try:
        service = ConsumoHospedagemService(db)
        resultado = service.obter_consumos_hospedagem(reserva_id)
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


@router.post("/itens/{item_id}/estornar")
async def estornar_item_consumo(
    item_id: int,
    dados: EstornoRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Estorna um item de consumo específico
    Cria lançamento negativo para cancelar o original
    """
    try:
        service = ConsumoHospedagemService(db)
        
        resultado = service.estornar_item_consumo(
            item_id=item_id,
            motivo=dados.motivo,
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


@router.get("/relatorio/{data}")
async def relatorio_consumos_dia(
    data: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Relatório de consumos do dia para controle operacional
    """
    try:
        service = ConsumoHospedagemService(db)
        relatorio = service.obter_relatorio_consumos_dia(data)
        
        # Calcular totais por tipo
        totais_por_tipo = {}
        total_geral = 0
        
        for item in relatorio:
            tipo = item["tipo"]
            valor = item["valor_total"]
            
            if tipo not in totais_por_tipo:
                totais_por_tipo[tipo] = 0
            
            totais_por_tipo[tipo] += valor
            total_geral += valor
        
        return {
            "data": data.isoformat(),
            "total_consumos": len(relatorio),
            "valor_total": total_geral,
            "totais_por_tipo": totais_por_tipo,
            "detalhes": relatorio
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}"
        )
