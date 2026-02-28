from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from app.db.base import Base

class Auditoria(Base):
    __tablename__ = "auditorias"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    entidade = Column(String(100), nullable=False, index=True)
    entidade_id = Column(String(50), nullable=False, index=True)
    acao = Column(String(50), nullable=False, index=True)
    payload_resumo = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
