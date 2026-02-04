from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
from app.core.enums import TipoDocumento, StatusCliente

class Cliente(Base):
    __tablename__ = "clientes"
    
    id = Column(Integer, primary_key=True, index=True)
    nome_completo = Column(String(255), nullable=False)
    tipo_documento = Column(SQLEnum(TipoDocumento), default=TipoDocumento.CPF)
    documento = Column(String(20), index=True, nullable=False)
    telefone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    cep = Column(String(10), nullable=True)
    rua = Column(String(255), nullable=True)
    numero = Column(String(10), nullable=True)
    bairro = Column(String(100), nullable=True)
    cidade = Column(String(100), nullable=True)
    estado = Column(String(2), nullable=True)
    observacoes = Column(String(1000), nullable=True)
    status = Column(SQLEnum(StatusCliente), default=StatusCliente.ATIVO)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relacionamentos
    reservas = relationship("Reserva", back_populates="cliente")
    usuario_pontos = relationship("UsuarioPontos", back_populates="cliente", uselist=False)
    pagamentos = relationship("Pagamento", back_populates="cliente")
