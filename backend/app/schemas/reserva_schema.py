from datetime import datetime
from app.utils.datetime_utils import now_utc, to_utc
from typing import Optional
from pydantic import BaseModel
from app.schemas.quarto_schema import TipoSuite
from app.schemas.status_enums import StatusReserva


class ReservaCreate(BaseModel):
    cliente_id: int
    quarto_numero: str
    tipo_suite: TipoSuite
    checkin_previsto: datetime
    checkout_previsto: datetime
    valor_diaria: Optional[float] = None
    num_diarias: int


class ReservaResponse(BaseModel):
    id: int
    codigo_reserva: str
    cliente_id: int
    cliente_nome: Optional[str]
    quarto_numero: str
    tipo_suite: TipoSuite
    status: StatusReserva
    checkin_previsto: Optional[datetime]
    checkout_previsto: Optional[datetime]
    checkin_realizado: Optional[datetime]
    checkout_realizado: Optional[datetime]
    valor_diaria: float
    num_diarias: int
    valor_total: float
    pagamentos: Optional[list]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
