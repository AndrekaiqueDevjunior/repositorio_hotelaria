from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
from app.core.enums import StatusQuarto

class TipoSuite(Base):
    __tablename__ = "tipos_suite"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    descricao = Column(String(500), nullable=True)
    capacidade = Column(Integer, nullable=False, default=2)
    pontos_por_par = Column(Integer, nullable=False)
    ativo = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relacionamentos
    quartos = relationship("Quarto", back_populates="tipo_suite")

class Quarto(Base):
    __tablename__ = "quartos"
    
    id = Column(Integer, primary_key=True, index=True)
    numero = Column(String(10), unique=True, nullable=False, index=True)
    tipo_suite_id = Column(Integer, ForeignKey("tipos_suite.id"), nullable=False)
    status = Column(SQLEnum(StatusQuarto), default=StatusQuarto.ATIVO)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relacionamentos
    tipo_suite = relationship("TipoSuite", back_populates="quartos")
    reservas = relationship("Reserva", back_populates="quarto")
