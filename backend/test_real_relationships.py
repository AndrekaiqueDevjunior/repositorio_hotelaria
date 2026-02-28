#!/usr/bin/env python3
"""
Script para testar relacionamentos no sistema real
"""

import sys
import os
sys.path.append('/app')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import *
from app.core.config import settings
from app.db.base import Base

def test_real_relationships():
    """Testa relacionamentos no sistema real"""
    
    print('🔧 Testando relacionamentos no sistema real...')
    
    # Criar engine e sessão
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Criar tabelas
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Teste 1: Contagem de registros
        print('\n📊 Contagem de registros:')
        clientes_count = db.query(Cliente).count()
        reservas_count = db.query(Reserva).count()
        quartos_count = db.query(Quarto).count()
        pagamentos_count = db.query(Pagamento).count()
        usuarios_count = db.query(Usuario).count()
        
        print(f'   Clientes: {clientes_count}')
        print(f'   Reservas: {reservas_count}')
        print(f'   Quartos: {quartos_count}')
        print(f'   Pagamentos: {pagamentos_count}')
        print(f'   Usuarios: {usuarios_count}')
        
        # Teste 2: Relacionamento Cliente -> Reservas
        if clientes_count > 0:
            cliente = db.query(Cliente).first()
            print(f'\n👤 Cliente: {cliente.nome_completo}')
            print(f'   Documento: {cliente.documento}')
            print(f'   Reservas: {len(cliente.reservas)}')
            for reserva in cliente.reservas[:3]:
                print(f'     - {reserva.codigo_reserva} ({reserva.status_reserva.value})')
            
            # Teste UsuarioPontos
            if cliente.usuario_pontos:
                print(f'   Pontos: {cliente.usuario_pontos.saldo_atual}')
            else:
                print('   Pontos: Sem registro')
        
        # Teste 3: Relacionamento Reserva -> Cliente + Quarto
        if reservas_count > 0:
            reserva = db.query(Reserva).first()
            print(f'\n🏨 Reserva: {reserva.codigo_reserva}')
            
            if reserva.cliente:
                print(f'   Cliente: {reserva.cliente.nome_completo}')
            else:
                print('   Cliente: N/A')
            
            if reserva.quarto:
                print(f'   Quarto: {reserva.quarto.numero}')
            else:
                print('   Quarto: N/A')
            
            print(f'   Pagamentos: {len(reserva.pagamentos)}')
            print(f'   Valor diária: R$ {reserva.valor_diaria}')
            
            # Teste pagamentos
            for pagamento in reserva.pagamentos[:2]:
                print(f'     Pagamento: R$ {pagamento.valor} ({pagamento.metodo.value})')
        
        # Teste 4: Relacionamento Quarto -> TipoSuite
        if quartos_count > 0:
            quarto = db.query(Quarto).first()
            print(f'\n🚪 Quarto: {quarto.numero}')
            print(f'   Status: {quarto.status.value}')
            
            if quarto.tipo_suite:
                print(f'   Tipo Suite: {quarto.tipo_suite.nome}')
                print(f'   Capacidade: {quarto.tipo_suite.capacidade}')
                print(f'   Pontos por par: {quarto.tipo_suite.pontos_por_par}')
            else:
                print('   Tipo Suite: N/A')
            
            print(f'   Reservas neste quarto: {len(quarto.reservas)}')
        
        # Teste 5: Relacionamento Usuario
        if usuarios_count > 0:
            usuario = db.query(Usuario).first()
            print(f'\n👨‍💼 Usuario: {usuario.nome}')
            print(f'   Email: {usuario.email}')
            print(f'   Perfil: {usuario.perfil.value}')
            print(f'   Reservas criadas: {len(usuario.reservas_criadas)}')
        
        # Teste 6: Relacionamento TipoSuite -> Quartos
        tipo_suites = db.query(TipoSuite).all()
        if tipo_suites:
            print(f'\n🏛️  Tipos de Suite: {len(tipo_suites)}')
            for ts in tipo_suites[:3]:
                print(f'   {ts.nome}: {len(ts.quartos)} quartos')
        
        print('\n✅ Relacionamentos testados com sucesso!')
        
    except Exception as e:
        print(f'\n❌ Erro: {str(e)}')
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()

if __name__ == "__main__":
    test_real_relationships()
