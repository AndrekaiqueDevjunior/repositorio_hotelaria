from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, Enum as SQLEnum
from sqlalchemy.sql import func
from app.db.base import Base
from app.core.enums import StatusAntifraude

class AntifraudeOperacao(Base):
    __tablename__ = "antifraude_operacoes"
    
    id = Column(Integer, primary_key=True, index=True)
    reserva_id = Column(Integer, ForeignKey("reservas.id"), nullable=False)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    cpf_hospede = Column(String(14), nullable=False, index=True)
    pontos_calculados = Column(Integer, nullable=False)
    operacao_id = Column(String(100), unique=True, nullable=False, index=True)
    status = Column(SQLEnum(StatusAntifraude), default=StatusAntifraude.PENDENTE)
    risk_score = Column(Integer, default=0)
    risk_flags = Column(JSON, nullable=True)
    motivo_recusa = Column(Text, nullable=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
