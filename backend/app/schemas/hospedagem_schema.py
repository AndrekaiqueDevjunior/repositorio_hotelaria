"""
Schemas para Hospedagem (Estado Operacional)
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.schemas.status_enums import StatusHospedagem


class HospedagemCreate(BaseModel):
    """Dados para criar hospedagem (automático ao confirmar reserva)"""
    reserva_id: int
    num_hospedes: Optional[int] = 1
    num_criancas: Optional[int] = 0
    placa_veiculo: Optional[str] = None
    observacoes: Optional[str] = None


class HospedagemCheckinRequest(BaseModel):
    """Dados para realizar check-in"""
    num_hospedes: Optional[int] = 1
    num_criancas: Optional[int] = 0
    placa_veiculo: Optional[str] = None
    observacoes: Optional[str] = None


class HospedagemCheckoutRequest(BaseModel):
    """Dados para realizar checkout"""
    consumo_frigobar: Optional[float] = 0
    servicos_extras: Optional[float] = 0
    avaliacao: Optional[int] = 5
    comentario_avaliacao: Optional[str] = None


class HospedagemResponse(BaseModel):
    """Response de hospedagem"""
    id: int
    reserva_id: int
    status_hospedagem: StatusHospedagem
    checkin_realizado_em: Optional[datetime]
    checkin_realizado_por: Optional[int]
    checkout_realizado_em: Optional[datetime]
    checkout_realizado_por: Optional[int]
    num_hospedes: Optional[int]
    num_criancas: Optional[int]
    placa_veiculo: Optional[str]
    observacoes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
