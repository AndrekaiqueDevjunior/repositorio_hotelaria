"""
Schemas unificados para consulta pública (Voucher + Reserva)
Centraliza o contrato de API para acesso público sem autenticação
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime

class ClienteInfo(BaseModel):
    nome_completo: str = Field(..., description="Nome completo do cliente")
    email: str = Field(..., description="Email do cliente")
    telefone: str = Field(..., description="Telefone do cliente")

class QuartoInfo(BaseModel):
    numero: str = Field(..., description="Número do quarto")
    tipo_suite: str = Field(..., description="Tipo de suíte")
    andar: Optional[str] = Field(None, description="Andar do quarto")

class DatasReserva(BaseModel):
    checkin_previsto: datetime = Field(..., description="Data/hora check-in previsto")
    checkout_previsto: datetime = Field(..., description="Data/hora checkout previsto")
    checkin_realizado: Optional[datetime] = Field(None, description="Data/hora check-in realizado")
    checkout_realizado: Optional[datetime] = Field(None, description="Data/hora checkout realizado")
    num_diarias: int = Field(..., description="Número de diárias")

class ValoresReserva(BaseModel):
    valor_diaria: float = Field(..., description="Valor da diária")
    valor_total: float = Field(..., description="Valor total da reserva")
    metodo_pagamento: Optional[str] = Field(None, description="Método de pagamento")

class PagamentoInfo(BaseModel):
    id: int
    status: str = Field(..., description="Status do pagamento")
    valor: float = Field(..., description="Valor pago")
    metodo: str = Field(..., description="Método de pagamento")
    data: datetime = Field(..., description="Data do pagamento")

class InstrucoesCheckin(BaseModel):
    horario_checkin: str = Field("12:00", description="Horário de check-in")
    horario_checkout: str = Field("11:00", description="Horário de checkout")
    documentos: str = Field("Apresente documento de identidade e CPF", description="Documentos necessários")
    contato: str = Field("(22) 2648-5900 ou contato@hotelrealcabofrio.com.br", description="Contato do hotel")

class ConsultaPublicaResponse(BaseModel):
    """Schema unificado para resposta de consulta pública"""
    success: bool = Field(True, description="Indica se a consulta foi bem-sucedida")
    tipo: Literal["VOUCHER", "RESERVA"] = Field(..., description="Tipo de consulta realizada")
    codigo: str = Field(..., description="Código único (voucher ou reserva)")
    status: str = Field(..., description="Status atual")
    cliente: ClienteInfo = Field(..., description="Informações do cliente")
    quarto: QuartoInfo = Field(..., description="Informações do quarto")
    datas: DatasReserva = Field(..., description="Datas da reserva")
    valores: ValoresReserva = Field(..., description="Valores da reserva")
    pagamentos: Optional[List[PagamentoInfo]] = Field(None, description="Lista de pagamentos")
    instrucoes: InstrucoesCheckin = Field(..., description="Instruções para check-in")
    
    # Campos específicos de voucher
    data_emissao: Optional[datetime] = Field(None, description="Data de emissão (apenas voucher)")
    
    # Links cruzados para melhor UX
    links: Optional[dict] = Field(None, description="Links relacionados (voucher ↔ reserva)")

class ConsultaPublicaRequest(BaseModel):
    """Schema para requisição de consulta pública"""
    codigo: str = Field(..., description="Código a ser consultado (voucher ou reserva)")
    tipo: Optional[Literal["AUTO", "VOUCHER", "RESERVA"]] = Field("AUTO", description="Tipo de consulta (AUTO detecta automaticamente)")

class ErroConsultaPublica(BaseModel):
    """Schema padronizado para erros de consulta pública"""
    success: bool = Field(False, description="Indica falha na consulta")
    erro: str = Field(..., description="Tipo de erro")
    mensagem: str = Field(..., description="Mensagem amigável para o usuário")
    codigo_consultado: str = Field(..., description="Código que foi tentado consultar")
    sugestoes: Optional[List[str]] = Field(None, description="Sugestões para o usuário")
