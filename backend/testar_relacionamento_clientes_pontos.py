#!/usr/bin/env python3
"""
Testa o relacionamento completo entre clientes e pontos usando SQLAlchemy
"""

import sys
import os
sys.path.append('/app')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.cliente import Cliente
from app.models.pontos import UsuarioPontos, TransacaoPontos, Premio
from app.models.usuario import Usuario
from app.core.enums import TipoTransacaoPontos, PerfilUsuario
from datetime import datetime

def testar_relacionamento_clientes_pontos():
    """Testa o relacionamento completo entre clientes e pontos"""
    
    print('🔗 TESTANDO RELACIONAMENTO CLIENTES ↔ PONTOS')
    print('=' * 60)
    
    # Conectar ao banco de dados
    engine = create_engine("postgresql://postgres:postgres@postgres/hotel_cabo_frio")
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        # 1. Criar usuário admin
        print('\n👤 Criando Usuário Admin...')
        admin = Usuario(
            nome="Admin Teste",
            email="admin@teste.com",
            senha_hash="hash123",
            perfil=PerfilUsuario.ADMIN,
            status="ATIVO"
        )
        session.add(admin)
        session.commit()
        print(f'   ✅ Admin criado: ID {admin.id}')
        
        # 2. Criar cliente
        print('\n🧑 Criando Cliente...')
        cliente = Cliente(
            nome_completo="João Pontos RP",
            documento="123456789",
            email="joao@pontos.com",
            telefone="119999999"
        )
        session.add(cliente)
        session.commit()
        print(f'   ✅ Cliente criado: ID {cliente.id}')
        
        # 3. Criar conta de pontos para o cliente
        print('\n💰 Criando Conta de Pontos...')
        usuario_pontos = UsuarioPontos(
            cliente_id=cliente.id,
            saldo_atual=0,  # Sistema legacy
            rp_points=0     # Novo sistema RP
        )
        session.add(usuario_pontos)
        session.commit()
        print(f'   ✅ Conta de pontos criada: ID {usuario_pontos.id}')
        
        # 4. Testar relacionamento Cliente → UsuarioPontos
        print('\n🔍 Testando Relacionamento Cliente → Pontos...')
        
        # Recarregar cliente com relacionamento
        session.refresh(cliente)
        
        print(f'   📋 Cliente: {cliente.nome_completo}')
        print(f'   💰 Conta de pontos ID: {cliente.usuario_pontos.id}')
        print(f'   💎 Saldo RP: {cliente.usuario_pontos.rp_points}')
        print(f'   📊 Saldo Legacy: {cliente.usuario_pontos.saldo_atual}')
        
        # 5. Adicionar transações de pontos
        print('\n📝 Adicionando Transações de Pontos...')
        
        transacoes = [
            TransacaoPontos(
                usuario_pontos_id=usuario_pontos.id,
                tipo=TipoTransacaoPontos.CREDITO,
                origem="RESERVA",
                pontos=3,
                motivo="Suíte Luxo - 2 diárias",
                criado_por_usuario_id=admin.id
            ),
            TransacaoPontos(
                usuario_pontos_id=usuario_pontos.id,
                tipo=TipoTransacaoPontos.CREDITO,
                origem="CHECKIN",
                pontos=1,
                motivo="Bônus de check-in",
                criado_por_usuario_id=admin.id
            )
        ]
        
        for transacao in transacoes:
            session.add(transacao)
        
        session.commit()
        print(f'   ✅ {len(transacoes)} transações adicionadas')
        
        # 6. Atualizar saldo RP
        print('\n💸 Atualizando Saldo RP...')
        total_rp = sum(t.pontos for t in transacoes)
        usuario_pontos.rp_points = total_rp
        session.commit()
        
        print(f'   💰 Saldo RP atualizado: {usuario_pontos.rp_points}')
        
        # 7. Testar relacionamento inverso UsuarioPontos → Cliente
        print('\n🔍 Testando Relacionamento Pontos → Cliente...')
        
        session.refresh(usuario_pontos)
        print(f'   🧑 Cliente via pontos: {usuario_pontos.cliente.nome_completo}')
        print(f'   📋 Cliente ID: {usuario_pontos.cliente.id}')
        
        # 8. Testar relacionamento com transações
        print('\n🔍 Testando Relacionamento Pontos → Transações...')
        
        transacoes_do_cliente = usuario_pontos.transacoes
        print(f'   📊 Total de transações: {len(transacoes_do_cliente)}')
        
        for transacao in transacoes_do_cliente:
            print(f'   📝 {transacao.tipo}: +{transacao.pontos} RP ({transacao.origem})')
        
        # 9. Testar prêmios
        print('\n🏆 Testando Prêmios...')
        
        premios = session.query(Premio).filter(Premio.ativo == True).all()
        print(f'   🎁 Prêmios disponíveis: {len(premios)}')
        
        for premio in premios:
            pode_resgatar = usuario_pontos.rp_points >= premio.preco_em_pontos
            status = "✅" if pode_resgatar else "❌"
            print(f'   {status} {premio.nome}: {premio.preco_em_pontos} RP')
        
        # 10. Testar navegação completa
        print('\n🔍 Testando Navegação Completa...')
        
        # Cliente → Pontos → Transações
        print(f'   🧑 Cliente: {cliente.nome_completo}')
        print(f'      💰 Pontos RP: {cliente.usuario_pontos.rp_points}')
        print(f'      📊 Transações: {len(cliente.usuario_pontos.transacoes)}')
        
        for trans in cliente.usuario_pontos.transacoes:
            print(f'         📝 {trans.tipo}: {trans.pontos} RP - {trans.motivo}')
        
        print('\n✅ RELACIONAMENTO CLIENTES ↔ PONTOS FUNCIONANDO PERFEITAMENTE!')
        print('🔗 Todos os relacionamentos bidirecionais operacionais')
        print('💎 Sistema RP integrado com modelo Cliente')
        
    except Exception as e:
        print(f'\n❌ Erro: {str(e)}')
        import traceback
        traceback.print_exc()
        session.rollback()
        
    finally:
        session.close()

if __name__ == "__main__":
    testar_relacionamento_clientes_pontos()
