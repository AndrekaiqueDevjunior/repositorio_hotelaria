from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Text, Date, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
from app.core.enums import StatusReserva, OrigemReserva, TipoItemCobranca, StatusFinanceiro, PoliticaCancelamento

class Reserva(Base):
    __tablename__ = "reservas"
    
    id = Column(Integer, primary_key=True, index=True)
    codigo_reserva = Column(String(50), unique=True, nullable=False, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    quarto_id = Column(Integer, ForeignKey("quartos.id"), nullable=True)
    status_reserva = Column(SQLEnum(StatusReserva), default=StatusReserva.PENDENTE)
    status_financeiro = Column(SQLEnum(StatusFinanceiro), default=StatusFinanceiro.AGUARDANDO_PAGAMENTO)
    politica_cancelamento = Column(SQLEnum(PoliticaCancelamento), default=PoliticaCancelamento.FLEXIVEL)
    origem = Column(SQLEnum(OrigemReserva), default=OrigemReserva.BALCAO)
    checkin_previsto = Column(DateTime(timezone=True), nullable=False)
    checkout_previsto = Column(DateTime(timezone=True), nullable=False)
    checkin_real = Column(DateTime(timezone=True), nullable=True)
    checkout_real = Column(DateTime(timezone=True), nullable=True)
    valor_diaria = Column(Numeric(10, 2), nullable=False)
    num_diarias_previstas = Column(Integer, nullable=False)
    valor_previsto = Column(Numeric(10, 2), nullable=False)
    observacoes = Column(Text, nullable=True)
    criado_por_usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    atualizado_por_usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relacionamentos
    cliente = relationship("Cliente", back_populates="reservas")
    quarto = relationship("Quarto", back_populates="reservas")
    criado_por = relationship("Usuario", foreign_keys=[criado_por_usuario_id])
    atualizado_por = relationship("Usuario", foreign_keys=[atualizado_por_usuario_id])
    hospedes_adicionais = relationship("HospedeAdicional", back_populates="reserva", cascade="all, delete-orphan")
    itens_cobranca = relationship("ItemCobranca", back_populates="reserva", cascade="all, delete-orphan")
    pagamentos = relationship("Pagamento", back_populates="reserva")
    transacoes_pontos = relationship("TransacaoPontos", back_populates="reserva")
    checkin_record = relationship("CheckinRecord", back_populates="reserva", uselist=False)
    checkout_record = relationship("CheckoutRecord", back_populates="reserva", uselist=False)

class HospedeAdicional(Base):
    __tablename__ = "hospedes_adicionais"
    
    id = Column(Integer, primary_key=True, index=True)
    reserva_id = Column(Integer, ForeignKey("reservas.id"), nullable=False)
    nome = Column(String(255), nullable=False)
    documento = Column(String(20), nullable=True)
    telefone = Column(String(20), nullable=True)
    data_nascimento = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relacionamento
    reserva = relationship("Reserva", back_populates="hospedes_adicionais")

class ItemCobranca(Base):
    __tablename__ = "itens_cobranca"
    
    id = Column(Integer, primary_key=True, index=True)
    reserva_id = Column(Integer, ForeignKey("reservas.id"), nullable=False)
    tipo = Column(SQLEnum(TipoItemCobranca), default=TipoItemCobranca.DIARIA)
    descricao = Column(String(255), nullable=False)
    quantidade = Column(Integer, default=1)
    valor_unitario = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relacionamento
    reserva = relationship("Reserva", back_populates="itens_cobranca")
