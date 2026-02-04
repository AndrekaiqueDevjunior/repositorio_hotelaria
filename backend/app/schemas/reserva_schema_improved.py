"""
Schemas melhorados para Reserva
Com validações completas e campos adicionais
"""
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field, validator
from decimal import Decimal
from app.schemas.quarto_schema import TipoSuite
from app.schemas.status_enums import StatusReserva


class ReservaCreate(BaseModel):
    """Schema para criação de reserva com validações completas"""
    cliente_id: int = Field(..., gt=0, description="ID do cliente")
    quarto_numero: str = Field(..., min_length=1, max_length=10, description="Número do quarto")
    tipo_suite: TipoSuite = Field(..., description="Tipo de suíte")
    checkin_previsto: datetime = Field(..., description="Data/hora prevista para check-in")
    checkout_previsto: datetime = Field(..., description="Data/hora prevista para check-out")
    valor_diaria: Optional[float] = Field(None, gt=0, description="Valor da diária")
    num_diarias: int = Field(..., gt=0, description="Número de diárias")
    
    # Campos adicionais
    num_hospedes: int = Field(1, gt=0, description="Número de hóspedes")
    num_criancas: int = Field(0, ge=0, description="Número de crianças")
    necessidades_especiais: Optional[str] = Field(None, description="Necessidades especiais")
    observacoes: Optional[str] = Field(None, max_length=500, description="Observações da reserva")
    
    # Informações de pagamento
    forma_pagamento: Optional[str] = Field(None, description="Forma de pagamento pretendida")
    valor_sinal: Optional[float] = Field(None, ge=0, description="Valor do sinal pago")
    
    # Contato
    telefone_contato: Optional[str] = Field(None, description="Telefone para contato")
    email_contato: Optional[str] = Field(None, description="Email para contato")
    
    @validator('checkout_previsto')
    def validar_datas(cls, v, values):
        if 'checkin_previsto' in values:
            checkin = values['checkin_previsto']
            if v <= checkin:
                raise ValueError('Checkout deve ser posterior ao check-in')
            
            # Validar duração mínima (1 diária = 24h)
            duracao_minima = checkin + datetime.timedelta(hours=24)
            if v < duracao_minima:
                raise ValueError('Período mínimo de hospedagem é de 24 horas')
        return v
    
    @validator('num_diarias')
    def calcular_num_diarias(cls, v, values):
        if 'checkin_previsto' in values and 'checkout_previsto' in values:
            checkin = values['checkin_previsto']
            checkout = values['checkout_previsto']
            
            # Calcular diárias baseado no período real
            duracao_horas = (checkout - checkin).total_seconds() / 3600
            diarias_calculadas = max(1, int(duracao_horas / 24))
            
            if abs(v - diarias_calculadas) > 0.5:
                raise ValueError(f'Número de diárias incorreto. Deveria ser {diarias_calculadas}')
        return v
    
    @validator('valor_diaria')
    def validar_valor_diaria(cls, v, values):
        if v is None:
            # Buscar tarifa automática baseada no tipo de suíte e datas
            # TODO: Implementar busca automática de tarifa
            pass
        return v


class ReservaUpdate(BaseModel):
    """Schema para atualização de reserva"""
    status: Optional[StatusReserva] = None
    checkin_previsto: Optional[datetime] = None
    checkout_previsto: Optional[datetime] = None
    valor_diaria: Optional[float] = Field(None, gt=0)
    num_diarias: Optional[int] = Field(None, gt=0)
    num_hospedes: Optional[int] = Field(None, gt=0)
    num_criancas: Optional[int] = Field(None, ge=0)
    observacoes: Optional[str] = Field(None, max_length=500)
    
    @validator('checkout_previsto')
    def validar_datas_update(cls, v, values):
        if v and 'checkin_previsto' in values and values['checkin_previsto']:
            if v <= values['checkin_previsto']:
                raise ValueError('Checkout deve ser posterior ao check-in')
        return v


class ReservaResponse(BaseModel):
    """Schema completo de resposta de reserva"""
    id: int
    codigo_reserva: str
    cliente_id: int
    cliente_nome: Optional[str]
    cliente_email: Optional[str]
    cliente_telefone: Optional[str]
    quarto_numero: str
    tipo_suite: TipoSuite
    andar: Optional[str]
    status: StatusReserva
    
    # Datas
    checkin_previsto: Optional[datetime]
    checkout_previsto: Optional[datetime]
    checkin_realizado: Optional[datetime]
    checkout_realizado: Optional[datetime]
    
    # Valores
    valor_diaria: float
    num_diarias: int
    valor_total: float
    valor_sinal: Optional[float]
    valor_restante: Optional[float]
    
    # Ocupação
    num_hospedes: int
    num_criancas: int
    
    # Relacionamentos
    pagamentos: Optional[List[dict]]
    hospedagem: Optional[dict]
    voucher: Optional[dict]
    
    # Metadados
    observacoes: Optional[str]
    necessidades_especiais: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    cancelado_em: Optional[datetime]
    motivo_cancelamento: Optional[str]
    
    class Config:
        from_attributes = True


class ReservaListResponse(BaseModel):
    """Schema para listagem de reservas (campos reduzidos)"""
    id: int
    codigo_reserva: str
    cliente_nome: Optional[str]
    quarto_numero: str
    tipo_suite: TipoSuite
    status: StatusReserva
    checkin_previsto: Optional[datetime]
    checkout_previsto: Optional[datetime]
    valor_total: float
    created_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ReservaDashboard(BaseModel):
    """Schema para dashboard de reservas"""
    total_reservas: int
    reservas_pendentes: int
    reservas_confirmadas: int
    reservas_hospedadas: int
    checkouts_hoje: int
    checkins_hoje: int
    ocupacao_atual: float
    faturamento_mes: float
    proximas_chegadas: List[dict]
    proximas_partidas: List[dict]


class ReservaRelatorio(BaseModel):
    """Schema para relatórios de reservas"""
    periodo_inicio: date
    periodo_fim: date
    total_reservas: int
    total_hospedes: int
    taxa_ocupacao: float
    faturamento_total: float
    faturamento_medio_diaria: float
    top_quartos: List[dict]
    cancelamentos: int
    no_shows: int
