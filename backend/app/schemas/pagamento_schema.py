from datetime import datetime
from app.utils.datetime_utils import now_utc, to_utc
from typing import Optional
from pydantic import BaseModel, validator


class PagamentoCreate(BaseModel):
    reserva_id: int
    valor: float
    metodo: str
    parcelas: Optional[int] = None
    cartao_numero: Optional[str] = None
    cartao_validade: Optional[str] = None
    cartao_cvv: Optional[str] = None
    cartao_nome: Optional[str] = None

    @validator("metodo", pre=True)
    def normalizar_metodo(cls, value):
        metodo = str(value or "").strip().lower()
        aliases = {
            "credito": "credit_card",
            "crédito": "credit_card",
            "cartao_credito": "credit_card",
            "cartão_credito": "credit_card",
            "cartao de credito": "credit_card",
            "cartão de crédito": "credit_card",
            "debit": "debit_card",
            "debito": "debit_card",
            "débito": "debit_card",
            "cartao_debito": "debit_card",
            "cartão_débito": "debit_card",
            "cartao de debito": "debit_card",
            "cartão de débito": "debit_card",
            "dinheiro": "na_chegada",
            "cash": "na_chegada",
            "pix": "pix",
            "tef": "tef",
            "balcao": "balcao",
            "balcão": "balcao",
            "na_chegada": "na_chegada",
            "na chegada": "na_chegada",
            "credit_card": "credit_card",
            "debit_card": "debit_card",
        }
        normalizado = aliases.get(metodo)
        if not normalizado:
            raise ValueError("Metodo de pagamento invalido")
        return normalizado


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
    nsu: Optional[str] = None
    authorization_code: Optional[str] = None
    tef_nsu: Optional[str] = None
    tef_autorizacao: Optional[str] = None
    tef_cupom_cliente: Optional[str] = None
    tef_cupom_estabelecimento: Optional[str] = None
    tef_cupom_cliente_arquivo: Optional[str] = None
    tef_cupom_estabelecimento_arquivo: Optional[str] = None
    
    class Config:
        from_attributes = True
        populate_by_name = True


class CieloWebhook(BaseModel):
    payment_id: str
    status: str
    authorization_code: Optional[str] = None
    response_code: Optional[str] = None
    response_message: Optional[str] = None
