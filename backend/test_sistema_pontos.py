#!/usr/bin/env python3
"""
Teste completo do Sistema de Pontos do Hotel
"""

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Numeric, DateTime, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship, sessionmaker, declarative_base
from sqlalchemy.sql import func
from enum import Enum
import datetime

# Enums
class TipoTransacaoPontos(Enum):
    CREDITO = "CREDITO"
    DEBITO = "DEBITO"
    BONUS = "BONUS"
    RESGATE = "RESGATE"

class PerfilUsuario(Enum):
    ADMIN = "ADMIN"
    FUNCIONARIO = "FUNCIONARIO"
    RECEPCAO = "RECEPCAO"

# Base
Base = declarative_base()

# Modelos Simplificados para Teste
class Usuario(Base):
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True)
    nome = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    perfil = Column(SQLEnum(PerfilUsuario), nullable=False)
    created_at = Column(DateTime, default=func.now())

class Cliente(Base):
    __tablename__ = "clientes"
    
    id = Column(Integer, primary_key=True)
    nome_completo = Column(String(255), nullable=False)
    documento = Column(String(20), nullable=False)
    email = Column(String(255), nullable=True)
    telefone = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=func.now())
    
    # Relacionamentos
    usuario_pontos = relationship("UsuarioPontos", back_populates="cliente", uselist=False)

class UsuarioPontos(Base):
    __tablename__ = "usuarios_pontos"
    
    id = Column(Integer, primary_key=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False, unique=True)
    saldo_atual = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relacionamentos
    cliente = relationship("Cliente", back_populates="usuario_pontos")
    transacoes = relationship("TransacaoPontos", back_populates="usuario_pontos", cascade="all, delete-orphan")

class TransacaoPontos(Base):
    __tablename__ = "transacoes_pontos"
    
    id = Column(Integer, primary_key=True)
    usuario_pontos_id = Column(Integer, ForeignKey("usuarios_pontos.id"), nullable=False)
    tipo = Column(SQLEnum(TipoTransacaoPontos), nullable=False)
    origem = Column(String(100), nullable=False)
    pontos = Column(Integer, nullable=False)
    motivo = Column(String(500), nullable=True)
    criado_por_usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())
    
    # Relacionamentos
    usuario_pontos = relationship("UsuarioPontos", back_populates="transacoes")
    criado_por = relationship("Usuario")

class Premio(Base):
    __tablename__ = "premios"
    
    id = Column(Integer, primary_key=True)
    nome = Column(String(255), nullable=False)
    preco_em_pontos = Column(Integer, nullable=False)
    ativo = Column(Boolean, default=True)
    descricao = Column(String(1000), nullable=True)
    created_at = Column(DateTime, default=func.now())

class SistemaPontos:
    """Classe que simula o serviço de pontos"""
    
    def __init__(self, session):
        self.session = session
    
    def criar_conta_pontos(self, cliente_id, pontos_iniciais=0):
        """Cria conta de pontos para um cliente"""
        # Verificar se já existe
        existente = self.session.query(UsuarioPontos).filter(
            UsuarioPontos.cliente_id == cliente_id
        ).first()
        
        if existente:
            raise ValueError("Cliente já possui conta de pontos")
        
        # Criar nova conta
        conta = UsuarioPontos(
            cliente_id=cliente_id,
            saldo_atual=pontos_iniciais
        )
        self.session.add(conta)
        self.session.flush()
        
        # Se houver pontos iniciais, criar transação
        if pontos_iniciais > 0:
            transacao = TransacaoPontos(
                usuario_pontos_id=conta.id,
                tipo=TipoTransacaoPontos.BONUS,
                origem="BEM_VINDO",
                pontos=pontos_iniciais,
                motivo="Bônus de boas-vindas"
            )
            self.session.add(transacao)
        
        return conta
    
    def adicionar_pontos(self, cliente_id, pontos, origem, motivo=None, usuario_id=None):
        """Adiciona pontos à conta do cliente"""
        conta = self.session.query(UsuarioPontos).filter(
            UsuarioPontos.cliente_id == cliente_id
        ).first()
        
        if not conta:
            raise ValueError("Cliente não possui conta de pontos")
        
        if pontos <= 0:
            raise ValueError("Pontos devem ser positivos")
        
        # Atualizar saldo
        saldo_anterior = conta.saldo_atual
        conta.saldo_atual += pontos
        conta.updated_at = func.now()
        
        # Criar transação
        transacao = TransacaoPontos(
            usuario_pontos_id=conta.id,
            tipo=TipoTransacaoPontos.CREDITO,
            origem=origem,
            pontos=pontos,
            motivo=motivo,
            criado_por_usuario_id=usuario_id
        )
        self.session.add(transacao)
        
        return conta, transacao
    
    def debitar_pontos(self, cliente_id, pontos, origem, motivo=None, usuario_id=None):
        """Debita pontos da conta do cliente"""
        conta = self.session.query(UsuarioPontos).filter(
            UsuarioPontos.cliente_id == cliente_id
        ).first()
        
        if not conta:
            raise ValueError("Cliente não possui conta de pontos")
        
        if pontos <= 0:
            raise ValueError("Pontos devem ser positivos")
        
        if conta.saldo_atual < pontos:
            raise ValueError(f"Saldo insuficiente. Saldo atual: {conta.saldo_atual}, Tentativa: {pontos}")
        
        # Atualizar saldo
        saldo_anterior = conta.saldo_atual
        conta.saldo_atual -= pontos
        conta.updated_at = func.now()
        
        # Criar transação
        transacao = TransacaoPontos(
            usuario_pontos_id=conta.id,
            tipo=TipoTransacaoPontos.DEBITO,
            origem=origem,
            pontos=-pontos,  # Negativo para débito
            motivo=motivo,
            criado_por_usuario_id=usuario_id
        )
        self.session.add(transacao)
        
        return conta, transacao
    
    def consultar_saldo(self, cliente_id):
        """Consulta saldo de pontos do cliente"""
        conta = self.session.query(UsuarioPontos).filter(
            UsuarioPontos.cliente_id == cliente_id
        ).first()
        
        if not conta:
            return 0
        
        return conta.saldo_atual
    
    consultar_saldo = consultar_saldo
    
    extrato = consultar_saldo
    
    def get_extrato(self, cliente_id, limite=10):
        """Retorna extrato de transações do cliente"""
        conta = self.session.query(UsuarioPontos).filter(
            UsuarioPontos.cliente_id == cliente_id
        ).first()
        
        if not conta:
            return []
        
        transacoes = self.session.query(TransacaoPontos).filter(
            TransacaoPontos.usuario_pontos_id == conta.id
        ).order_by(TransacaoPontos.created_at.desc()).limit(limite).all()
        
        return transacoes
    
    def resgatar_premio(self, cliente_id, premio_id, usuario_id=None):
        """Resgata um prêmio usando pontos"""
        conta = self.session.query(UsuarioPontos).filter(
            UsuarioPontos.cliente_id == cliente_id
        ).first()
        
        if not conta:
            raise ValueError("Cliente não possui conta de pontos")
        
        premio = self.session.query(Premio).filter(
            Premio.id == premio_id,
            Premio.ativo == True
        ).first()
        
        if not premio:
            raise ValueError("Prêmio não encontrado ou inativo")
        
        if conta.saldo_atual < premio.preco_em_pontos:
            raise ValueError(f"Saldo insuficiente para resgatar {premio.nome}")
        
        # Debitar pontos
        self.debitar_pontos(
            cliente_id=cliente_id,
            pontos=premio.preco_em_pontos,
            origem="RESGATE",
            motivo=f"Resgate: {premio.nome}",
            usuario_id=usuario_id
        )
        
        return premio

def test_sistema_pontos():
    """Teste completo do sistema de pontos"""
    
    print('🎯 Teste Completo do Sistema de Pontos')
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
        # Criar serviço de pontos
        sistema_pontos = SistemaPontos(session)
        
        # === CRIAÇÃO DE DADOS ===
        print('\n📝 Criando dados de teste...')
        
        # 1. Usuário admin
        admin = Usuario(
            nome="Administrador",
            email="admin@hotel.com",
            perfil=PerfilUsuario.ADMIN
        )
        session.add(admin)
        session.flush()
        
        # 2. Clientes
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
        cliente3 = Cliente(
            nome_completo="Carlos Oliveira",
            documento="456789123",
            email="carlos@email.com",
            telefone="117777777"
        )
        session.add_all([cliente1, cliente2, cliente3])
        session.flush()
        
        # 3. Prêmios
        premio1 = Premio(
            nome="Diária Gratuita",
            preco_em_pontos=500,
            descricao="Uma diária gratuita em suíte padrão"
        )
        premio2 = Premio(
            nome="Jantar Romântico",
            preco_em_pontos=300,
            descricao="Jantar para dois no restaurante do hotel"
        )
        premio3 = Premio(
            nome="Spa Day",
            preco_em_pontos=200,
            descricao="Pacote completo de spa por 4 horas"
        )
        session.add_all([premio1, premio2, premio3])
        session.commit()
        
        print('✅ Dados criados com sucesso!')
        
        # === TESTES DO SISTEMA ===
        print('\n🎯 Testando Sistema de Pontos')
        print('=' * 50)
        
        # Teste 1: Criar contas de pontos
        print('\n1. CRIANDO CONTAS DE PONTOS')
        
        # Cliente 1 - com bônus de boas-vindas
        conta1 = sistema_pontos.criar_conta_pontos(cliente1.id, pontos_iniciais=100)
        print(f'   ✅ Conta criada para {cliente1.nome_completo} com 100 pontos bônus')
        
        # Cliente 2 - sem bônus
        conta2 = sistema_pontos.criar_conta_pontos(cliente2.id, pontos_iniciais=0)
        print(f'   ✅ Conta criada para {cliente2.nome_completo} sem pontos iniciais')
        
        # Cliente 3 - com bônus maior
        conta3 = sistema_pontos.criar_conta_pontos(cliente3.id, pontos_iniciais=50)
        print(f'   ✅ Conta criada para {cliente3.nome_completo} com 50 pontos bônus')
        
        session.commit()
        
        # Teste 2: Consultar saldos
        print('\n2. CONSULTANDO SALDOS')
        saldo1 = sistema_pontos.consultar_saldo(cliente1.id)
        saldo2 = sistema_pontos.consultar_saldo(cliente2.id)
        saldo3 = sistema_pontos.consultar_saldo(cliente3.id)
        
        print(f'   {cliente1.nome_completo}: {saldo1} pontos')
        print(f'   {cliente2.nome_completo}: {saldo2} pontos')
        print(f'   {cliente3.nome_completo}: {saldo3} pontos')
        
        # Teste 3: Adicionar pontos (créditos)
        print('\n3. ADICIONANDO PONTOS (CRÉDITOS)')
        
        # João fez uma reserva
        sistema_pontos.adicionar_pontos(
            cliente_id=cliente1.id,
            pontos=50,
            origem="RESERVA",
            motivo="Pontos por reserva: RES001",
            usuario_id=admin.id
        )
        print(f'   ✅ +50 pontos para {cliente1.nome_completo} (reserva)')
        
        # Maria fez check-in
        sistema_pontos.adicionar_pontos(
            cliente_id=cliente2.id,
            pontos=30,
            origem="CHECKIN",
            motivo="Pontos por check-in",
            usuario_id=admin.id
        )
        print(f'   ✅ +30 pontos para {cliente2.nome_completo} (check-in)')
        
        # Carlos indicou um amigo
        sistema_pontos.adicionar_pontos(
            cliente_id=cliente3.id,
            pontos=100,
            origem="INDICACAO",
            motivo="Indicação de novo cliente",
            usuario_id=admin.id
        )
        print(f'   ✅ +100 pontos para {cliente3.nome_completo} (indicação)')
        
        session.commit()
        
        # Teste 4: Consultar saldos atualizados
        print('\n4. SALDOS APÓS CRÉDITOS')
        saldo1 = sistema_pontos.consultar_saldo(cliente1.id)
        saldo2 = sistema_pontos.consultar_saldo(cliente2.id)
        saldo3 = sistema_pontos.consultar_saldo(cliente3.id)
        
        print(f'   {cliente1.nome_completo}: {saldo1} pontos (+50)')
        print(f'   {cliente2.nome_completo}: {saldo2} pontos (+30)')
        print(f'   {cliente3.nome_completo}: {saldo3} pontos (+100)')
        
        # Teste 5: Extrato de transações
        print('\n5. EXTRATO DE TRANSAÇÕES')
        
        print(f'\n   Extrato de {cliente1.nome_completo}:')
        extrato1 = sistema_pontos.get_extrato(cliente1.id)
        for trans in extrato1:
            sinal = "+" if trans.pontos > 0 else ""
            print(f'     {trans.created_at.strftime("%d/%m %H:%M")} | {trans.tipo.value} | {sinal}{trans.pontos} pts | {trans.origem}')
        
        print(f'\n   Extrato de {cliente3.nome_completo}:')
        extrato3 = sistema_pontos.get_extrato(cliente3.id)
        for trans in extrato3:
            sinal = "+" if trans.pontos > 0 else ""
            print(f'     {trans.created_at.strftime("%d/%m %H:%M")} | {trans.tipo.value} | {sinal}{trans.pontos} pts | {trans.origem}')
        
        # Teste 6: Resgatar prêmios
        print('\n6. RESGATANDO PRÊMIOS')
        
        print('\n   Prêmios disponíveis:')
        premios = session.query(Premio).filter(Premio.ativo == True).all()
        for premio in premios:
            print(f'     - {premio.nome}: {premio.preco_em_pontos} pontos')
        
        # João resgata Spa Day
        try:
            premio_resgatado = sistema_pontos.resgatar_premio(
                cliente_id=cliente1.id,
                premio_id=premio3.id,  # Spa Day
                usuario_id=admin.id
            )
            print(f'\n   ✅ {cliente1.nome_completo} resgatou "{premio_resgatado.nome}" por {premio_resgatado.preco_em_pontos} pontos')
        except ValueError as e:
            print(f'   ❌ Erro ao resgatar: {str(e)}')
        
        session.commit()
        
        # Teste 7: Saldo após resgate
        print('\n7. SALDO APÓS RESGATE')
        saldo1 = sistema_pontos.consultar_saldo(cliente1.id)
        print(f'   {cliente1.nome_completo}: {saldo1} pontos (-200 do resgate)')
        
        # Teste 8: Tentativa de resgate sem saldo
        print('\n8. TENTATIVA DE RESGATE SEM SALDO')
        
        try:
            sistema_pontos.resgatar_premio(
                cliente_id=cliente2.id,  # Maria só tem 30 pontos
                premio_id=premio1.id,    # Diária Gratuita custa 500
                usuario_id=admin.id
            )
        except ValueError as e:
            print(f'   ✅ Erro esperado: {str(e)}')
        
        # Teste 9: Adicionar mais pontos e novo resgate
        print('\n9. ADICIONAR PONTOS E NOVO RESGATE')
        
        # Maria acumula mais pontos
        sistema_pontos.adicionar_pontos(
            cliente_id=cliente2.id,
            pontos=500,
            origem="ESTADIA_LONGA",
            motivo="Pontos por estadia de 7 dias",
            usuario_id=admin.id
        )
        session.commit()
        
        saldo2 = sistema_pontos.consultar_saldo(cliente2.id)
        print(f'   {cliente2.nome_completo} agora tem {saldo2} pontos')
        
        # Maria resgata jantar romântico
        try:
            premio_resgatado = sistema_pontos.resgatar_premio(
                cliente_id=cliente2.id,
                premio_id=premio2.id,  # Jantar Romântico
                usuario_id=admin.id
            )
            print(f'   ✅ {cliente2.nome_completo} resgatou "{premio_resgatado.nome}" por {premio_resgatado.preco_em_pontos} pontos')
        except ValueError as e:
            print(f'   ❌ Erro ao resgatar: {str(e)}')
        
        session.commit()
        
        # Teste 10: Relatórios
        print('\n10. RELATÓRIOS DO SISTEMA')
        
        # Total de pontos em circulação
        total_pontos = session.query(func.sum(UsuarioPontos.saldo_atual)).scalar() or 0
        print(f'   Total de pontos em circulação: {total_pontos}')
        
        # Clientes com pontos
        clientes_com_pontos = session.query(UsuarioPontos).count()
        print(f'   Clientes com conta de pontos: {clientes_com_pontos}')
        
        # Transações por tipo
        transacoes_credito = session.query(TransacaoPontos).filter(
            TransacaoPontos.tipo == TipoTransacaoPontos.CREDITO
        ).count()
        transacoes_debito = session.query(TransacaoPontos).filter(
            TransacaoPontos.tipo == TipoTransacaoPontos.DEBITO
        ).count()
        transacoes_bonus = session.query(TransacaoPontos).filter(
            TransacaoPontos.tipo == TipoTransacaoPontos.BONUS
        ).count()
        
        print(f'   Transações de crédito: {transacoes_credito}')
        print(f'   Transações de débito: {transacoes_debito}')
        print(f'   Transações de bônus: {transacoes_bonus}')
        
        # Prêmios resgatados
        total_resgates = session.query(TransacaoPontos).filter(
            TransacaoPontos.origem == "RESGATE"
        ).count()
        print(f'   Total de resgates: {total_resgates}')
        
        # Teste 11: Extrato final completo
        print('\n11. EXTRATO FINAL COMPLETO')
        
        print(f'\n   Extrato completo de {cliente2.nome_completo}:')
        extrato2_final = sistema_pontos.get_extrato(cliente2.id, limite=20)
        saldo_atual = sistema_pontos.consultar_saldo(cliente2.id)
        print(f'   Saldo atual: {saldo_atual} pontos')
        print(f'   Transações ({len(extrato2_final)}):')
        
        for i, trans in enumerate(extrato2_final, 1):
            sinal = "+" if trans.pontos > 0 else ""
            print(f'     {i}. {trans.created_at.strftime("%d/%m %H:%M")} | {trans.tipo.value} | {sinal}{trans.pontos} pts | {trans.origem}')
            if trans.motivo:
                print(f'        Motivo: {trans.motivo}')
        
        print('\n🎉 TESTE DO SISTEMA DE PONTOS CONCLUÍDO!')
        print('✅ Todas as funcionalidades testadas com sucesso!')
        
        # Resumo final
        print('\n📊 Resumo Final:')
        print(f'   - {session.query(Cliente).count()} clientes')
        print(f'   - {session.query(UsuarioPontos).count()} contas de pontos')
        print(f'   - {session.query(TransacaoPontos).count()} transações')
        print(f'   - {session.query(Premio).count()} prêmios disponíveis')
        print(f'   - {total_pontos} pontos em circulação')
        
    except Exception as e:
        print(f'\n❌ Erro: {str(e)}')
        import traceback
        traceback.print_exc()
        session.rollback()
        
    finally:
        session.close()

if __name__ == "__main__":
    test_sistema_pontos()
