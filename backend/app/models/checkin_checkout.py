from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class CheckinRecord(Base):
    """Registro formal de Check-in com todos os dados obrigatórios"""
    __tablename__ = "checkin_records"
    
    id = Column(Integer, primary_key=True, index=True)
    reserva_id = Column(Integer, ForeignKey("reservas.id"), nullable=False)
    
    # Dados do processo
    checkin_datetime = Column(DateTime(timezone=True), nullable=False)
    realizado_por_usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    
    # Dados do hóspede titular
    hospede_titular_nome = Column(String(255), nullable=False)
    hospede_titular_documento = Column(String(50), nullable=False)
    hospede_titular_documento_tipo = Column(String(20), nullable=False)  # RG, CPF, PASSAPORTE
    
    # Validações obrigatórias
    pagamento_validado = Column(Boolean, default=False, nullable=False)
    documentos_conferidos = Column(Boolean, default=False, nullable=False)
    termos_aceitos = Column(Boolean, default=False, nullable=False)
    assinatura_digital = Column(Text, nullable=True)  # Base64 da assinatura
    
    # Dados da hospedagem
    num_hospedes_real = Column(Integer, nullable=False)
    num_criancas = Column(Integer, default=0)
    veiculo_placa = Column(String(20), nullable=True)
    observacoes_checkin = Column(Text, nullable=True)
    
    # Caução (se aplicável)
    caucao_cobrada = Column(Numeric(10, 2), default=0)
    caucao_forma_pagamento = Column(String(50), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relacionamentos
    reserva = relationship("Reserva", back_populates="checkin_record")
    realizado_por = relationship("Usuario", foreign_keys=[realizado_por_usuario_id])
    hospedes_registrados = relationship("HospedeCheckin", back_populates="checkin_record", cascade="all, delete-orphan")


class HospedeCheckin(Base):
    """Registro individual de cada hóspede no check-in"""
    __tablename__ = "hospedes_checkin"
    
    id = Column(Integer, primary_key=True, index=True)
    checkin_record_id = Column(Integer, ForeignKey("checkin_records.id"), nullable=False)
    
    # Dados pessoais
    nome_completo = Column(String(255), nullable=False)
    documento = Column(String(50), nullable=False)
    documento_tipo = Column(String(20), nullable=False)
    nacionalidade = Column(String(100), default="Brasil")
    data_nascimento = Column(DateTime, nullable=True)
    telefone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    
    # Para menores de idade
    e_menor = Column(Boolean, default=False)
    responsavel_nome = Column(String(255), nullable=True)
    responsavel_documento = Column(String(50), nullable=True)
    
    # Relacionamento
    checkin_record = relationship("CheckinRecord", back_populates="hospedes_registrados")


class CheckoutRecord(Base):
    """Registro formal de Check-out com vistoria e acertos financeiros"""
    __tablename__ = "checkout_records"
    
    id = Column(Integer, primary_key=True, index=True)
    reserva_id = Column(Integer, ForeignKey("reservas.id"), nullable=False)
    checkin_record_id = Column(Integer, ForeignKey("checkin_records.id"), nullable=False)
    
    # Dados do processo
    checkout_datetime = Column(DateTime(timezone=True), nullable=False)
    realizado_por_usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    
    # Vistoria do quarto
    vistoria_ok = Column(Boolean, default=True)
    danos_encontrados = Column(Text, nullable=True)
    valor_danos = Column(Numeric(10, 2), default=0)
    
    # Consumos finais
    consumo_frigobar = Column(Numeric(10, 2), default=0)
    servicos_extras = Column(Numeric(10, 2), default=0)
    taxa_late_checkout = Column(Numeric(10, 2), default=0)
    
    # Caução
    caucao_devolvida = Column(Numeric(10, 2), default=0)
    caucao_retida = Column(Numeric(10, 2), default=0)
    motivo_retencao = Column(Text, nullable=True)
    
    # Satisfação
    avaliacao_hospede = Column(Integer, default=5)  # 1-5
    comentario_hospede = Column(Text, nullable=True)
    
    # Acerto financeiro final
    valor_total_final = Column(Numeric(10, 2), nullable=False)
    saldo_devedor = Column(Numeric(10, 2), default=0)
    saldo_credor = Column(Numeric(10, 2), default=0)
    forma_acerto = Column(String(50), nullable=True)
    
    observacoes_checkout = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relacionamentos
    reserva = relationship("Reserva", back_populates="checkout_record")
    checkin_record = relationship("CheckinRecord", back_populates="checkout_record")
    realizado_por = relationship("Usuario", foreign_keys=[realizado_por_usuario_id])


# Adicionando relacionamentos aos modelos existentes
# Isso será feito via migration, mas documentando aqui:
"""
Em Reserva:
    checkin_record = relationship("CheckinRecord", back_populates="reserva", uselist=False)
    checkout_record = relationship("CheckoutRecord", back_populates="reserva", uselist=False)

Em CheckinRecord:
    checkout_record = relationship("CheckoutRecord", back_populates="checkin_record", uselist=False)
"""
