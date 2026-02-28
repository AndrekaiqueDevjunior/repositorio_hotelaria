from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
from app.core.enums import MetodoPagamento, StatusPagamento

class Pagamento(Base):
    __tablename__ = "pagamentos"
    
    id = Column(Integer, primary_key=True, index=True)
    reserva_id = Column(Integer, ForeignKey("reservas.id"), nullable=False)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    metodo = Column(SQLEnum(MetodoPagamento), nullable=False)
    valor = Column(Numeric(10, 2), nullable=False)
    observacao = Column(Text, nullable=True)
    data_pagamento = Column(DateTime(timezone=True), server_default=func.now())
    status_pagamento = Column(SQLEnum(StatusPagamento), default=StatusPagamento.PENDENTE)
    provider = Column(String(50), nullable=True)
    payment_id = Column(String(100), nullable=True)
    raw_response = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relacionamentos
    reserva = relationship("Reserva", back_populates="pagamentos")
    cliente = relationship("Cliente", back_populates="pagamentos")
