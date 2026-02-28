from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
from app.core.enums import PerfilUsuario, StatusUsuario

class Usuario(Base):
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    documento = Column(String(20), nullable=True)
    telefone = Column(String(20), nullable=True)
    senha_hash = Column(String(255), nullable=False)
    perfil = Column(SQLEnum(PerfilUsuario), nullable=False)
    status = Column(SQLEnum(StatusUsuario), default=StatusUsuario.ATIVO)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relacionamentos
    reservas_criadas = relationship("Reserva", foreign_keys="Reserva.criado_por_usuario_id")
    reservas_atualizadas = relationship("Reserva", foreign_keys="Reserva.atualizado_por_usuario_id")
    transacoes_pontos_criadas = relationship("TransacaoPontos", foreign_keys="TransacaoPontos.criado_por_usuario_id")
