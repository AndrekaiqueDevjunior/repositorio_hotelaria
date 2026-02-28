"""
Sistema de Comprovação de Pagamentos

Fluxo completo para validar comprovantes de pagamento:
1. Upload do comprovante
2. Análise pelo administrador
3. Aprovação/Rejeição
4. Auditoria completa
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from enum import Enum

class TipoComprovante(str, Enum):
    PIX = "PIX"
    TRANSFERENCIA = "TRANSFERENCIA"
    DINHEIRO = "DINHEIRO"
    BOLETO = "BOLETO"
    CARTAO = "CARTAO"
    OUTRO = "OUTRO"

class StatusValidacao(str, Enum):
    AGUARDANDO_COMPROVANTE = "AGUARDANDO_COMPROVANTE"
    EM_ANALISE = "EM_ANALISE"
    APROVADO = "APROVADO"
    RECUSADO = "RECUSADO"
    CANCELADO = "CANCELADO"

class ComprovanteUpload(BaseModel):
    pagamento_id: int
    tipo_comprovante: TipoComprovante
    arquivo_base64: str
    nome_arquivo: str
    observacoes: Optional[str] = None
    valor_confirmado: Optional[float] = None

class ValidacaoPagamento(BaseModel):
    pagamento_id: int
    status: StatusValidacao
    motivo: Optional[str] = None
    usuario_validador_id: int
    observacoes_internas: Optional[str] = None

class ComprovanteResponse(BaseModel):
    id: int
    pagamento_id: int
    tipo_comprovante: TipoComprovante
    nome_arquivo: str
    url_arquivo: str
    observacoes: Optional[str]
    valor_confirmado: Optional[float]
    status_validacao: StatusValidacao
    data_upload: datetime
    data_validacao: Optional[datetime]
    validador_id: Optional[int]
    motivo_recusa: Optional[str]

# Schema para dashboard de validação
class DashboardValidacao(BaseModel):
    aguardando_comprovante: List[ComprovanteResponse]
    em_analise: List[ComprovanteResponse]
    aprovados_hoje: List[ComprovanteResponse]
    recusados_hoje: List[ComprovanteResponse]
    estatisticas: Dict[str, Any]
