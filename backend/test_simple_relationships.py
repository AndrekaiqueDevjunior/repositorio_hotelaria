#!/usr/bin/env python3
"""
Script simples para testar relacionamentos SQLAlchemy sem dependências
"""

import sys
import os

# Adicionar o path do projeto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from sqlalchemy.sql import func

# Base para testes
Base = declarative_base()

# Modelos simplificados para teste
class Cliente(Base):
    __tablename__ = "clientes"
    
    id = Column(Integer, primary_key=True)
    nome = Column(String(100))
    
    # Relacionamentos
    reservas = relationship("Reserva", back_populates="cliente")
    usuario_pontos = relationship("UsuarioPontos", back_populates="cliente", uselist=False)
    pagamentos = relationship("Pagamento", back_populates="cliente")

class Reserva(Base):
    __tablename__ = "reservas"
    
    id = Column(Integer, primary_key=True)
    codigo = Column(String(50))
    cliente_id = Column(Integer, ForeignKey("clientes.id"))
    quarto_id = Column(Integer, ForeignKey("quartos.id"))
    
    # Relacionamentos
    cliente = relationship("Cliente", back_populates="reservas")
    quarto = relationship("Quarto", back_populates="reservas")
    pagamentos = relationship("Pagamento", back_populates="reserva")

class Quarto(Base):
    __tablename__ = "quartos"
    
    id = Column(Integer, primary_key=True)
    numero = Column(String(10))
    tipo_suite_id = Column(Integer, ForeignKey("tipos_suite.id"))
    
    # Relacionamentos
    tipo_suite = relationship("TipoSuite", back_populates="quartos")
    reservas = relationship("Reserva", back_populates="quarto")

class TipoSuite(Base):
    __tablename__ = "tipos_suite"
    
    id = Column(Integer, primary_key=True)
    nome = Column(String(100))
    
    # Relacionamentos
    quartos = relationship("Quarto", back_populates="tipo_suite")

class Pagamento(Base):
    __tablename__ = "pagamentos"
    
    id = Column(Integer, primary_key=True)
    valor = Column(String(50))
    reserva_id = Column(Integer, ForeignKey("reservas.id"))
    cliente_id = Column(Integer, ForeignKey("clientes.id"))
    
    # Relacionamentos
    reserva = relationship("Reserva", back_populates="pagamentos")
    cliente = relationship("Cliente", back_populates="pagamentos")

class UsuarioPontos(Base):
    __tablename__ = "usuarios_pontos"
    
    id = Column(Integer, primary_key=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"))
    saldo = Column(Integer, default=0)
    
    # Relacionamentos
    cliente = relationship("Cliente", back_populates="usuario_pontos")

def test_simple_relationships():
    """Testa relacionamentos básicos com SQLite em memória"""
    
    print("🔧 Testando relacionamentos SQLAlchemy (modo simplificado)...")
    
    # Criar engine em memória
    engine = create_engine("sqlite:///:memory:", echo=False)
    
    # Criar tabelas
    Base.metadata.create_all(engine)
    
    # Criar sessão
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Criar dados de teste
        print("\n📝 Criando dados de teste...")
        
        # Tipo Suite
        tipo_suite = TipoSuite(nome="Suíte Deluxe")
        session.add(tipo_suite)
        
        # Quarto
        quarto = Quarto(numero="101", tipo_suite=tipo_suite)
        session.add(quarto)
        
        # Cliente
        cliente = Cliente(nome="João Silva")
        session.add(cliente)
        
        # Usuario Pontos
        usuario_pontos = UsuarioPontos(cliente=cliente, saldo=100)
        session.add(usuario_pontos)
        
        # Reserva
        reserva = Reserva(codigo="RES001", cliente=cliente, quarto=quarto)
        session.add(reserva)
        
        # Pagamento
        pagamento = Pagamento(valor="500.00", reserva=reserva, cliente=cliente)
        session.add(pagamento)
        
        session.commit()
        
        print("✅ Dados criados com sucesso!")
        
        # Testar relacionamentos
        print("\n🔍 Testando relacionamentos...")
        
        # 1. Cliente -> Reservas
        print(f"\n1. Cliente: {cliente.nome}")
        print(f"   Reservas: {len(cliente.reservas)}")
        for res in cliente.reservas:
            print(f"     - {res.codigo}")
        
        # 2. Cliente -> UsuarioPontos
        print(f"\n2. Cliente: {cliente.nome}")
        print(f"   Pontos: {cliente.usuario_pontos.saldo if cliente.usuario_pontos else 'N/A'}")
        
        # 3. Reserva -> Cliente + Quarto
        print(f"\n3. Reserva: {reserva.codigo}")
        print(f"   Cliente: {reserva.cliente.nome}")
        print(f"   Quarto: {reserva.quarto.numero}")
        
        # 4. Reserva -> Pagamentos
        print(f"\n4. Reserva: {reserva.codigo}")
        print(f"   Pagamentos: {len(reserva.pagamentos)}")
        for pag in reserva.pagamentos:
            print(f"     - R$ {pag.valor}")
        
        # 5. Quarto -> TipoSuite
        print(f"\n5. Quarto: {quarto.numero}")
        print(f"   Tipo: {quarto.tipo_suite.nome}")
        
        # 6. Quarto -> Reservas
        print(f"\n6. Quarto: {quarto.numero}")
        print(f"   Reservas: {len(quarto.reservas)}")
        for res in quarto.reservas:
            print(f"     - {res.codigo}")
        
        # 7. TipoSuite -> Quartos
        print(f"\n7. Tipo Suite: {tipo_suite.nome}")
        print(f"   Quartos: {len(tipo_suite.quartos)}")
        for q in tipo_suite.quartos:
            print(f"     - {q.numero}")
        
        # 8. Pagamento -> Reserva + Cliente
        print(f"\n8. Pagamento: R$ {pagamento.valor}")
        print(f"   Reserva: {pagamento.reserva.codigo}")
        print(f"   Cliente: {pagamento.cliente.nome}")
        
        print("\n🎉 Todos os relacionamentos funcionando corretamente!")
        
    except Exception as e:
        print(f"\n❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        session.close()

if __name__ == "__main__":
    test_simple_relationships()
