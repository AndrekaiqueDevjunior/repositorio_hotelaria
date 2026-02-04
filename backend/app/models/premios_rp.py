"""
Modelos de Prêmios RP (Reais Pontos)
Implementa o catálogo de prêmios específicos do Hotel Real Cabo Frio
"""

from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
from app.db.base import Base
from app.core.enums import CategoriaPremio

class PremioRP(Base):
    """
    Modelo de prêmios disponíveis para resgate com pontos RP
    """
    __tablename__ = "premios_rp"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=False, index=True)
    descricao = Column(Text, nullable=True)
    categoria = Column(SQLEnum(CategoriaPremio), nullable=False, index=True)
    preco_em_rp = Column(Integer, nullable=False)  # Custo em pontos RP
    imagem_url = Column(String(500), nullable=True)
    ativo = Column(Boolean, default=True, index=True)
    estoque = Column(Integer, default=0)  # Quantidade disponível
    valor_estimado = Column(Integer, nullable=True)  # Valor em reais (para referência)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<PremioRP(id={self.id}, nome='{self.nome}', pontos={self.preco_em_rp})>"

class ResgatePremio(Base):
    """
    Modelo para registrar resgates de prêmios
    """
    __tablename__ = "resgates_premios"
    
    id = Column(Integer, primary_key=True, index=True)
    premio_id = Column(Integer, nullable=False, index=True)
    cliente_id = Column(Integer, nullable=False, index=True)
    pontos_utilizados = Column(Integer, nullable=False)
    status_resgate = Column(String(50), default="PENDENTE")  # PENDENTE, APROVADO, ENTREGUE, CANCELADO
    data_solicitacao = Column(DateTime(timezone=True), server_default=func.now())
    data_aprovacao = Column(DateTime(timezone=True), nullable=True)
    data_entrega = Column(DateTime(timezone=True), nullable=True)
    observacoes = Column(Text, nullable=True)
    criado_por_usuario_id = Column(Integer, nullable=True)
    
    def __repr__(self):
        return f"<ResgatePremio(id={self.id}, premio_id={self.premio_id}, cliente_id={self.cliente_id})>"
