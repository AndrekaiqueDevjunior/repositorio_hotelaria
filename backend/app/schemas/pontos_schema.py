from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class ValidarReservaRequest(BaseModel):
    codigo_reserva: str
    cpf_hospede: str
    usuario_id: int


class ConfirmarLancamentoRequest(BaseModel):
    reserva_id: int
    cliente_id: int
    cpf_hospede: str
    usuario_id: int


class AjustarPontosRequest(BaseModel):
    cliente_id: int
    pontos: int  # positivo para creditar, negativo para debitar
    motivo: str
    usuario_id: int


class GerarConviteRequest(BaseModel):
    convidante_cliente_id: int
    usos_maximos: int = 5


class UsarConviteRequest(BaseModel):
    codigo: str
    cliente_id: int  # quem está usando o convite


class SaldoResponse(BaseModel):
    success: bool
    saldo: int = 0
    usuario_pontos_id: int = 0
    error: Optional[str] = None


class TransacaoResponse(BaseModel):
    success: bool
    transacao_id: int = 0
    novo_saldo: int = 0
    error: Optional[str] = None


class HistoricoTransacao(BaseModel):
    id: int
    tipo: str
    pontos: int
    saldo_anterior: int
    saldo_posterior: int
    origem: str
    created_at: datetime
    reserva_codigo: Optional[str] = None


class HistoricoResponse(BaseModel):
    success: bool
    transacoes: List[HistoricoTransacao]
    total: int
    error: Optional[str] = None


class ValidarReservaResponse(BaseModel):
    success: bool
    pontos_ganhos: int = 0
    valor_reserva: float = 0.0
    data_checkout: str = ""
    error: Optional[str] = None


class ConviteResponse(BaseModel):
    success: bool
    codigo: str = ""
    usos_maximos: int = 0
    usos_restantes: int = 0
    error: Optional[str] = None


class HistoricoPontosItem(BaseModel):
    id: int
    tipo: str
    pontos: int
    origem: str
    created_at: datetime
    reserva_codigo: Optional[str] = None
