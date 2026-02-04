from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
from app.core.enums import TipoTransacaoPontos

class UsuarioPontos(Base):
    __tablename__ = "usuarios_pontos"
    
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False, unique=True)
    saldo_atual = Column(Integer, default=0, nullable=False)
    rp_points = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relacionamentos
    cliente = relationship("Cliente", back_populates="usuario_pontos")
    transacoes = relationship("TransacaoPontos", back_populates="usuario_pontos", cascade="all, delete-orphan")

class TransacaoPontos(Base):
    __tablename__ = "transacoes_pontos"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_pontos_id = Column(Integer, ForeignKey("usuarios_pontos.id"), nullable=False)
    tipo = Column(SQLEnum(TipoTransacaoPontos), nullable=False)
    origem = Column(String(100), nullable=False)
    reserva_id = Column(Integer, ForeignKey("reservas.id"), nullable=True)
    pontos = Column(Integer, nullable=False)
    motivo = Column(String(500), nullable=True)
    criado_por_usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relacionamentos
    usuario_pontos = relationship("UsuarioPontos", back_populates="transacoes")
    reserva = relationship("Reserva", back_populates="transacoes_pontos")
    criado_por = relationship("Usuario")

class Premio(Base):
    __tablename__ = "premios"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=False)
    preco_em_pontos = Column(Integer, nullable=False)  # Mantido para compatibilidade
    preco_em_rp = Column(Integer, nullable=False)  # Novo campo RP
    ativo = Column(Boolean, default=True)
    descricao = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
