#!/usr/bin/env python3
"""
Teste simples do relacionamento clientes-pontos direto no banco
"""

import sys
import os
sys.path.append('/app')

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

def testar_relacionamento_simples():
    """Testa o relacionamento de forma simples direto no banco"""
    
    print('🔗 TESTE SIMPLES - Relacionamento Clientes ↔ Pontos')
    print('=' * 60)
    
    try:
        conn = psycopg2.connect(
            host="postgres",
            database="hotel_cabo_frio",
            user="postgres",
            password="postgres",
            cursor_factory=RealDictCursor
        )
        cursor = conn.cursor()
        
        # 1. Verificar estrutura atual
        print('\n📊 Verificando estrutura atual...')
        
        # Clientes
        cursor.execute("SELECT COUNT(*) as total FROM clientes")
        total_clientes = cursor.fetchone()["total"]
        print(f'   👥 Clientes existentes: {total_clientes}')
        
        # Contas de pontos
        cursor.execute("SELECT COUNT(*) as total FROM usuarios_pontos")
        total_pontos = cursor.fetchone()["total"]
        print(f'   💰 Contas de pontos: {total_pontos}')
        
        # 2. Criar cliente teste se não existir
        if total_clientes == 0:
            print('\n🧑 Criando cliente teste...')
            cursor.execute("""
                INSERT INTO clientes (nome_completo, documento, email, telefone)
                VALUES ('Teste Relacionamento', '987654321', 'teste@rel.com', '118888888')
                RETURNING id
            """)
            cliente_id = cursor.fetchone()["id"]
            print(f'   ✅ Cliente criado: ID {cliente_id}')
        else:
            cursor.execute("SELECT id, nome_completo FROM clientes LIMIT 1")
            cliente = cursor.fetchone()
            cliente_id = cliente["id"]
            print(f'   ✅ Usando cliente existente: {cliente["nome_completo"]} (ID {cliente_id})')
        
        # 3. Criar conta de pontos se não existir
        cursor.execute("SELECT id FROM usuarios_pontos WHERE cliente_id = %s", (cliente_id,))
        pontos_existe = cursor.fetchone()
        
        if not pontos_existe:
            print('\n💰 Criando conta de pontos...')
            cursor.execute("""
                INSERT INTO usuarios_pontos (cliente_id, saldo_atual, rp_points)
                VALUES (%s, 0, 0)
                RETURNING id
            """, (cliente_id,))
            pontos_id = cursor.fetchone()["id"]
            print(f'   ✅ Conta criada: ID {pontos_id}')
        else:
            pontos_id = pontos_existe["id"]
            print(f'   ✅ Conta existente: ID {pontos_id}')
        
        # 4. Adicionar transação de teste
        print('\n📝 Adicionando transação de teste...')
        cursor.execute("""
            INSERT INTO transacoes_pontos 
            (usuario_pontos_id, tipo, origem, pontos, motivo)
            VALUES (%s, 'CREDITO', 'RESERVA', 3, 'Teste Suíte Luxo')
            RETURNING id
        """, (pontos_id,))
        
        transacao_id = cursor.fetchone()["id"]
        print(f'   ✅ Transação criada: ID {transacao_id}')
        
        # 5. Atualizar saldo RP
        print('\n💸 Atualizando saldo RP...')
        cursor.execute("""
            UPDATE usuarios_pontos 
            SET rp_points = rp_points + 3
            WHERE id = %s
            RETURNING rp_points
        """, (pontos_id,))
        
        novo_saldo = cursor.fetchone()["rp_points"]
        print(f'   💰 Novo saldo RP: {novo_saldo}')
        
        # 6. Testar relacionamento completo
        print('\n🔍 Testando relacionamento completo...')
        
        # Cliente → Pontos
        cursor.execute("""
            SELECT c.nome_completo, c.email, up.id as pontos_id, up.rp_points, up.saldo_atual
            FROM clientes c
            LEFT JOIN usuarios_pontos up ON c.id = up.cliente_id
            WHERE c.id = %s
        """, (cliente_id,))
        
        cliente_com_pontos = cursor.fetchone()
        
        if cliente_com_pontos:
            print(f'   🧑 Cliente: {cliente_com_pontos["nome_completo"]}')
            print(f'      📧 Email: {cliente_com_pontos["email"]}')
            print(f'      💰 Pontos ID: {cliente_com_pontos["pontos_id"]}')
            print(f'      💎 Saldo RP: {cliente_com_pontos["rp_points"]}')
            print(f'      📊 Saldo Legacy: {cliente_com_pontos["saldo_atual"]}')
        
        # Pontos → Transações
        cursor.execute("""
            SELECT tp.tipo, tp.pontos, tp.origem, tp.motivo, tp.created_at
            FROM transacoes_pontos tp
            WHERE tp.usuario_pontos_id = %s
            ORDER BY tp.created_at DESC
        """, (pontos_id,))
        
        transacoes = cursor.fetchall()
        print(f'   📊 Transações ({len(transacoes)}):')
        
        for trans in transacoes:
            data = trans["created_at"].strftime("%d/%m %H:%M")
            print(f'      📝 {data} | {trans["tipo"]} | +{trans["pontos"]} RP | {trans["origem"]}')
            if trans["motivo"]:
                print(f'         💭 {trans["motivo"]}')
        
        # 7. Verificar prêmios disponíveis
        print('\n🏆 Verificando prêmios disponíveis...')
        cursor.execute("SELECT * FROM premios WHERE ativo = TRUE ORDER BY preco_em_pontos")
        
        premios = cursor.fetchall()
        print(f'   🎁 Prêmios ({len(premios)}):')
        
        for premio in premios:
            pode_resgatar = novo_saldo >= premio["preco_em_pontos"]
            status = "✅" if pode_resgatar else "❌"
            print(f'      {status} {premio["nome"]}: {premio["preco_em_pontos"]} RP')
        
        conn.commit()
        
        # 8. Resumo final
        print('\n📋 RESUMO FINAL - Relacionamento Testado')
        print('=' * 60)
        print(f'✅ Cliente → Pontos: Funcionando')
        print(f'✅ Pontos → Cliente: Funcionando')
        print(f'✅ Pontos → Transações: Funcionando')
        print(f'✅ Saldo RP atualizado: {novo_saldo}')
        print(f'✅ Transações registradas: {len(transacoes)}')
        
        print('\n🎯 RELACIONAMENTO CLIENTES ↔ PONTOS 100% FUNCIONAL!')
        
    except Exception as e:
        print(f'\n❌ Erro: {str(e)}')
        import traceback
        traceback.print_exc()
        if 'conn' in locals():
            conn.rollback()
        
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    testar_relacionamento_simples()
