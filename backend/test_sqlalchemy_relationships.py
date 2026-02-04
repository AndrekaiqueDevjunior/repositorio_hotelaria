#!/usr/bin/env python3
"""
Script para testar relacionamentos SQLAlchemy sem dependências externas
"""

import sys
import os
sys.path.append('/app')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

def test_sqlalchemy_relationships():
    """Testa relacionamentos SQLAlchemy com SQLite em memória"""
    
    print('🔧 Testando relacionamentos SQLAlchemy (SQLite)...')
    
    # Criar engine em memória
    engine = create_engine("sqlite:///:memory:", echo=False)
    
    # Importar modelos
    from app.models.usuario import Usuario
    from app.models.cliente import Cliente
    from app.models.hotel import TipoSuite, Quarto
    from app.models.reserva import Reserva
    from app.models.pagamento import Pagamento
    from app.models.pontos import UsuarioPontos, TransacaoPontos
    from app.db.base import Base
    
    # Criar tabelas
    Base.metadata.create_all(engine)
    
    print('✅ Tabelas criadas com sucesso!')
    
    # Criar sessão
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Inserir dados de teste
        print('\n📝 Inserindo dados de teste...')
        
        # 1. Usuario
        usuario = Usuario(
            nome="Admin Test",
            email="admin@test.com",
            senha_hash="hash123",
            perfil="ADMIN"
        )
        session.add(usuario)
        session.flush()  # Obter ID sem commit
        
        # 2. Tipo Suite
        tipo_suite = TipoSuite(
            nome="Suíte Deluxe",
            descricao="Suíte de luxo",
            capacidade=2,
            pontos_por_par=50
        )
        session.add(tipo_suite)
        session.flush()
        
        # 3. Quarto
        quarto = Quarto(
            numero="101",
            tipo_suite_id=tipo_suite.id
        )
        session.add(quarto)
        session.flush()
        
        # 4. Cliente
        cliente = Cliente(
            nome_completo="João Silva",
            documento="123456789",
            email="joao@test.com",
            telefone="119999999"
        )
        session.add(cliente)
        session.flush()
        
        # 5. UsuarioPontos
        usuario_pontos = UsuarioPontos(
            cliente_id=cliente.id,
            saldo_atual=100
        )
        session.add(usuario_pontos)
        session.flush()
        
        # 6. Reserva
        reserva = Reserva(
            codigo_reserva="RES001",
            cliente_id=cliente.id,
            quarto_id=quarto.id,
            valor_diaria=250.00,
            num_diarias_previstas=2,
            valor_previsto=500.00,
            criado_por_usuario_id=usuario.id
        )
        session.add(reserva)
        session.flush()
        
        # 7. Pagamento
        pagamento = Pagamento(
            reserva_id=reserva.id,
            cliente_id=cliente.id,
            valor=500.00,
            metodo="CARTAO"
        )
        session.add(pagamento)
        session.flush()
        
        # 8. TransacaoPontos
        transacao = TransacaoPontos(
            usuario_pontos_id=usuario_pontos.id,
            tipo="CREDITO",
            origem="RESERVA",
            pontos=50,
            reserva_id=reserva.id,
            criado_por_usuario_id=usuario.id
        )
        session.add(transacao)
        
        session.commit()
        print('✅ Dados inseridos com sucesso!')
        
        # Testar relacionamentos
        print('\n🔍 Testando relacionamentos...')
        
        # 1. Cliente -> Reservas
        print(f'\n👤 Cliente: {cliente.nome_completo}')
        print(f'   Reservas: {len(cliente.reservas)}')
        for res in cliente.reservas:
            print(f'     - {res.codigo_reserva} ({res.status_reserva.value})')
        
        # 2. Cliente -> UsuarioPontos
        print(f'\n💰 Pontos do cliente: {cliente.usuario_pontos.saldo_atual if cliente.usuario_pontos else 0}')
        
        # 3. Reserva -> Cliente + Quarto
        print(f'\n🏨 Reserva: {reserva.codigo_reserva}')
        print(f'   Cliente: {reserva.cliente.nome_completo}')
        print(f'   Quarto: {reserva.quarto.numero}')
        print(f'   Pagamentos: {len(reserva.pagamentos)}')
        
        # 4. Reserva -> Pagamentos
        for pag in reserva.pagamentos:
            print(f'     Pagamento: R$ {pag.valor} ({pag.metodo.value})')
        
        # 5. Quarto -> TipoSuite
        print(f'\n🚪 Quarto: {quarto.numero}')
        print(f'   Tipo Suite: {quarto.tipo_suite.nome}')
        print(f'   Capacidade: {quarto.tipo_suite.capacidade}')
        print(f'   Reservas neste quarto: {len(quarto.reservas)}')
        
        # 6. TipoSuite -> Quartos
        print(f'\n🏛️  Tipo Suite: {tipo_suite.nome}')
        print(f'   Quartos: {len(tipo_suite.quartos)}')
        for q in tipo_suite.quartos:
            print(f'     - {q.numero}')
        
        # 7. Usuario -> Reservas criadas
        print(f'\n👨‍💼 Usuario: {usuario.nome}')
        print(f'   Reservas criadas: {len(usuario.reservas_criadas)}')
        for res in usuario.reservas_criadas:
            print(f'     - {res.codigo_reserva}')
        
        # 8. UsuarioPontos -> Transacoes
        print(f'\n🎯 Transações de pontos:')
        print(f'   Total: {len(usuario_pontos.transacoes)}')
        for trans in usuario_pontos.transacoes:
            print(f'     {trans.pontos} pontos ({trans.tipo.value}) - {trans.origem}')
        
        # 9. Pagamento -> Reserva + Cliente
        print(f'\n💳 Pagamento: R$ {pagamento.valor}')
        print(f'   Reserva: {pagamento.reserva.codigo_reserva}')
        print(f'   Cliente: {pagamento.cliente.nome_completo}')
        
        # 10. Navegação inversa
        print(f'\n🔄 Navegação inversa:')
        print(f'   Cliente do pagamento: {pagamento.cliente.nome_completo}')
        print(f'   Reserva do pagamento: {pagamento.reserva.codigo_reserva}')
        print(f'   Cliente da reserva: {reserva.cliente.nome_completo}')
        print(f'   Quarto da reserva: {reserva.quarto.numero}')
        print(f'   Tipo do quarto: {reserva.quarto.tipo_suite.nome}')
        
        print('\n🎉 Todos os relacionamentos SQLAlchemy funcionando perfeitamente!')
        
        # Verificar integridade
        print('\n🔒 Verificando integridade dos relacionamentos:')
        
        assert cliente.reservas[0].id == reserva.id, "Relacionamento Cliente->Reserva falhou"
        assert reserva.cliente.id == cliente.id, "Relacionamento Reserva->Cliente falhou"
        assert quarto.tipo_suite.id == tipo_suite.id, "Relacionamento Quarto->TipoSuite falhou"
        assert tipo_suite.quartos[0].id == quarto.id, "Relacionamento TipoSuite->Quartos falhou"
        assert pagamento.reserva.id == reserva.id, "Relacionamento Pagamento->Reserva falhou"
        assert pagamento.cliente.id == cliente.id, "Relacionamento Pagamento->Cliente falhou"
        assert cliente.usuario_pontos.id == usuario_pontos.id, "Relacionamento Cliente->UsuarioPontos falhou"
        assert usuario_pontos.cliente.id == cliente.id, "Relacionamento UsuarioPontos->Cliente falhou"
        
        print('✅ Integridade verificada com sucesso!')
        
    except Exception as e:
        print(f'\n❌ Erro: {str(e)}')
        import traceback
        traceback.print_exc()
        session.rollback()
        
    finally:
        session.close()

if __name__ == "__main__":
    test_sqlalchemy_relationships()
