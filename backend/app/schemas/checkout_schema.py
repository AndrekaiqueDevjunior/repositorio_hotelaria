"""
Schemas centralizados para Check-in e Check-out
Padronização e validações completas
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator
from enum import Enum


class MetodoPagamentoEnum(str, Enum):
    """Métodos de pagamento aceitos"""
    DINHEIRO = "DINHEIRO"
    CREDITO = "CREDITO"
    DEBITO = "DEBITO"
    PIX = "PIX"
    BOLETO = "BOLETO"


class FormaAcertoEnum(str, Enum):
    """Formas de acerto de consumos"""
    DINHEIRO = "DINHEIRO"
    CREDITO = "CREDITO"
    DEBITO = "DEBITO"
    PIX = "PIX"
    CONTA_HOSPEDAGEM = "CONTA_HOSPEDAGEM"


class DocumentoHospede(BaseModel):
    """Documento de identificação do hóspede"""
    tipo: str = Field(..., description="Tipo: CPF, RG, Passaporte")
    numero: str = Field(..., description="Número do documento")
    nome_completo: str = Field(..., description="Nome completo como no documento")
    data_nascimento: Optional[datetime] = Field(None, description="Data de nascimento")
    nacionalidade: str = Field("Brasil", description="Nacionalidade")


class ConsumoAdicional(BaseModel):
    """Item de consumo adicional durante checkout"""
    descricao: str = Field(..., description="Descrição do consumo")
    quantidade: int = Field(..., ge=1, description="Quantidade")
    valor_unitario: float = Field(..., ge=0, description="Valor unitário")
    valor_total: float = Field(..., ge=0, description="Valor total")
    
    @validator('valor_total')
    def calcular_total(cls, v, values):
        if 'quantidade' in values and 'valor_unitario' in values:
            expected = values['quantidade'] * values['valor_unitario']
            if abs(v - expected) > 0.01:
                raise ValueError('Valor total não corresponde à quantidade × valor unitário')
        return v


class CheckinRequest(BaseModel):
    """Schema completo para check-in"""
    reserva_id: int = Field(..., description="ID da reserva")
    
    # Informações dos hóspedes
    hospedes: List[DocumentoHospede] = Field(..., min_items=1, description="Lista de hóspedes")
    num_hospedes: int = Field(..., ge=1, description="Número total de hóspedes")
    num_criancas: int = Field(0, ge=0, description="Número de crianças")
    
    # Veículo
    placa_veiculo: Optional[str] = Field(None, description="Placa do veículo")
    modelo_veiculo: Optional[str] = Field(None, description="Modelo do veículo")
    
    # Documentos e assinatura
    documentos_checkin: List[str] = Field(default_factory=list, description="URLs dos documentos digitalizados")
    assinatura_digital: Optional[str] = Field(None, description="Assinatura digital do hóspede principal")
    foto_hospede: Optional[str] = Field(None, description="URL da foto do hóspede")
    
    # Pagamento de caução (se aplicável)
    valor_caucao: Optional[float] = Field(None, ge=0, description="Valor da caução")
    metodo_caucao: Optional[MetodoPagamentoEnum] = Field(None, description="Método de pagamento da caução")
    
    # Observações
    observacoes: Optional[str] = Field(None, description="Observações adicionais")
    necessidades_especiais: Optional[str] = Field(None, description="Necessidades especiais")
    
    # Funcionário responsável
    funcionario_id: int = Field(..., description="ID do funcionário que realizou o check-in")
    
    @validator('hospedes')
    def validar_hospedes(cls, v, values):
        if 'num_hospedes' in values and len(v) != values['num_hospedes']:
            raise ValueError('Número de hóspedes não corresponde à lista de documentos')
        return v


class CheckoutRequest(BaseModel):
    """Schema completo para check-out"""
    reserva_id: int = Field(..., description="ID da reserva")
    
    # Vistoria do quarto
    vistoria_ok: bool = Field(True, description="Quarto em ordem?")
    danos_encontrados: Optional[str] = Field(None, description="Descrição de danos")
    fotos_vistoria: List[str] = Field(default_factory=list, description="URLs das fotos da vistoria")
    valor_danos: float = Field(0, ge=0, description="Valor dos danos (se houver)")
    
    # Consumos
    consumo_frigobar: float = Field(0, ge=0, description="Valor total do frigobar")
    servicos_extras: float = Field(0, ge=0, description="Valor de serviços extras")
    consumos_adicionais: List[ConsumoAdicional] = Field(default_factory=list, description="Outros consumos")
    taxa_late_checkout: float = Field(0, ge=0, description="Taxa de late checkout")
    
    # Caução
    caucao_devolvida: float = Field(0, ge=0, description="Valor da caução devolvido")
    caucao_retida: float = Field(0, ge=0, description="Valor da caução retido")
    motivo_retencao: Optional[str] = Field(None, description="Motivo da retenção da caução")
    
    # Acerto financeiro
    valor_total_consumos: float = Field(0, ge=0, description="Valor total dos consumos")
    valor_total_acerto: float = Field(0, ge=0, description="Valor total do acerto")
    forma_acerto: FormaAcertoEnum = Field(..., description="Forma de acerto dos valores")
    
    # Avaliação do hóspede
    avaliacao_hospede: int = Field(5, ge=1, le=5, description="Avaliação do hóspede (1-5)")
    comentario_hospede: Optional[str] = Field(None, description="Comentário do hóspede")
    
    # Observações finais
    observacoes_checkout: Optional[str] = Field(None, description="Observações do checkout")
    
    # Funcionário responsável
    funcionario_id: int = Field(..., description="ID do funcionário que realizou o checkout")
    assinatura_funcionario: Optional[str] = Field(None, description="Assinatura do funcionário")
    
    @validator('valor_total_acerto')
    def calcular_acerto(cls, v, values):
        total_consumos = (
            values.get('consumo_frigobar', 0) +
            values.get('servicos_extras', 0) +
            values.get('valor_danos', 0) +
            values.get('taxa_late_checkout', 0)
        )
        
        # Adicionar consumos adicionais
        for consumo in values.get('consumos_adicionais', []):
            total_consumos += consumo.get('valor_total', 0)
        
        if abs(v - total_consumos) > 0.01:
            raise ValueError('Valor total do acerto não corresponde à soma dos consumos')
        return v


class CheckinResponse(BaseModel):
    """Response do check-in"""
    success: bool = True
    mensagem: str = "Check-in realizado com sucesso"
    hospedagem_id: int
    data_checkin: datetime
    quarto: dict
    hospedes: List[dict]
    caucao_cobrada: Optional[float] = None
    instrucoes: List[str]


class CheckoutResponse(BaseModel):
    """Response do check-out"""
    success: bool = True
    mensagem: str = "Check-out realizado com sucesso"
    hospedagem_id: int
    data_checkout: datetime
    resumo_financeiro: dict
    comprovante_url: Optional[str] = None
    fidelidade_ganha: Optional[int] = None


class VoucherCreate(BaseModel):
    """Schema para criação de voucher"""
    reserva_id: int = Field(..., description="ID da reserva")
    tipo_voucher: str = Field("CONFIRMACAO", description="Tipo do voucher")
    observacoes: Optional[str] = Field(None, description="Observações")
    emitente_funcionario_id: int = Field(..., description="ID do funcionário emissor")


class VoucherResponse(BaseModel):
    """Response do voucher"""
    id: int
    codigo_voucher: str
    reserva_id: int
    tipo_voucher: str
    status: str
    data_emissao: datetime
    data_validade: Optional[datetime]
    qr_code: Optional[str]
    url_pdf: Optional[str]
    reserva: dict
    cliente: dict
    quarto: dict
    valores: dict
    instrucoes: dict
    emitente: dict
