from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class IndicacaoCreateRequest(BaseModel):
    cliente_indicador_id: int = Field(..., ge=1)
    cpf_indicado: str


class IndicacaoStatusRequest(BaseModel):
    cliente_id: int = Field(..., ge=1)


class IndicacaoResponse(BaseModel):
    id: int
    cliente_indicador_id: int
    cliente_indicado_id: Optional[int] = None
    reserva_id: Optional[int] = None
    cpf_indicador: str
    cpf_indicado: str
    status: str
    data_envio: Optional[datetime] = None
    data_reserva: Optional[datetime] = None
    data_checkin: Optional[datetime] = None
    data_checkout: Optional[datetime] = None
    pontos_creditados: bool = False
    transacao_pontos_id: Optional[int] = None


class IndicacaoStatusResponse(BaseModel):
    status: str
    progresso: str
    ja_ganhou_pontos: bool
    ainda_pode_indicar: bool
    saldo_atual: int
    faltam_pontos_para_proximo_premio: Optional[int] = None
    proximo_premio: Optional[dict] = None
    indicacoes: list[IndicacaoResponse] = Field(default_factory=list)


class IndicacaoReprocessarResponse(BaseModel):
    success: bool
    processadas: int = 0
    creditadas: int = 0
    resultados: list[dict] = Field(default_factory=list)
