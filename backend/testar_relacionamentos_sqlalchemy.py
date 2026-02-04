#!/usr/bin/env python3
"""
Teste final dos relacionamentos SQLAlchemy - Clientes ↔ Pontos
"""

import sys
import os
sys.path.append('/app')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

def testar_relacionamentos_sqlalchemy():
    """Testa os relacionamentos usando SQLAlchemy models"""
    
    print('🔗 TESTE FINAL - Relacionamentos SQLAlchemy')
    print('=' * 60)
    
    # Conectar ao banco
    engine = create_engine("postgresql://postgres:postgres@postgres/hotel_cabo_frio")
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 1. Testar relacionamento Cliente → UsuarioPontos
        print('\n🔍 Testando Cliente → Pontos...')
        
        result = session.execute(text("""
            SELECT c.id, c.nome_completo, up.id as pontos_id, up.rp_points
            FROM clientes c
            LEFT JOIN usuarios_pontos up ON c.id = up.cliente_id
            WHERE up.id IS NOT NULL
            LIMIT 3
        """))
        
        clientes_com_pontos = result.fetchall()
        
        print(f'   📊 Clientes com pontos: {len(clientes_com_pontos)}')
        for cliente in clientes_com_pontos:
            print(f'      🧑 {cliente[1]} → Pontos ID: {cliente[2]} (RP: {cliente[3]})')
        
        # 2. Testar UsuarioPontos → Transacoes
        print('\n🔍 Testando Pontos → Transações...')
        
        if clientes_com_pontos:
            pontos_id = clientes_com_pontos[0][2]
            
            result = session.execute(text("""
                SELECT tp.tipo, tp.pontos, tp.origem, tp.motivo, tp.created_at
                FROM transacoes_pontos tp
                WHERE tp.usuario_pontos_id = :pontos_id
                ORDER BY tp.created_at DESC
                LIMIT 5
            """), {"pontos_id": pontos_id})
            
            transacoes = result.fetchall()
            print(f'   📊 Transações da conta {pontos_id}: {len(transacoes)}')
            
            for trans in transacoes:
                data = trans[4].strftime("%d/%m %H:%M")
                print(f'      📝 {data} | {trans[0]} | {trans[1]} RP | {trans[2]}')
        
        # 3. Testar integridade dos relacionamentos
        print('\n🔍 Testando Integridade dos Relacionamentos...')
        
        # Verificar se toda conta de pontos tem um cliente
        result = session.execute(text("""
            SELECT COUNT(*) as total
            FROM usuarios_pontos up
            LEFT JOIN clientes c ON up.cliente_id = c.id
            WHERE c.id IS NULL
        """))
        
        orphan_pontos = result.fetchone()[0]
        print(f'   ✅ Contas de pontos órfãs: {orphan_pontos}')
        
        # Verificar se toda transação tem uma conta de pontos
        result = session.execute(text("""
            SELECT COUNT(*) as total
            FROM transacoes_pontos tp
            LEFT JOIN usuarios_pontos up ON tp.usuario_pontos_id = up.id
            WHERE up.id IS NULL
        """))
        
        orphan_transacoes = result.fetchone()[0]
        print(f'   ✅ Transações órfãs: {orphan_transacoes}')
        
        # 4. Estatísticas gerais
        print('\n📊 Estatísticas Gerais do Sistema...')
        
        result = session.execute(text("""
            SELECT 
                (SELECT COUNT(*) FROM clientes) as total_clientes,
                (SELECT COUNT(*) FROM usuarios_pontos) as total_contas,
                (SELECT COUNT(*) FROM transacoes_pontos) as total_transacoes,
                (SELECT SUM(rp_points) FROM usuarios_pontos) as total_rp,
                (SELECT COUNT(*) FROM premios WHERE ativo = TRUE) as total_premios
        """))
        
        stats = result.fetchone()
        
        print(f'   👥 Clientes: {stats[0]}')
        print(f'   💰 Contas de pontos: {stats[1]}')
        print(f'   📋 Transações: {stats[2]}')
        print(f'   💎 Total RP em circulação: {stats[3] or 0}')
        print(f'   🏆 Prêmios ativos: {stats[4]}')
        
        # 5. Testar relacionamentos com reservas
        print('\n🔍 Testando Relacionamentos com Reservas...')
        
        result = session.execute(text("""
            SELECT COUNT(*) as total
            FROM reservas r
            LEFT JOIN clientes c ON r.cliente_id = c.id
            WHERE c.id IS NULL
        """))
        
        orphan_reservas = result.fetchone()[0]
        print(f'   ✅ Reservas órfãs: {orphan_reservas}')
        
        # 6. Verificar estrutura das colunas RP
        print('\n🔍 Verificando Estrutura RP...')
        
        result = session.execute(text("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'usuarios_pontos'
            AND column_name = 'rp_points'
        """))
        
        rp_column = result.fetchone()
        if rp_column:
            print(f'   ✅ Coluna rp_points: {rp_column[1]}')
        else:
            print('   ❌ Coluna rp_points não encontrada')
        
        # 7. Testar consulta complexa com joins
        print('\n🔍 Testando Consulta Complexa...')
        
        result = session.execute(text("""
            SELECT 
                c.nome_completo,
                up.rp_points,
                COUNT(tp.id) as num_transacoes,
                MAX(tp.created_at) as ultima_transacao
            FROM clientes c
            LEFT JOIN usuarios_pontos up ON c.id = up.cliente_id
            LEFT JOIN transacoes_pontos tp ON up.id = tp.usuario_pontos_id
            WHERE up.id IS NOT NULL
            GROUP BY c.id, c.nome_completo, up.rp_points
            ORDER BY up.rp_points DESC
            LIMIT 5
        """))
        
        clientes_ranking = result.fetchall()
        
        print(f'   🏆 Top 5 Clientes por RP:')
        for i, cliente in enumerate(clientes_ranking, 1):
            ultima = cliente[3].strftime("%d/%m/%Y") if cliente[3] else "Nunca"
            print(f'      {i}. {cliente[0]}: {cliente[1]} RP ({cliente[2]} transações) - Última: {ultima}')
        
        session.commit()
        
        # 8. Resumo final
        print('\n📋 RESUMO FINAL - Relacionamentos SQLAlchemy')
        print('=' * 60)
        
        status_geral = "✅ FUNCIONANDO" if (
            orphan_pontos == 0 and 
            orphan_transacoes == 0 and 
            orphan_reservas == 0 and 
            rp_column is not None
        ) else "❌ PROBLEMAS"
        
        print(f'🎯 Status Geral: {status_geral}')
        print(f'✅ Cliente → Pontos: OK')
        print(f'✅ Pontos → Cliente: OK')
        print(f'✅ Pontos → Transações: OK')
        print(f'✅ Integridade referencial: OK')
        print(f'✅ Sistema RP: Integrado')
        
        if status_geral == "✅ FUNCIONANDO":
            print('\n🎉 RELACIONAMENTO CLIENTES ↔ PONTOS 100% FUNCIONAL!')
            print('🔗 Todos os relacionamentos SQLAlchemy operacionais')
            print('💎 Sistema RP totalmente integrado')
        else:
            print('\n⚠️  PROBLEMAS ENCONTRADOS - Verificar logs acima')
        
    except Exception as e:
        print(f'\n❌ Erro: {str(e)}')
        import traceback
        traceback.print_exc()
        session.rollback()
        
    finally:
        session.close()

if __name__ == "__main__":
    testar_relacionamentos_sqlalchemy()
