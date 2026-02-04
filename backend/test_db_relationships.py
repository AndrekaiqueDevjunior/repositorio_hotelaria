#!/usr/bin/env python3
"""
Script para testar relacionamentos inserindo dados reais
"""

import sys
import os
sys.path.append('/app')

import psycopg2
from psycopg2.extras import RealDictCursor

def test_database_relationships():
    """Testa relacionamentos diretamente no PostgreSQL"""
    
    print('🔧 Testando relacionamentos no PostgreSQL...')
    
    # Conectar ao banco
    try:
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
        cursor.execute("DELETE FROM pagamentos")
        cursor.execute("DELETE FROM hospedes_adicionais")
        cursor.execute("DELETE FROM itens_cobranca")
        cursor.execute("DELETE FROM reservas")
        cursor.execute("DELETE FROM quartos")
        cursor.execute("DELETE FROM tipos_suite")
        cursor.execute("DELETE FROM clientes")
        cursor.execute("DELETE FROM usuarios")
        conn.commit()
        
        # Inserir dados de teste
        print('\n📝 Inserindo dados de teste...')
        
        # 1. Usuario
        cursor.execute("""
            INSERT INTO usuarios (nome, email, senha_hash, perfil, status)
            VALUES ('Admin', 'admin@hotel.com', 'hash123', 'ADMIN', 'ATIVO')
            RETURNING id
        """)
        usuario_id = cursor.fetchone()['id']
        
        # 2. Tipo Suite
        cursor.execute("""
            INSERT INTO tipos_suite (nome, descricao, capacidade, pontos_por_par)
            VALUES ('Suíte Deluxe', 'Suíte de luxo', 2, 50)
            RETURNING id
        """)
        tipo_suite_id = cursor.fetchone()['id']
        
        # 3. Quarto
        cursor.execute("""
            INSERT INTO quartos (numero, tipo_suite_id, status)
            VALUES ('101', %s, 'ATIVO')
            RETURNING id
        """, (tipo_suite_id,))
        quarto_id = cursor.fetchone()['id']
        
        # 4. Cliente
        cursor.execute("""
            INSERT INTO clientes (nome_completo, documento, email, telefone)
            VALUES ('João Silva', '123456789', 'joao@email.com', '119999999')
            RETURNING id
        """)
        cliente_id = cursor.fetchone()['id']
        
        # 5. UsuarioPontos
        cursor.execute("""
            INSERT INTO usuarios_pontos (cliente_id, saldo_atual)
            VALUES (%s, 100)
            RETURNING id
        """, (cliente_id,))
        usuario_pontos_id = cursor.fetchone()['id']
        
        # 6. Reserva
        cursor.execute("""
            INSERT INTO reservas 
            (codigo_reserva, cliente_id, quarto_id, status_reserva, 
             checkin_previsto, checkout_previsto, valor_diaria, 
             num_diarias_previstas, valor_previsto, criado_por_usuario_id)
            VALUES ('RES001', %s, %s, 'CONFIRMADA', 
                   NOW(), NOW() + INTERVAL '2 days', 250.00, 2, 500.00, %s)
            RETURNING id
        """, (cliente_id, quarto_id, usuario_id))
        reserva_id = cursor.fetchone()['id']
        
        # 7. Pagamento
        cursor.execute("""
            INSERT INTO pagamentos 
            (reserva_id, cliente_id, metodo, valor, status_pagamento)
            VALUES (%s, %s, 'CARTAO', 500.00, 'APROVADO')
            RETURNING id
        """, (reserva_id, cliente_id))
        pagamento_id = cursor.fetchone()['id']
        
        # 8. TransacaoPontos
        cursor.execute("""
            INSERT INTO transacoes_pontos 
            (usuario_pontos_id, tipo, origem, pontos, reserva_id, criado_por_usuario_id)
            VALUES (%s, 'CREDITO', 'RESERVA', 50, %s, %s)
        """, (usuario_pontos_id, reserva_id, usuario_id))
        
        conn.commit()
        print('✅ Dados inseridos com sucesso!')
        
        # Testar relacionamentos
        print('\n🔍 Testando relacionamentos...')
        
        # 1. Cliente -> Reservas
        cursor.execute("""
            SELECT c.nome_completo, r.codigo_reserva, r.status_reserva
            FROM clientes c
            LEFT JOIN reservas r ON c.id = r.cliente_id
            WHERE c.id = %s
        """, (cliente_id,))
        
        print('\n👤 Cliente e suas reservas:')
        for row in cursor.fetchall():
            if row['codigo_reserva']:
                print(f"   {row['nome_completo']} -> {row['codigo_reserva']} ({row['status_reserva']})")
            else:
                print(f"   {row['nome_completo']} -> Sem reservas")
        
        # 2. Reserva -> Cliente + Quarto
        cursor.execute("""
            SELECT r.codigo_reserva, c.nome_completo as cliente_nome, 
                   q.numero as quarto_numero, ts.nome as tipo_suite
            FROM reservas r
            LEFT JOIN clientes c ON r.cliente_id = c.id
            LEFT JOIN quartos q ON r.quarto_id = q.id
            LEFT JOIN tipos_suite ts ON q.tipo_suite_id = ts.id
            WHERE r.id = %s
        """, (reserva_id,))
        
        print('\n🏨 Reserva completa:')
        row = cursor.fetchone()
        if row:
            print(f"   {row['codigo_reserva']}")
            print(f"   Cliente: {row['cliente_nome']}")
            print(f"   Quarto: {row['quarto_numero']} ({row['tipo_suite']})")
        
        # 3. Quarto -> TipoSuite + Reservas
        cursor.execute("""
            SELECT q.numero, ts.nome as tipo_suite, ts.capacidade,
                   COUNT(r.id) as num_reservas
            FROM quartos q
            LEFT JOIN tipos_suite ts ON q.tipo_suite_id = ts.id
            LEFT JOIN reservas r ON q.id = r.quarto_id
            WHERE q.id = %s
            GROUP BY q.numero, ts.nome, ts.capacidade
        """, (quarto_id,))
        
        print('\n🚪 Quarto e informações:')
        row = cursor.fetchone()
        if row:
            print(f"   Quarto {row['numero']}")
            print(f"   Tipo: {row['tipo_suite']} (capacidade: {row['capacidade']})")
            print(f"   Reservas: {row['num_reservas']}")
        
        # 4. Cliente -> Pontos
        cursor.execute("""
            SELECT c.nome_completo, up.saldo_atual
            FROM clientes c
            LEFT JOIN usuarios_pontos up ON c.id = up.cliente_id
            WHERE c.id = %s
        """, (cliente_id,))
        
        print('\n💰 Pontos do cliente:')
        row = cursor.fetchone()
        if row:
            print(f"   {row['nome_completo']}: {row['saldo_atual'] or 0} pontos")
        
        # 5. Pagamento -> Reserva + Cliente
        cursor.execute("""
            SELECT p.valor, p.metodo, r.codigo_reserva, c.nome_completo
            FROM pagamentos p
            LEFT JOIN reservas r ON p.reserva_id = r.id
            LEFT JOIN clientes c ON p.cliente_id = c.id
            WHERE p.id = %s
        """, (pagamento_id,))
        
        print('\n💳 Pagamento completo:')
        row = cursor.fetchone()
        if row:
            print(f"   R$ {row['valor']} ({row['metodo']})")
            print(f"   Reserva: {row['codigo_reserva']}")
            print(f"   Cliente: {row['nome_completo']}")
        
        # 6. TransacoesPontos
        cursor.execute("""
            SELECT tp.pontos, tp.tipo, tp.origem, r.codigo_reserva, c.nome_completo
            FROM transacoes_pontos tp
            LEFT JOIN reservas r ON tp.reserva_id = r.id
            LEFT JOIN usuarios_pontos up ON tp.usuario_pontos_id = up.id
            LEFT JOIN clientes c ON up.cliente_id = c.id
            WHERE tp.usuario_pontos_id = %s
        """, (usuario_pontos_id,))
        
        print('\n🎯 Transações de pontos:')
        for row in cursor.fetchall():
            print(f"   {row['pontos']} pontos ({row['tipo']}) - {row['origem']}")
            print(f"   Reserva: {row['codigo_reserva']}")
            print(f"   Cliente: {row['nome_completo']}")
        
        print('\n🎉 Todos os relacionamentos testados com sucesso!')
        
    except Exception as e:
        print(f'\n❌ Erro: {str(e)}')
        import traceback
        traceback.print_exc()
        
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    test_database_relationships()
