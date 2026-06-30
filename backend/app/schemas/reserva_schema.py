from datetime import datetime
from app.utils.datetime_utils import now_utc, to_utc
from typing import Optional
from pydantic import BaseModel, Field
from app.schemas.quarto_schema import TipoSuite
from app.schemas.status_enums import StatusReserva


class ReservaCreate(BaseModel):
    cliente_id: int
    quarto_numero: str
    tipo_suite: TipoSuite
    checkin_previsto: datetime
    checkout_previsto: datetime
    valor_diaria: Optional[float] = None
    valor_total: Optional[float] = None
    num_diarias: int
    origem: Optional[str] = Field(default="PARTICULAR", max_length=50)
    responsavel_nome: Optional[str] = Field(default=None, max_length=150)
    forma_pagamento: Optional[str] = Field(default=None, max_length=50)
    observacoes: Optional[str] = Field(default=None, max_length=1000)
    telefone_contato: Optional[str] = Field(default=None, max_length=30)
    email_contato: Optional[str] = Field(default=None, max_length=255)


class ReservaUpdate(BaseModel):
    quarto_numero: Optional[str] = None
    tipo_suite: Optional[TipoSuite] = None
    checkin_previsto: Optional[datetime] = None
    checkout_previsto: Optional[datetime] = None
    valor_diaria: Optional[float] = None
    valor_total: Optional[float] = None
    num_diarias: Optional[int] = None
    origem: Optional[str] = Field(default=None, max_length=50)
    responsavel_nome: Optional[str] = Field(default=None, max_length=150)
    forma_pagamento: Optional[str] = Field(default=None, max_length=50)
    observacoes: Optional[str] = Field(default=None, max_length=1000)
    telefone_contato: Optional[str] = Field(default=None, max_length=30)
    email_contato: Optional[str] = Field(default=None, max_length=255)


class ReservaResponse(BaseModel):
    id: int
    codigo_reserva: str
    cliente_id: int
    cliente_nome: Optional[str]
    quarto_numero: str
    tipo_suite: TipoSuite
    status: str
    checkin_previsto: Optional[datetime]
    checkout_previsto: Optional[datetime]
    checkin_realizado: Optional[datetime]
    checkout_realizado: Optional[datetime]
    valor_diaria: float
    num_diarias: int
    valor_total: float
    origem: Optional[str] = None
    responsavel_nome: Optional[str] = None
    forma_pagamento: Optional[str] = None
    observacoes: Optional[str] = None
    telefone_contato: Optional[str] = None
    email_contato: Optional[str] = None
    valor_desconto: Optional[float] = 0.0
    valor_total_com_desconto: Optional[float] = None
    pagamentos: Optional[list]
    hospedagem: Optional[dict] = None
    cupom_uso: Optional[dict] = None
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
