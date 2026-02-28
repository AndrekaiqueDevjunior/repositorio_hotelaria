"""
Schemas completos para Voucher
Com validações de segurança e autenticidade
"""
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field, validator
from enum import Enum
import uuid
import hashlib


class TipoVoucherEnum(str, Enum):
    """Tipos de voucher disponíveis"""
    CONFIRMACAO = "CONFIRMACAO"
    PRESENTE = "PRESENTE"
    CORTESIA = "CORTESIA"
    PROMOCIONAL = "PROMOCIONAL"
    REEMBOLSO = "REEMBOLSO"


class StatusVoucherEnum(str, Enum):
    """Status do voucher"""
    EMITIDO = "EMITIDO"
    ATIVO = "ATIVO"
    UTILIZADO = "UTILIZADO"
    EXPIRADO = "EXPIRADO"
    CANCELADO = "CANCELADO"
    SUSPENSO = "SUSPENSO"


class VoucherCreate(BaseModel):
    """Schema para criação de voucher"""
    reserva_id: int = Field(..., gt=0, description="ID da reserva associada")
    tipo_voucher: TipoVoucherEnum = Field(..., description="Tipo do voucher")
    
    # Dados de emissão
    emitente_funcionario_id: int = Field(..., gt=0, description="ID do funcionário emissor")
    observacoes: Optional[str] = Field(None, max_length=500, description="Observações")
    
    # Validação
    data_validade: Optional[datetime] = Field(None, description="Data de validade customizada")
    restricoes: Optional[str] = Field(None, max_length=1000, description="Restrições de uso")
    
    # Segurança
    senha_acesso: Optional[str] = Field(None, min_length=4, max_length=20, description="Senha para acesso")
    nivel_acesso: str = Field("PUBLICO", description="Nível de acesso")
    
    @validator('data_validade')
    def validar_validade_minima(cls, v):
        if v and v < datetime.now():
            raise ValueError('Data de validade não pode ser no passado')
        return v
    
    @validator('senha_acesso')
    def gerar_senha_automatica(cls, v):
        if not v:
            # Gerar senha automática
            import random
            import string
            return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return v


class VoucherUpdate(BaseModel):
    """Schema para atualização de voucher"""
    status: Optional[StatusVoucherEnum] = None
    data_validade: Optional[datetime] = None
    observacoes: Optional[str] = Field(None, max_length=500)
    restricoes: Optional[str] = Field(None, max_length=1000)
    senha_acesso: Optional[str] = Field(None, min_length=4, max_length=20)
    motivo_cancelamento: Optional[str] = Field(None, max_length=500, description="Motivo do cancelamento")


class VoucherValidacao(BaseModel):
    """Schema para validação de voucher"""
    codigo_voucher: str = Field(..., min_length=8, max_length=20, description="Código do voucher")
    senha_acesso: Optional[str] = Field(None, description="Senha de acesso (se requerida)")
    contexto_validacao: str = Field("CHECKIN", description="Contexto: CHECKIN, CHECKOUT, CONSULTA")
    
    @validator('codigo_voucher')
    def formatar_codigo(cls, v):
        return v.upper().strip()


class VoucherResponse(BaseModel):
    """Schema completo de resposta de voucher"""
    id: int
    codigo_voucher: str
    codigo_seguranca: Optional[str]  # Hash para verificação
    reserva_id: int
    tipo_voucher: TipoVoucherEnum
    status: StatusVoucherEnum
    
    # Dados de emissão
    data_emissao: datetime
    emitente_funcionario_id: int
    emitente_funcionario_nome: Optional[str]
    
    # Validação
    data_validade: Optional[datetime]
    data_utilizacao: Optional[datetime]
    data_cancelamento: Optional[datetime]
    
    # Segurança
    senha_acesso: Optional[str]  # Não expor senha completa
    possui_senha: bool
    nivel_acesso: str
    qr_code: Optional[str]
    hash_verificacao: str
    
    # Relacionamentos
    reserva: Optional[dict]
    cliente: Optional[dict]
    quarto: Optional[dict]
    
    # Conteúdo do voucher
    titulo: str
    descricao: str
    instrucoes: List[str]
    restricoes: Optional[str]
    beneficios: List[str]
    
    # Arquivos
    url_pdf: Optional[str]
    url_imagem: Optional[str]
    
    # Metadados
    observacoes: Optional[str]
    motivo_cancelamento: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class VoucherPublicResponse(BaseModel):
    """Schema público de voucher (sem dados sensíveis)"""
    codigo_voucher: str
    tipo_voucher: TipoVoucherEnum
    status: StatusVoucherEnum
    data_emissao: datetime
    data_validade: Optional[datetime]
    qr_code: Optional[str]
    
    # Conteúdo público
    titulo: str
    descricao: str
    instrucoes: List[str]
    restricoes: Optional[str]
    
    # Informações básicas
    nome_cliente: Optional[str]
    nome_hotel: str
    endereco_hotel: str
    contato_hotel: str
    
    # Arquivos
    url_pdf: Optional[str]
    url_imagem: Optional[str]
    
    class Config:
        from_attributes = True


class VoucherCheckin(BaseModel):
    """Schema para validação de voucher no check-in"""
    voucher_id: int
    codigo_voucher: str
    valido_para_checkin: bool
    mensagem_validacao: str
    dados_reserva: Optional[dict]
    restricoes_checkin: List[str]
    
    # Validação de identidade
    documento_obrigatorio: bool
    assinatura_obrigatoria: bool
    foto_obrigatoria: bool


class VoucherCheckout(BaseModel):
    """Schema para validação de voucher no check-out"""
    voucher_id: int
    codigo_voucher: str
    utilizado_checkin: bool
    valido_para_checkout: bool
    mensagem_validacao: str
    consumos_registrados: bool
    pendencias_pagamento: List[str]


class VoucherRelatorio(BaseModel):
    """Schema para relatórios de vouchers"""
    periodo_inicio: date
    periodo_fim: date
    total_vouchers: int
    vouchers_emitidos: int
    vouchers_utilizados: int
    vouchers_expirados: int
    vouchers_cancelados: int
    
    # Por tipo
    vouchers_por_tipo: dict
    
    # Por status
    vouchers_por_status: dict
    
    # Financeiro
    valor_total_vouchers: float
    valor_medio_voucher: float
    
    # Eficiência
    taxa_utilizacao: float
    taxa_expiracao: float


class VoucherBatch(BaseModel):
    """Schema para criação em lote de vouchers"""
    tipo_voucher: TipoVoucherEnum
    quantidade: int = Field(..., gt=0, le=100, description="Quantidade de vouchers")
    valor_unitario: Optional[float] = Field(None, gt=0, description="Valor por voucher")
    data_validade: Optional[datetime] = None
    restricoes: Optional[str] = None
    emitente_funcionario_id: int
    
    @validator('quantidade')
    def validar_limite_lote(cls, v):
        if v > 100:
            raise ValueError('Limite máximo de 100 vouchers por lote')
        return v


class VoucherTemplate(BaseModel):
    """Schema para template de voucher"""
    id: int
    nome: str
    tipo_voucher: TipoVoucherEnum
    titulo_padrao: str
    descricao_padrao: str
    instrucoes_padrao: List[str]
    restricoes_padrao: Optional[str]
    beneficios_padrao: List[str]
    layout_pdf: Optional[str]
    ativo: bool
    
    class Config:
        from_attributes = True


# Utilitários para voucher
def gerar_codigo_voucher() -> str:
    """Gera código único de voucher"""
    timestamp = datetime.now().strftime("%Y%m%d")
    random_num = str(uuid.uuid4())[:8].upper()
    return f"VCR{timestamp}{random_num}"


def gerar_hash_verificacao(voucher_data: dict) -> str:
    """Gera hash de verificação para voucher"""
    string_data = f"{voucher_data.get('codigo_voucher')}{voucher_data.get('reserva_id')}{voucher_data.get('data_emissao')}"
    return hashlib.sha256(string_data.encode()).hexdigest()[:16].upper()


def gerar_qr_code_data(codigo_voucher: str, hash_verificacao: str) -> str:
    """Gera dados para QR code"""
    return f"VCR:{codigo_voucher}:{hash_verificacao}"
