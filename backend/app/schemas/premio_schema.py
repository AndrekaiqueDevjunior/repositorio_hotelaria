"""
Schemas para o sistema de prêmios/recompensas.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class PremioBase(BaseModel):
    nome: str = Field(..., min_length=1, max_length=255)
    descricao: Optional[str] = None
    preco_em_pontos: int = Field(..., gt=0)
    preco_em_rp: Optional[int] = None
    categoria: Optional[str] = "GERAL"
    estoque: Optional[int] = None
    imagem_url: Optional[str] = None


class PremioCreate(PremioBase):
    ativo: bool = True


class PremioUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    preco_em_pontos: Optional[int] = None
    preco_em_rp: Optional[int] = None
    ativo: Optional[bool] = None
    categoria: Optional[str] = None
    estoque: Optional[int] = None
    imagem_url: Optional[str] = None


class PremioResponse(PremioBase):
    id: int
    ativo: bool
    created_at: Optional[str] = None
    
    class Config:
        from_attributes = True


class ResgatePremioRequest(BaseModel):
    cliente_id: int
    premio_id: int


class ResgatePremioPublicoRequest(BaseModel):
    premio_id: int
    cliente_documento: str
    observacoes: Optional[str] = None


class ResgatePremioResponse(BaseModel):
    success: bool
    resgate_id: Optional[int] = None
    premio: Optional[PremioResponse] = None
    pontos_usados: Optional[int] = None
    novo_saldo: Optional[int] = None
    transacao_id: Optional[int] = None
    error: Optional[str] = None


class ResgateHistoricoResponse(BaseModel):
    id: int
    premio_id: int
    premio_nome: Optional[str] = None
    pontos_usados: int
    status: str
    data_resgate: Optional[str] = None


class ConfirmarEntregaRequest(BaseModel):
    resgate_id: int


class PremiosDisponiveis(BaseModel):
    """Response para consulta de prêmios disponíveis para um cliente"""
    cliente_id: int
    saldo_atual: int
    premios_disponiveis: List[PremioResponse]
    premios_proximos: List[dict]  # Prêmios que o cliente quase pode resgatar
