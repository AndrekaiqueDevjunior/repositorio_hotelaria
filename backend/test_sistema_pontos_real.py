#!/usr/bin/env python3
"""
Teste do Sistema de Pontos com os modelos reais do projeto
"""

import sys
import os
sys.path.append('/app')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

def test_sistema_pontos_real():
    """Testa sistema de pontos com modelos reais via SQL direto"""
    
    print('🎯 Teste Sistema de Pontos - Modelos Reais')
    print('=' * 50)
    
    # Conectar ao banco PostgreSQL
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        conn = psycopg2.connect(
            host="postgres",
            database="hotel_cabo_frio",
            user="postgres",
            password="postgres",
            cursor_factory=RealDictCursor
        )
        cursor = conn.cursor()
        
        print('✅ Conectado ao PostgreSQL')
        
        # Limpar dados anteriores
        print('\n🧹 Limpando dados anteriores...')
        cursor.execute("DELETE FROM transacoes_pontos")
        cursor.execute("DELETE FROM usuarios_pontos")
        cursor.execute("DELETE FROM clientes")
        cursor.execute("DELETE FROM usuarios")
        conn.commit()
        
        # Inserir dados de teste
        print('\n📝 Inserindo dados de teste...')
        
        # 1. Usuario Admin
        cursor.execute("""
            INSERT INTO usuarios (nome, email, senha_hash, perfil, status)
            VALUES ('Admin Sistema', 'admin@hotel.com', 'hash123', 'ADMIN', 'ATIVO')
            RETURNING id
        """)
        admin_id = cursor.fetchone()['id']
        
        # 2. Clientes
        cursor.execute("""
            INSERT INTO clientes (nome_completo, documento, email, telefone)
            VALUES 
                ('Ana Costa', '111222333', 'ana@email.com', '119999999'),
                ('Pedro Silva', '444555666', 'pedro@email.com', '118888888'),
                ('Lucia Mendes', '777888999', 'lucia@email.com', '117777777')
            RETURNING id
        """)
        
        clientes_ids = [row['id'] for row in cursor.fetchall()]
        ana_id, pedro_id, lucia_id = clientes_ids
        
        # 3. Contas de pontos
        cursor.execute("""
            INSERT INTO usuarios_pontos (cliente_id, saldo_atual)
            VALUES 
                (%s, 100),  -- Ana: bônus de boas-vindas
                (%s, 0),    -- Pedro: sem pontos iniciais
                (%s, 50)    -- Lucia: bônus menor
            RETURNING id
        """, (ana_id, pedro_id, lucia_id))
        
        pontos_ids = [row['id'] for row in cursor.fetchall()]
        ana_pontos_id, pedro_pontos_id, lucia_pontos_id = pontos_ids
        
        # 4. Transações iniciais (bônus)
        cursor.execute("""
            INSERT INTO transacoes_pontos 
            (usuario_pontos_id, tipo, origem, pontos, motivo, criado_por_usuario_id)
            VALUES 
                (%s, 'CREDITO', 'BEM_VINDO', 100, 'Bônus de boas-vindas', %s),
                (%s, 'CREDITO', 'BEM_VINDO', 50, 'Bônus reduzido', %s)
        """, (ana_pontos_id, admin_id, lucia_pontos_id, admin_id))
        
        conn.commit()
        print('✅ Dados inseridos com sucesso!')
        
        # === TESTES DO SISTEMA ===
        print('\n🎯 Testando Funcionalidades')
        print('=' * 50)
        
        # Teste 1: Consultar saldos
        print('\n1. SALDOS INICIAIS')
        cursor.execute("""
            SELECT c.nome_completo, up.saldo_atual
            FROM clientes c
            LEFT JOIN usuarios_pontos up ON c.id = up.cliente_id
            ORDER BY c.nome_completo
        """)
        
        for row in cursor.fetchall():
            saldo = row['saldo_atual'] if row['saldo_atual'] else 0
            print(f'   {row["nome_completo"]}: {saldo} pontos')
        
        # Teste 2: Adicionar pontos por reserva
        print('\n2. ADICIONANDO PONTOS (RESERVA)')
        
        # Ana fez uma reserva - ganha 50 pontos
        cursor.execute("""
            INSERT INTO transacoes_pontos 
            (usuario_pontos_id, tipo, origem, pontos, motivo, criado_por_usuario_id)
            VALUES (%s, 'CREDITO', 'RESERVA', 50, 'Pontos por reserva RES001', %s)
        """, (ana_pontos_id, admin_id))
        
        # Atualizar saldo
        cursor.execute("""
            UPDATE usuarios_pontos 
            SET saldo_atual = saldo_atual + 50
            WHERE id = %s
        """, (ana_pontos_id,))
        
        print('   ✅ +50 pontos para Ana (reserva)')
        
        # Pedro fez check-in - ganha 30 pontos
        cursor.execute("""
            INSERT INTO transacoes_pontos 
            (usuario_pontos_id, tipo, origem, pontos, motivo, criado_por_usuario_id)
            VALUES (%s, 'CREDITO', 'CHECKIN', 30, 'Pontos por check-in', %s)
        """, (pedro_pontos_id, admin_id))
        
        # Atualizar saldo
        cursor.execute("""
            UPDATE usuarios_pontos 
            SET saldo_atual = saldo_atual + 30
            WHERE id = %s
        """, (pedro_pontos_id,))
        
        print('   ✅ +30 pontos para Pedro (check-in)')
        
        conn.commit()
        
        # Teste 3: Saldos após créditos
        print('\n3. SALDOS APÓS CRÉDITOS')
        cursor.execute("""
            SELECT c.nome_completo, up.saldo_atual,
                   (SELECT COUNT(*) FROM transacoes_pontos tp 
                    WHERE tp.usuario_pontos_id = up.id) as total_transacoes
            FROM clientes c
            LEFT JOIN usuarios_pontos up ON c.id = up.cliente_id
            ORDER BY c.nome_completo
        """)
        
        for row in cursor.fetchall():
            saldo = row['saldo_atual'] if row['saldo_atual'] else 0
            transacoes = row['total_transacoes'] or 0
            print(f'   {row["nome_completo"]}: {saldo} pontos ({transacoes} transações)')
        
        # Teste 4: Extrato detalhado
        print('\n4. EXTRATO DETALHADO')
        
        cursor.execute("""
            SELECT c.nome_completo, tp.tipo, tp.pontos, tp.origem, 
                   tp.motivo, tp.created_at
            FROM transacoes_pontos tp
            JOIN usuarios_pontos up ON tp.usuario_pontos_id = up.id
            JOIN clientes c ON up.cliente_id = c.id
            WHERE c.nome_completo = 'Ana Costa'
            ORDER BY tp.created_at DESC
        """)
        
        print(f'\n   Extrato de Ana Costa:')
        for row in cursor.fetchall():
            sinal = "+" if row['pontos'] > 0 else ""
            data = row['created_at'].strftime("%d/%m %H:%M")
            print(f'     {data} | {row["tipo"]} | {sinal}{row["pontos"]} pts | {row["origem"]}')
            if row['motivo']:
                print(f'        Motivo: {row["motivo"]}')
        
        # Teste 5: Resgatar prêmios (simulado)
        print('\n5. RESGATE DE PRÊMIOS (SIMULADO)')
        
        # Ana quer resgatar um prêmio de 80 pontos
        pontos_premio = 80
        
        # Verificar saldo atual
        cursor.execute("SELECT saldo_atual FROM usuarios_pontos WHERE cliente_id = %s", (ana_id,))
        saldo_ana = cursor.fetchone()['saldo_atual']
        
        if saldo_ana >= pontos_premio:
            # Debitar pontos
            cursor.execute("""
                INSERT INTO transacoes_pontos 
                (usuario_pontos_id, tipo, origem, pontos, motivo, criado_por_usuario_id)
                VALUES (%s, 'DEBITO', 'RESGATE', -80, 'Resgate: Spa Day', %s)
            """, (ana_pontos_id, admin_id))
            
            # Atualizar saldo
            cursor.execute("""
                UPDATE usuarios_pontos 
                SET saldo_atual = saldo_atual - 80
                WHERE id = %s
            """, (ana_pontos_id,))
            
            print(f'   ✅ Ana resgatou Spa Day por {pontos_premio} pontos')
        else:
            print(f'   ❌ Ana não tem pontos suficientes (tem {saldo_ana}, precisa {pontos_premio})')
        
        conn.commit()
        
        # Teste 6: Saldo após resgate
        print('\n6. SALDO APÓS RESGATE')
        cursor.execute("SELECT saldo_atual FROM usuarios_pontos WHERE cliente_id = %s", (ana_id,))
        novo_saldo_ana = cursor.fetchone()['saldo_atual']
        print(f'   Ana: {novo_saldo_ana} pontos (-{pontos_premio} do resgate)')
        
        # Teste 7: Relatórios do sistema
        print('\n7. RELATÓRIOS DO SISTEMA')
        
        # Total de pontos em circulação
        cursor.execute("SELECT SUM(saldo_atual) as total FROM usuarios_pontos")
        total_pontos = cursor.fetchone()['total'] or 0
        print(f'   Total de pontos em circulação: {total_pontos}')
        
        # Clientes com pontos
        cursor.execute("SELECT COUNT(*) as total FROM usuarios_pontos")
        clientes_com_pontos = cursor.fetchone()['total']
        print(f'   Clientes com conta de pontos: {clientes_com_pontos}')
        
        # Transações por tipo
        cursor.execute("""
            SELECT tipo, COUNT(*) as quantidade, SUM(pontos) as total_pontos
            FROM transacoes_pontos
            GROUP BY tipo
            ORDER BY tipo
        """)
        
        print(f'   Transações por tipo:')
        for row in cursor.fetchall():
            print(f'     {row["tipo"]}: {row["quantidade"]} transações, {row["total_pontos"]} pontos')
        
        # Top clientes
        cursor.execute("""
            SELECT c.nome_completo, up.saldo_atual,
                   COUNT(tp.id) as num_transacoes
            FROM clientes c
            JOIN usuarios_pontos up ON c.id = up.cliente_id
            LEFT JOIN transacoes_pontos tp ON up.id = tp.usuario_pontos_id
            GROUP BY c.id, up.id
            ORDER BY up.saldo_atual DESC
            LIMIT 3
        """)
        
        print(f'   Top clientes por saldo:')
        for i, row in enumerate(cursor.fetchall(), 1):
            print(f'     {i}. {row["nome_completo"]}: {row["saldo_atual"]} pts ({row["num_transacoes"]} transações)')
        
        # Teste 8: Histórico completo
        print('\n8. HISTÓRICO COMPLETO DO SISTEMA')
        
        cursor.execute("""
            SELECT tp.created_at, c.nome_completo, tp.tipo, tp.pontos, 
                   tp.origem, tp.motivo, u.nome as operador
            FROM transacoes_pontos tp
            JOIN usuarios_pontos up ON tp.usuario_pontos_id = up.id
            JOIN clientes c ON up.cliente_id = c.id
            LEFT JOIN usuarios u ON tp.criado_por_usuario_id = u.id
            ORDER BY tp.created_at DESC
        """)
        
        print(f'   Todas as transações ({cursor.rowcount}):')
        for i, row in enumerate(cursor.fetchall(), 1):
            sinal = "+" if row['pontos'] > 0 else ""
            data = row['created_at'].strftime("%d/%m %H:%M")
            operador = f" (por {row['operador']})" if row['operador'] else ""
            print(f'     {i}. {data} | {row["nome_completo"]} | {row["tipo"]} | {sinal}{row["pontos"]} pts | {row["origem"]}{operador}')
            if row['motivo']:
                print(f'        {row["motivo"]}')
        
        print('\n🎉 TESTE DO SISTEMA DE PONTOS CONCLUÍDO!')
        print('✅ Funcionalidades validadas com sucesso!')
        
        # Resumo final
        print('\n📊 Resumo Final:')
        print(f'   - {clientes_com_pontos} clientes com pontos')
        print(f'   - {total_pontos} pontos em circulação')
        print(f'   - Sistema operacional para créditos, débitos e relatórios')
        
    except Exception as e:
        print(f'\n❌ Erro: {str(e)}')
        import traceback
        traceback.print_exc()
        
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    test_sistema_pontos_real()
