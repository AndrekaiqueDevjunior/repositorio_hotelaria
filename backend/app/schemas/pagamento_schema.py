from datetime import datetime
from app.utils.datetime_utils import now_utc, to_utc
from typing import Optional
from pydantic import BaseModel


class PagamentoCreate(BaseModel):
    reserva_id: int
    valor: float
    metodo: str  # credit_card, debit_card, pix
    parcelas: Optional[int] = None
    cartao_numero: Optional[str] = None
    cartao_validade: Optional[str] = None
    cartao_cvv: Optional[str] = None
    cartao_nome: Optional[str] = None


class PagamentoResponse(BaseModel):
    id: int
    reserva_id: Optional[int] = None
    reserva_codigo: Optional[str] = None
    quarto_numero: Optional[str] = None
    cliente_id: Optional[int] = None
    cliente_nome: Optional[str] = None
    cliente_email: Optional[str] = None
    cielo_payment_id: Optional[str] = None
    status: str
    valor: float
    metodo: str
    parcelas: Optional[int] = None
    cartao_nome: Optional[str] = None
    cartao_final: Optional[str] = None
    url_pagamento: Optional[str] = None
    data_criacao: Optional[datetime] = None
    risk_score: Optional[int] = None
    
    class Config:
        from_attributes = True
        populate_by_name = True


class CieloWebhook(BaseModel):
    payment_id: str
    status: str
    authorization_code: Optional[str] = None
    response_code: Optional[str] = None
    response_message: Optional[str] = None
