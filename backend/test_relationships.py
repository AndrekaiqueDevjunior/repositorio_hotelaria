#!/usr/bin/env python3
"""
Script para testar os relacionamentos do sistema
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, relationship
from app.models import *
from app.core.config import settings
from app.db.base import Base

def test_relationships():
    """Testa todos os relacionamentos do sistema"""
    
    print("🔧 Testando relacionamentos do sistema...")
    
    # Criar engine e sessão
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Criar tabelas (se não existirem)
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Teste 1: Relacionamento Cliente -> Reservas
        print("\n1. Testando Cliente -> Reservas")
        cliente = db.query(Cliente).first()
        if cliente:
            print(f"   Cliente: {cliente.nome_completo}")
            print(f"   Reservas: {len(cliente.reservas)} encontradas")
            for reserva in cliente.reservas[:3]:
                print(f"     - {reserva.codigo_reserva} ({reserva.status_reserva})")
        
        # Teste 2: Relacionamento Reserva -> Cliente
        print("\n2. Testando Reserva -> Cliente")
        reserva = db.query(Reserva).first()
        if reserva:
            print(f"   Reserva: {reserva.codigo_reserva}")
            print(f"   Cliente: {reserva.cliente.nome_completo if reserva.cliente else 'N/A'}")
            print(f"   Quarto: {reserva.quarto.numero if reserva.quarto else 'N/A'}")
        
        # Teste 3: Relacionamento Reserva -> Pagamentos
        print("\n3. Testando Reserva -> Pagamentos")
        if reserva:
            print(f"   Reserva: {reserva.codigo_reserva}")
            print(f"   Pagamentos: {len(reserva.pagamentos)} encontrados")
            for pagamento in reserva.pagamentos:
                print(f"     - R$ {pagamento.valor} ({pagamento.metodo.value})")
        
        # Teste 4: Relacionamento Cliente -> UsuarioPontos
        print("\n4. Testando Cliente -> UsuarioPontos")
        if cliente:
            print(f"   Cliente: {cliente.nome_completo}")
            if cliente.usuario_pontos:
                print(f"   Saldo de pontos: {cliente.usuario_pontos.saldo_atual}")
                print(f"   Transações: {len(cliente.usuario_pontos.transacoes)}")
            else:
                print("   Sem registro de pontos")
        
        # Teste 5: Relacionamento Quarto -> TipoSuite
        print("\n5. Testando Quarto -> TipoSuite")
        quarto = db.query(Quarto).first()
        if quarto:
            print(f"   Quarto: {quarto.numero}")
            print(f"   Tipo Suite: {quarto.tipo_suite.nome if quarto.tipo_suite else 'N/A'}")
            print(f"   Capacidade: {quarto.tipo_suite.capacidade if quarto.tipo_suite else 'N/A'}")
        
        # Teste 6: Relacionamento TipoSuite -> Quartos
        print("\n6. Testando TipoSuite -> Quartos")
        tipo_suite = db.query(TipoSuite).first()
        if tipo_suite:
            print(f"   Tipo Suite: {tipo_suite.nome}")
            print(f"   Quartos: {len(tipo_suite.quartos)} encontrados")
            for quarto in tipo_suite.quartos[:3]:
                print(f"     - {quarto.numero} ({quarto.status.value})")
        
        # Teste 7: Relacionamento Usuario -> Reservas criadas
        print("\n7. Testando Usuario -> Reservas criadas")
        usuario = db.query(Usuario).first()
        if usuario:
            print(f"   Usuário: {usuario.nome}")
            print(f"   Reservas criadas: {len(usuario.reservas_criadas)}")
            print(f"   Perfil: {usuario.perfil.value}")
        
        # Teste 8: Relacionamentos completos de Pagamento
        print("\n8. Testando Pagamento -> Reserva + Cliente")
        pagamento = db.query(Pagamento).first()
        if pagamento:
            print(f"   Pagamento ID: {pagamento.id}")
            print(f"   Valor: R$ {pagamento.valor}")
            print(f"   Reserva: {pagamento.reserva.codigo_reserva if pagamento.reserva else 'N/A'}")
            print(f"   Cliente: {pagamento.cliente.nome_completo if pagamento.cliente else 'N/A'}")
        
        print("\n✅ Todos os relacionamentos testados com sucesso!")
        
    except Exception as e:
        print(f"\n❌ Erro ao testar relacionamentos: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()

if __name__ == "__main__":
    test_relationships()
