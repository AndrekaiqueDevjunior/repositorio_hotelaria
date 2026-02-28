from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class AntifraudeOperacaoResponse(BaseModel):
    id: int
    reserva_id: Optional[int]
    cliente_id: Optional[int]
    cliente_nome: Optional[str]
    reserva_codigo: Optional[str]
    pagamento_id: Optional[int]
    payment_status: Optional[str]
    pontos_calculados: Optional[int]
    risk_score: Optional[int]
    status: str
    motivo_risco: Optional[str]
    created_at: Optional[datetime]
