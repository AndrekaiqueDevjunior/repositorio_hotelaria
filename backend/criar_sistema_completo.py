# Salve como: criar_sistema_completo.py
# Execute com: python criar_sistema_completo.py

from pathlib import Path
import json

def criar_sistema_completo():
    base_dir = Path.cwd()
    
    print("🚀 Criando sistema completo Hotel Real Cabo Frio...")
    print("="*60)
    
    # 1. CRIAR TODOS OS MODELOS
    modelos = {
        "app/models/__init__.py": """from .usuario import Usuario
from .cliente import Cliente
from .hotel import TipoSuite, Quarto
from .reserva import Reserva, HospedeAdicional, ItemCobranca
from .pagamento import Pagamento
from .pontos import UsuarioPontos, TransacaoPontos, Premio
from .antifraude import AntifraudeOperacao
from .auditoria import Auditoria

__all__ = [
    "Usuario", "Cliente", "TipoSuite", "Quarto", 
    "Reserva", "HospedeAdicional", "ItemCobranca",
    "Pagamento", "UsuarioPontos", "TransacaoPontos", 
    "Premio", "AntifraudeOperacao", "Auditoria"
]
""",

        "app/models/usuario.py": """from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum
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
""",

        "app/models/cliente.py": """from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum
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
""",

        "app/models/hotel.py": """from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum
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

class Quarto(Base):
    __tablename__ = "quartos"
    
    id = Column(Integer, primary_key=True, index=True)
    numero = Column(String(10), unique=True, nullable=False, index=True)
    tipo_suite_id = Column(Integer, ForeignKey("tipos_suite.id"), nullable=False)
    status = Column(SQLEnum(StatusQuarto), default=StatusQuarto.ATIVO)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
""",

        "app/models/reserva.py": """from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Text, Date, Enum as SQLEnum
from sqlalchemy.sql import func
from app.db.base import Base
from app.core.enums import StatusReserva, OrigemReserva, TipoItemCobranca

class Reserva(Base):
    __tablename__ = "reservas"
    
    id = Column(Integer, primary_key=True, index=True)
    codigo_reserva = Column(String(50), unique=True, nullable=False, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    quarto_id = Column(Integer, ForeignKey("quartos.id"), nullable=True)
    status_reserva = Column(SQLEnum(StatusReserva), default=StatusReserva.PENDENTE)
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

class HospedeAdicional(Base):
    __tablename__ = "hospedes_adicionais"
    
    id = Column(Integer, primary_key=True, index=True)
    reserva_id = Column(Integer, ForeignKey("reservas.id"), nullable=False)
    nome = Column(String(255), nullable=False)
    documento = Column(String(20), nullable=True)
    telefone = Column(String(20), nullable=True)
    data_nascimento = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ItemCobranca(Base):
    __tablename__ = "itens_cobranca"
    
    id = Column(Integer, primary_key=True, index=True)
    reserva_id = Column(Integer, ForeignKey("reservas.id"), nullable=False)
    tipo = Column(SQLEnum(TipoItemCobranca), default=TipoItemCobranca.CONSUMO)
    descricao = Column(String(255), nullable=False)
    quantidade = Column(Integer, default=1)
    valor_unitario = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
""",

        "app/models/pagamento.py": """from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Text, Enum as SQLEnum
from sqlalchemy.sql import func
from app.db.base import Base
from app.core.enums import MetodoPagamento, StatusPagamento

class Pagamento(Base):
    __tablename__ = "pagamentos"
    
    id = Column(Integer, primary_key=True, index=True)
    reserva_id = Column(Integer, ForeignKey("reservas.id"), nullable=False)
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
""",

        "app/models/pontos.py": """from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, Enum as SQLEnum
from sqlalchemy.sql import func
from app.db.base import Base
from app.core.enums import TipoTransacaoPontos

class UsuarioPontos(Base):
    __tablename__ = "usuarios_pontos"
    
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False, unique=True)
    saldo_atual = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

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

class Premio(Base):
    __tablename__ = "premios"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=False)
    preco_em_rp = Column(Integer, nullable=False)
    ativo = Column(Boolean, default=True)
    descricao = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
""",

        "app/models/antifraude.py": """from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, Enum as SQLEnum
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
""",

        "app/models/auditoria.py": """from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
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
""",
    }
    
    # Criar modelos
    for filepath, content in modelos.items():
        full_path = base_dir / filepath
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Criado: {filepath}")
    
    print("\n✨ Sistema completo criado com sucesso!")
    print("\n📋 Próximos passos:")
    print("1. Criar as tabelas no banco: alembic upgrade head")
    print("2. Testar a API: http://localhost:8000/docs")

if __name__ == "__main__":
    criar_sistema_completo()