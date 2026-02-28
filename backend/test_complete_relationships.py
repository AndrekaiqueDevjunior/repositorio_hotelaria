#!/usr/bin/env python3
"""
Teste completo dos relacionamentos SQLAlchemy sem dependências
"""

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Numeric, DateTime, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship, sessionmaker, declarative_base
from sqlalchemy.sql import func
from enum import Enum
import datetime

# Enums
class StatusReserva(Enum):
    PENDENTE = "PENDENTE"
    CONFIRMADA = "CONFIRMADA"
    CANCELADA = "CANCELADA"
    HOSPEDADO = "HOSPEDADO"
    CHECKED_OUT = "CHECKED_OUT"

class MetodoPagamento(Enum):
    DINHEIRO = "DINHEIRO"
    CARTAO = "CARTAO"
    PIX = "PIX"
    TRANSFERENCIA = "TRANSFERENCIA"

class TipoTransacaoPontos(Enum):
    CREDITO = "CREDITO"
    DEBITO = "DEBITO"

class PerfilUsuario(Enum):
    ADMIN = "ADMIN"
    FUNCIONARIO = "FUNCIONARIO"
    RECEPCAO = "RECEPCAO"

class StatusQuarto(Enum):
    ATIVO = "ATIVO"
    MANUTENCAO = "MANUTENCAO"
    INATIVO = "INATIVO"

# Base
Base = declarative_base()

# Modelos
class Usuario(Base):
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True)
    nome = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    perfil = Column(SQLEnum(PerfilUsuario), nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    # Relacionamentos
    reservas_criadas = relationship("Reserva", foreign_keys="Reserva.criado_por_usuario_id")

class Cliente(Base):
    __tablename__ = "clientes"
    
    id = Column(Integer, primary_key=True)
    nome_completo = Column(String(255), nullable=False)
    documento = Column(String(20), nullable=False)
    email = Column(String(255), nullable=True)
    telefone = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=func.now())
    
    # Relacionamentos
    reservas = relationship("Reserva", back_populates="cliente")
    usuario_pontos = relationship("UsuarioPontos", back_populates="cliente", uselist=False)
    pagamentos = relationship("Pagamento", back_populates="cliente")

class TipoSuite(Base):
    __tablename__ = "tipos_suite"
    
    id = Column(Integer, primary_key=True)
    nome = Column(String(100), nullable=False)
    descricao = Column(String(500), nullable=True)
    capacidade = Column(Integer, nullable=False, default=2)
    pontos_por_par = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    # Relacionamentos
    quartos = relationship("Quarto", back_populates="tipo_suite")

class Quarto(Base):
    __tablename__ = "quartos"
    
    id = Column(Integer, primary_key=True)
    numero = Column(String(10), unique=True, nullable=False)
    tipo_suite_id = Column(Integer, ForeignKey("tipos_suite.id"), nullable=False)
    status = Column(SQLEnum(StatusQuarto), default=StatusQuarto.ATIVO)
    created_at = Column(DateTime, default=func.now())
    
    # Relacionamentos
    tipo_suite = relationship("TipoSuite", back_populates="quartos")
    reservas = relationship("Reserva", back_populates="quarto")

class Reserva(Base):
    __tablename__ = "reservas"
    
    id = Column(Integer, primary_key=True)
    codigo_reserva = Column(String(50), unique=True, nullable=False)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    quarto_id = Column(Integer, ForeignKey("quartos.id"), nullable=True)
    status_reserva = Column(SQLEnum(StatusReserva), default=StatusReserva.PENDENTE)
    valor_diaria = Column(Numeric(10, 2), nullable=False)
    num_diarias_previstas = Column(Integer, nullable=False)
    valor_previsto = Column(Numeric(10, 2), nullable=False)
    criado_por_usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    # Relacionamentos
    cliente = relationship("Cliente", back_populates="reservas")
    quarto = relationship("Quarto", back_populates="reservas")
    criado_por = relationship("Usuario", foreign_keys=[criado_por_usuario_id])
    pagamentos = relationship("Pagamento", back_populates="reserva")

class Pagamento(Base):
    __tablename__ = "pagamentos"
    
    id = Column(Integer, primary_key=True)
    reserva_id = Column(Integer, ForeignKey("reservas.id"), nullable=False)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    metodo = Column(SQLEnum(MetodoPagamento), nullable=False)
    valor = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    # Relacionamentos
    reserva = relationship("Reserva", back_populates="pagamentos")
    cliente = relationship("Cliente", back_populates="pagamentos")

class UsuarioPontos(Base):
    __tablename__ = "usuarios_pontos"
    
    id = Column(Integer, primary_key=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False, unique=True)
    saldo_atual = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    # Relacionamentos
    cliente = relationship("Cliente", back_populates="usuario_pontos")
    transacoes = relationship("TransacaoPontos", back_populates="usuario_pontos")

class TransacaoPontos(Base):
    __tablename__ = "transacoes_pontos"
    
    id = Column(Integer, primary_key=True)
    usuario_pontos_id = Column(Integer, ForeignKey("usuarios_pontos.id"), nullable=False)
    tipo = Column(SQLEnum(TipoTransacaoPontos), nullable=False)
    origem = Column(String(100), nullable=False)
    pontos = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    # Relacionamentos
    usuario_pontos = relationship("UsuarioPontos", back_populates="transacoes")

def test_complete_relationships():
    """Teste completo de todos os relacionamentos"""
    
    print('🔧 Teste Completo de Relacionamentos SQLAlchemy')
    print('=' * 50)
    
    # Criar engine
    engine = create_engine("sqlite:///:memory:", echo=False)
    
    # Criar tabelas
    Base.metadata.create_all(engine)
    print('✅ Tabelas criadas')
    
    # Criar sessão
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # === CRIAÇÃO DE DADOS ===
        print('\n📝 Criando dados de teste...')
        
        # 1. Usuario Admin
        admin = Usuario(
            nome="Administrador",
            email="admin@hotel.com",
            senha_hash="hash123",
            perfil=PerfilUsuario.ADMIN
        )
        session.add(admin)
        session.flush()
        
        # 2. Tipo Suite
        suite_deluxe = TipoSuite(
            nome="Suíte Deluxe",
            descricao="Suíte de luxo com vista mar",
            capacidade=2,
            pontos_por_par=50
        )
        session.add(suite_deluxe)
        session.flush()
        
        # 3. Quartos
        quarto_101 = Quarto(numero="101", tipo_suite_id=suite_deluxe.id)
        quarto_102 = Quarto(numero="102", tipo_suite_id=suite_deluxe.id)
        session.add_all([quarto_101, quarto_102])
        session.flush()
        
        # 4. Clientes
        cliente1 = Cliente(
            nome_completo="João Silva",
            documento="123456789",
            email="joao@email.com",
            telefone="119999999"
        )
        cliente2 = Cliente(
            nome_completo="Maria Santos",
            documento="987654321",
            email="maria@email.com",
            telefone="118888888"
        )
        session.add_all([cliente1, cliente2])
        session.flush()
        
        # 5. Sistema de Pontos
        pontos_joao = UsuarioPontos(cliente_id=cliente1.id, saldo_atual=150)
        pontos_maria = UsuarioPontos(cliente_id=cliente2.id, saldo_atual=75)
        session.add_all([pontos_joao, pontos_maria])
        session.flush()
        
        # 6. Reservas
        reserva1 = Reserva(
            codigo_reserva="RES001",
            cliente_id=cliente1.id,
            quarto_id=quarto_101.id,
            status_reserva=StatusReserva.CONFIRMADA,
            valor_diaria=250.00,
            num_diarias_previstas=2,
            valor_previsto=500.00,
            criado_por_usuario_id=admin.id
        )
        reserva2 = Reserva(
            codigo_reserva="RES002",
            cliente_id=cliente2.id,
            quarto_id=quarto_102.id,
            status_reserva=StatusReserva.PENDENTE,
            valor_diaria=300.00,
            num_diarias_previstas=3,
            valor_previsto=900.00,
            criado_por_usuario_id=admin.id
        )
        session.add_all([reserva1, reserva2])
        session.flush()
        
        # 7. Pagamentos
        pag1 = Pagamento(
            reserva_id=reserva1.id,
            cliente_id=cliente1.id,
            metodo=MetodoPagamento.CARTAO,
            valor=500.00
        )
        pag2 = Pagamento(
            reserva_id=reserva2.id,
            cliente_id=cliente2.id,
            metodo=MetodoPagamento.PIX,
            valor=900.00
        )
        session.add_all([pag1, pag2])
        session.flush()
        
        # 8. Transações de Pontos
        trans1 = TransacaoPontos(
            usuario_pontos_id=pontos_joao.id,
            tipo=TipoTransacaoPontos.CREDITO,
            origem="RESERVA",
            pontos=50
        )
        trans2 = TransacaoPontos(
            usuario_pontos_id=pontos_maria.id,
            tipo=TipoTransacaoPontos.CREDITO,
            origem="BONUS",
            pontos=25
        )
        session.add_all([trans1, trans2])
        
        session.commit()
        print('✅ Dados criados com sucesso!')
        
        # === TESTES DE RELACIONAMENTOS ===
        print('\n🔍 Testando Relacionamentos')
        print('=' * 50)
        
        # Teste 1: Cliente -> Reservas
        print('\n1. CLIENTE -> RESERVAS')
        print(f'   Cliente: {cliente1.nome_completo}')
        print(f'   Reservas: {len(cliente1.reservas)}')
        for res in cliente1.reservas:
            print(f'     - {res.codigo_reserva} ({res.status_reserva.value}) - R$ {res.valor_previsto}')
        
        # Teste 2: Cliente -> Pontos
        print('\n2. CLIENTE -> PONTOS')
        print(f'   Cliente: {cliente1.nome_completo}')
        print(f'   Saldo atual: {cliente1.usuario_pontos.saldo_atual} pontos')
        print(f'   Transações: {len(cliente1.usuario_pontos.transacoes)}')
        for trans in cliente1.usuario_pontos.transacoes:
            print(f'     - {trans.pontos} pontos ({trans.tipo.value}) - {trans.origem}')
        
        # Teste 3: Reserva -> Cliente + Quarto
        print('\n3. RESERVA -> CLIENTE + QUARTO')
        print(f'   Reserva: {reserva1.codigo_reserva}')
        print(f'   Cliente: {reserva1.cliente.nome_completo}')
        print(f'   Quarto: {reserva1.quarto.numero}')
        print(f'   Tipo Suite: {reserva1.quarto.tipo_suite.nome}')
        print(f'   Criado por: {reserva1.criado_por.nome}')
        
        # Teste 4: Reserva -> Pagamentos
        print('\n4. RESERVA -> PAGAMENTOS')
        print(f'   Reserva: {reserva1.codigo_reserva}')
        print(f'   Pagamentos: {len(reserva1.pagamentos)}')
        for pag in reserva1.pagamentos:
            print(f'     - R$ {pag.valor} ({pag.metodo.value})')
        
        # Teste 5: Quarto -> TipoSuite + Reservas
        print('\n5. QUARTO -> TIPO SUITE + RESERVAS')
        print(f'   Quarto: {quarto_101.numero}')
        print(f'   Tipo Suite: {quarto_101.tipo_suite.nome}')
        print(f'   Capacidade: {quarto_101.tipo_suite.capacidade} pessoas')
        print(f'   Pontos por par: {quarto_101.tipo_suite.pontos_por_par}')
        print(f'   Reservas no quarto: {len(quarto_101.reservas)}')
        for res in quarto_101.reservas:
            print(f'     - {res.codigo_reserva} ({res.cliente.nome_completo})')
        
        # Teste 6: TipoSuite -> Quartos
        print('\n6. TIPO SUITE -> QUARTOS')
        print(f'   Tipo Suite: {suite_deluxe.nome}')
        print(f'   Quartos: {len(suite_deluxe.quartos)}')
        for q in suite_deluxe.quartos:
            print(f'     - {q.numero} ({len(q.reservas)} reservas)')
        
        # Teste 7: Usuario -> Reservas Criadas
        print('\n7. USUARIO -> RESERVAS CRIADAS')
        print(f'   Usuário: {admin.nome} ({admin.perfil.value})')
        print(f'   Reservas criadas: {len(admin.reservas_criadas)}')
        for res in admin.reservas_criadas:
            print(f'     - {res.codigo_reserva} para {res.cliente.nome_completo}')
        
        # Teste 8: Pagamento -> Reserva + Cliente
        print('\n8. PAGAMENTO -> RESERVA + CLIENTE')
        print(f'   Pagamento: R$ {pag1.valor} ({pag1.metodo.value})')
        print(f'   Reserva: {pag1.reserva.codigo_reserva}')
        print(f'   Cliente: {pag1.cliente.nome_completo}')
        print(f'   Status da reserva: {pag1.reserva.status_reserva.value}')
        
        # Teste 9: Navegação Completa
        print('\n9. NAVEGAÇÃO COMPLETA (Multi-nível)')
        print(f'   Cliente -> Reserva -> Quarto -> Tipo Suite')
        print(f'   {cliente1.nome_completo}')
        print(f'   └─ {reserva1.codigo_reserva}')
        print(f'      └─ Quarto {reserva1.quarto.numero}')
        print(f'         └─ {reserva1.quarto.tipo_suite.nome}')
        
        print(f'   Tipo Suite -> Quartos -> Reservas -> Clientes')
        print(f'   {suite_deluxe.nome}')
        print(f'   └─ {len(suite_deluxe.quartos)} quartos')
        for q in suite_deluxe.quartos:
            print(f'      └─ Quarto {q.numero}: {len(q.reservas)} reservas')
            for res in q.reservas:
                print(f'         └─ {res.codigo_reserva}: {res.cliente.nome_completo}')
        
        # Teste 10: Verificação de Integridade
        print('\n10. VERIFICAÇÃO DE INTEGRIDADE')
        print('   Validando todos os relacionamentos...')
        
        assert cliente1.reservas[0].id == reserva1.id, "Cliente->Reserva falhou"
        assert reserva1.cliente.id == cliente1.id, "Reserva->Cliente falhou"
        assert quarto_101.tipo_suite.id == suite_deluxe.id, "Quarto->TipoSuite falhou"
        assert suite_deluxe.quartos[0].id == quarto_101.id, "TipoSuite->Quartos falhou"
        assert pag1.reserva.id == reserva1.id, "Pagamento->Reserva falhou"
        assert pag1.cliente.id == cliente1.id, "Pagamento->Cliente falhou"
        assert cliente1.usuario_pontos.id == pontos_joao.id, "Cliente->UsuarioPontos falhou"
        assert pontos_joao.cliente.id == cliente1.id, "UsuarioPontos->Cliente falhou"
        assert admin.reservas_criadas[0].id == reserva1.id, "Usuario->ReservasCriadas falhou"
        
        print('   ✅ Todos os relacionamentos intactos!')
        
        # Teste 11: Consultas Complexas
        print('\n11. CONSULTAS COMPLEXAS')
        
        # Todas as reservas com cliente e quarto
        reservas_completas = session.query(Reserva).join(Cliente).join(Quarto).all()
        print(f'   Reservas completas: {len(reservas_completas)}')
        
        # Todos os pagamentos com reserva e cliente
        pagamentos_completos = session.query(Pagamento).join(Reserva).join(Cliente).all()
        print(f'   Pagamentos completos: {len(pagamentos_completos)}')
        
        # Clientes com pontos e transações
        clientes_com_pontos = session.query(Cliente).join(UsuarioPontos).all()
        print(f'   Clientes com pontos: {len(clientes_com_pontos)}')
        
        # Quartos por tipo suite
        quartos_por_tipo = session.query(Quarto).join(TipoSuite).group_by(TipoSuite.id).count()
        print(f'   Quartos agrupados por tipo: {quartos_por_tipo}')
        
        print('\n🎉 TESTE CONCLUÍDO COM SUCESSO!')
        print('📊 Resumo:')
        print(f'   - {session.query(Usuario).count()} usuários')
        print(f'   - {session.query(Cliente).count()} clientes')
        print(f'   - {session.query(TipoSuite).count()} tipos de suíte')
        print(f'   - {session.query(Quarto).count()} quartos')
        print(f'   - {session.query(Reserva).count()} reservas')
        print(f'   - {session.query(Pagamento).count()} pagamentos')
        print(f'   - {session.query(UsuarioPontos).count()} contas de pontos')
        print(f'   - {session.query(TransacaoPontos).count()} transações de pontos')
        
    except Exception as e:
        print(f'\n❌ Erro: {str(e)}')
        import traceback
        traceback.print_exc()
        session.rollback()
        
    finally:
        session.close()

if __name__ == "__main__":
    test_complete_relationships()
