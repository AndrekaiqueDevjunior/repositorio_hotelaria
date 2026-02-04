from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
from app.core.enums import PerfilUsuario

class Notificacao(Base):
    __tablename__ = "notificacoes"
    
    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(255), nullable=False)
    mensagem = Column(Text, nullable=False)
    tipo = Column(SQLEnum("info", "warning", "critical", "success", name="tipo_notificacao"), default="info")
    categoria = Column(SQLEnum("reserva", "pagamento", "sistema", "antifraude", name="categoria_notificacao"), default="sistema")
    perfil = Column(SQLEnum(PerfilUsuario), nullable=True)  # None = todos os perfis
    lida = Column(Boolean, default=False, nullable=False)
    
    # Relacionamentos opcionais
    reserva_id = Column(Integer, ForeignKey("reservas.id"), nullable=True)
    pagamento_id = Column(Integer, ForeignKey("pagamentos.id"), nullable=True)
    usuario_destino_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    usuario_criacao_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    
    # Metadados
    url_acao = Column(String(500), nullable=True)
    dados_adicionais = Column(Text, nullable=True)  # JSON string para dados extras
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    lida_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relacionamentos
    reserva = relationship("Reserva", foreign_keys=[reserva_id])
    pagamento = relationship("Pagamento", foreign_keys=[pagamento_id])
    usuario_destino = relationship("Usuario", foreign_keys=[usuario_destino_id])
    usuario_criacao = relationship("Usuario", foreign_keys=[usuario_criacao_id])
    
    def __repr__(self):
        return f"<Notificacao(id={self.id}, titulo='{self.titulo}', tipo='{self.tipo}', lida={self.lida})>"
