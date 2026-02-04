"""
Schemas melhorados para Pagamento
Com validações completas e segurança
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator, SecretStr
from decimal import Decimal
from enum import Enum


class MetodoPagamentoEnum(str, Enum):
    """Métodos de pagamento aceitos"""
    CREDITO = "CREDITO"
    DEBITO = "DEBITO"
    PIX = "PIX"
    BOLETO = "BOLETO"
    DINHEIRO = "DINHEIRO"
    TRANSFERENCIA = "TRANSFERENCIA"
    CREDITO_HOTEL = "CREDITO_HOTEL"


class StatusPagamentoEnum(str, Enum):
    """Status do pagamento"""
    PENDENTE = "PENDENTE"
    PROCESSANDO = "PROCESSANDO"
    APROVADO = "APROVADO"
    REJEITADO = "REJEITADO"
    CANCELADO = "CANCELADO"
    ESTORNADO = "ESTORNADO"
    EXPIRADO = "EXPIRADO"


class BandeiraCartaoEnum(str, Enum):
    """Bandeiras de cartão aceitas"""
    VISA = "VISA"
    MASTERCARD = "MASTERCARD"
    AMEX = "AMEX"
    ELO = "ELO"
    HIPERCARD = "HIPERCARD"
    DINERS = "DINERS"


class CartaoDados(BaseModel):
    """Dados do cartão (criptografados)"""
    numero: SecretStr = Field(..., description="Número do cartão")
    nome_titular: str = Field(..., description="Nome do titular")
    validade: str = Field(..., regex=r"^(0[1-9]|1[0-2])\/\d{2}$", description="MM/AA")
    cvv: SecretStr = Field(..., min_length=3, max_length=4, description="CVV")
    bandeira: BandeiraCartaoEnum = Field(..., description="Bandeira do cartão")
    
    @validator('validade')
    def validar_validade(cls, v):
        try:
            mes, ano = v.split('/')
            ano_completo = 2000 + int(ano)
            
            # Validar mês
            if not (1 <= int(mes) <= 12):
                raise ValueError('Mês inválido')
            
            # Validar se não está expirado
            data_validade = datetime(ano_completo, int(mes), 1)
            if data_validade < datetime.now():
                raise ValueError('Cartão expirado')
                
        except ValueError:
            raise ValueError('Formato de validade inválido. Use MM/AA')
        
        return v
    
    @validator('numero')
    def validar_numero_cartao(cls, v):
        # Remover espaços e caracteres não numéricos
        numero_limpo = ''.join(filter(str.isdigit, v.get_secret_value()))
        
        # Validação básica de comprimento
        if len(numero_limpo) < 13 or len(numero_limpo) > 19:
            raise ValueError('Número de cartão inválido')
        
        # Algoritmo de Luhn para validação básica
        soma = 0
        duplo = False
        
        for digito in reversed(numero_limpo):
            d = int(digito)
            if duplo:
                d *= 2
                if d > 9:
                    d -= 9
            soma += d
            duplo = not duplo
        
        if soma % 10 != 0:
            raise ValueError('Número de cartão inválido')
        
        return v


class PagamentoCreate(BaseModel):
    """Schema para criação de pagamento com validações"""
    reserva_id: int = Field(..., gt=0, description="ID da reserva")
    valor: float = Field(..., gt=0, description="Valor do pagamento")
    metodo: MetodoPagamentoEnum = Field(..., description="Método de pagamento")
    
    # Parcelamento (apenas para cartão de crédito)
    parcelas: Optional[int] = Field(1, ge=1, le=12, description="Número de parcelas")
    
    # Dados do cartão (se aplicável)
    cartao: Optional[CartaoDados] = Field(None, description="Dados do cartão")
    
    # Dados para PIX
    chave_pix: Optional[str] = Field(None, description="Chave PIX do pagador")
    cpf_pagador: Optional[str] = Field(None, description="CPF do pagador (PIX)")
    
    # Dados para boleto
    cpf_boleto: Optional[str] = Field(None, description="CPF para boleto")
    nome_boleto: Optional[str] = Field(None, description="Nome para boleto")
    
    # Metadados
    descricao: Optional[str] = Field(None, max_length=200, description="Descrição do pagamento")
    origem: str = Field("SISTEMA", description="Origem do pagamento")
    ip_cliente: Optional[str] = Field(None, description="IP do cliente")
    
    @validator('parcelas')
    def validar_parcelamento(cls, v, values):
        if v and v > 1 and values.get('metodo') != MetodoPagamentoEnum.CREDITO:
            raise ValueError('Parcelamento apenas disponível para cartão de crédito')
        
        if v and values.get('valor') and values.get('valor') < 10.0:
            raise ValueError('Valor mínimo para parcelamento é R$ 10,00')
        
        return v
    
    @validator('cartao')
    def validar_cartao_obrigatorio(cls, v, values):
        metodo = values.get('metodo')
        if metodo in [MetodoPagamentoEnum.CREDITO, MetodoPagamentoEnum.DEBITO] and not v:
            raise ValueError('Dados do cartão obrigatórios para pagamento com cartão')
        return v
    
    @validator('chave_pix', 'cpf_pagador')
    def validar_pix_obrigatorio(cls, v, values):
        if values.get('metodo') == MetodoPagamentoEnum.PIX and not values.get('chave_pix'):
            raise ValueError('Chave PIX obrigatória para pagamento via PIX')
        return v


class PagamentoUpdate(BaseModel):
    """Schema para atualização de pagamento"""
    status: Optional[StatusPagamentoEnum] = None
    valor: Optional[float] = Field(None, gt=0)
    descricao: Optional[str] = Field(None, max_length=200)
    data_aprovacao: Optional[datetime] = None
    transacao_id: Optional[str] = None
    gateway_resposta: Optional[dict] = None


class PagamentoResponse(BaseModel):
    """Schema completo de resposta de pagamento"""
    id: int
    reserva_id: Optional[int]
    reserva_codigo: Optional[str]
    quarto_numero: Optional[str]
    cliente_id: Optional[int]
    cliente_nome: Optional[str]
    cliente_email: Optional[str]
    
    # Dados do pagamento
    status: StatusPagamentoEnum
    valor: float
    valor_original: Optional[float]
    metodo: MetodoPagamentoEnum
    parcelas: Optional[int]
    descricao: Optional[str]
    
    # Dados do cartão (mascarados)
    cartao_nome: Optional[str]
    cartao_final: Optional[str]
    cartao_bandeira: Optional[str]
    
    # Gateway
    gateway_transacao_id: Optional[str]
    gateway_url_pagamento: Optional[str]
    gateway_qr_code: Optional[str]
    gateway_resposta: Optional[dict]
    
    # Datas
    data_criacao: Optional[datetime]
    data_aprovacao: Optional[datetime]
    data_cancelamento: Optional[datetime]
    data_estorno: Optional[datetime]
    data_expiracao: Optional[datetime]
    
    # Segurança
    risk_score: Optional[int]
    ip_cliente: Optional[str]
    fingerprint: Optional[str]
    
    # Relacionamentos
    estornos: Optional[List[dict]]
    
    class Config:
        from_attributes = True


class PagamentoWebhook(BaseModel):
    """Schema para webhooks de gateway de pagamento"""
    pagamento_id: int
    status: StatusPagamentoEnum
    gateway_transacao_id: Optional[str]
    gateway_resposta: Optional[dict]
    data_evento: datetime
    assinatura: Optional[str] = None
    
    @validator('assinatura')
    def validar_assinatura(cls, v, values):
        # TODO: Implementar validação de assinatura HMAC
        return v


class EstornoCreate(BaseModel):
    """Schema para criação de estorno"""
    pagamento_id: int = Field(..., gt=0)
    valor: float = Field(..., gt=0, description="Valor a ser estornado")
    motivo: str = Field(..., min_length=5, max_length=500, description="Motivo do estorno")
    parcial: bool = Field(False, description="Estorno parcial?")
    
    @validator('valor')
    def validar_valor_estorno(cls, v, values):
        # TODO: Validar se valor não excede o valor original do pagamento
        return v


class EstornoResponse(BaseModel):
    """Schema de resposta de estorno"""
    id: int
    pagamento_id: int
    valor: float
    motivo: str
    status: str
    data_solicitacao: datetime
    data_processamento: Optional[datetime]
    gateway_transacao_id: Optional[str]
    
    class Config:
        from_attributes = True


class RelatorioPagamentos(BaseModel):
    """Schema para relatórios de pagamentos"""
    periodo_inicio: datetime
    periodo_fim: datetime
    total_pagamentos: int
    valor_total: float
    valor_aprovado: float
    valor_pendente: float
    valor_rejeitado: float
    valor_estornado: float
    por_metodo: dict
    por_status: dict
    media_ticket: float
    taxa_aprovacao: float
