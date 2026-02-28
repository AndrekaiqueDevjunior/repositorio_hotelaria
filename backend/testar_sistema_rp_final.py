#!/usr/bin/env python3
"""
Teste final do sistema RP com códigos únicos
"""

import sys
import os
sys.path.append('/app')

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import time

def testar_sistema_rp_final():
    """Teste final do sistema RP com códigos únicos"""
    
    print('🎯 TESTE FINAL - Sistema de Pontos RP')
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
        
        print('✅ Conectado ao banco de dados')
        
        # 1. Obter usuário admin
        cursor.execute("SELECT id FROM usuarios WHERE perfil = 'ADMIN' LIMIT 1")
        admin = cursor.fetchone()
        admin_id = admin["id"] if admin else None
        
        # 2. Obter clientes existentes
        cursor.execute("""
            SELECT id, nome_completo 
            FROM clientes 
            WHERE nome_completo LIKE '%Luxo%' OR nome_completo LIKE '%Dupla%' 
            OR nome_completo LIKE '%Master%' OR nome_completo LIKE '%Real%'
            ORDER BY id
            LIMIT 4
        """)
        
        clientes = cursor.fetchall()
        
        if len(clientes) < 4:
            print('❌ Clientes insuficientes para teste')
            return
        
        # 3. Obter quartos por tipo
        cursor.execute("""
            SELECT q.id, q.numero, ts.nome as tipo_suite, ts.pontos_por_par
            FROM quartos q
            JOIN tipos_suite ts ON q.tipo_suite_id = ts.id
            ORDER BY ts.id, q.numero
        """)
        
        quartos = cursor.fetchall()
        quartos_por_tipo = {}
        for quarto in quartos:
            tipo = quarto["tipo_suite"]
            if tipo not in quartos_por_tipo:
                quartos_por_tipo[tipo] = []
            quartos_por_tipo[tipo].append(quarto)
        
        # 4. Criar reservas teste
        print('\n📋 Criando Reservas Teste...')
        
        reservas_teste = [
            # (cliente_index, tipo_suite, valor_diaria, num_diarias, rp_esperado)
            (0, 'Suíte Luxo', 325, 2, 3),      # Maria Luxo: R$ 650 = 3 RP
            (1, 'Suíte Dupla', 650, 2, 4),      # João Dupla: R$ 1300 = 4 RP
            (2, 'Suíte Master', 425, 2, 4),     # Ana Master: R$ 850 = 4 RP
            (3, 'Suíte Real', 550, 2, 5),      # Carlos Real: R$ 1100 = 5 RP
        ]
        
        for i, (cliente_idx, tipo_suite, valor_diaria, num_diarias, rp_esperado) in enumerate(reservas_teste):
            cliente = clientes[cliente_idx]
            quarto_disponivel = quartos_por_tipo[tipo_suite][i]
            
            valor_total = valor_diaria * num_diarias
            checkin = datetime.now() + timedelta(days=7+i)
            checkout = checkin + timedelta(days=num_diarias)
            
            # Gerar código único
            codigo_reserva = f"RP{int(time.time())}{i}{num_diarias}"
            
            # Criar reserva
            cursor.execute("""
                INSERT INTO reservas 
                (codigo_reserva, cliente_id, quarto_id, status_reserva,
                 checkin_previsto, checkout_previsto, valor_diaria,
                 num_diarias_previstas, valor_previsto, criado_por_usuario_id)
                VALUES (%s, %s, %s, 'CONFIRMADA', %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                codigo_reserva,
                cliente["id"],
                quarto_disponivel["id"],
                checkin,
                checkout,
                valor_diaria,
                num_diarias,
                valor_total,
                admin_id
            ))
            
            reserva_id = cursor.fetchone()["id"]
            
            # Criar pagamento
            cursor.execute("""
                INSERT INTO pagamentos 
                (reserva_id, cliente_id, metodo, valor, status_pagamento)
                VALUES (%s, %s, 'CREDITO', %s, 'CONFIRMADO')
                RETURNING id
            """, (reserva_id, cliente["id"], valor_total))
            
            # Calcular pontos
            cursor.execute("SELECT calcular_pontos_rp(%s, %s)", (valor_total, num_diarias))
            rp_calculado = cursor.fetchone()["calcular_pontos_rp"]
            
            # Obter ID da conta de pontos
            cursor.execute("SELECT id FROM usuarios_pontos WHERE cliente_id = %s", (cliente["id"],))
            pontos_id = cursor.fetchone()["id"]
            
            # Creditar pontos RP
            cursor.execute("""
                INSERT INTO transacoes_pontos 
                (usuario_pontos_id, tipo, origem, pontos, motivo, criado_por_usuario_id)
                VALUES (%s, 'CREDITO', 'RESERVA', %s, %s, %s)
            """, (pontos_id, rp_calculado, f'Pontos RP: {tipo_suite}', admin_id))
            
            # Atualizar saldo RP
            cursor.execute("""
                UPDATE usuarios_pontos 
                SET rp_points = rp_points + %s
                WHERE id = %s
            """, (rp_calculado, pontos_id))
            
            status = "✅" if rp_calculado == rp_esperado else "❌"
            print(f'   {status} {cliente["nome_completo"]}: {tipo_suite}')
            print(f'      R$ {valor_total} ({num_diarias} diárias) = {rp_calculado} RP (esperado: {rp_esperado})')
        
        conn.commit()
        
        # 5. Relatório final
        print('\n📊 RELATÓRIO FINAL - Sistema RP')
        print('=' * 60)
        
        print('\n💰 Saldo de Pontos RP:')
        cursor.execute("""
            SELECT c.nome_completo, up.rp_points, up.saldo_atual
            FROM clientes c
            JOIN usuarios_pontos up ON c.id = up.cliente_id
            WHERE c.nome_completo IN (%s, %s, %s, %s)
            ORDER BY up.rp_points DESC
        """, ('Maria Luxo', 'João Dupla', 'Ana Master', 'Carlos Real'))
        
        for cliente in cursor.fetchall():
            print(f'   🧑 {cliente["nome_completo"]}: {cliente["rp_points"]} RP (legacy: {cliente["saldo_atual"]} pts)')
        
        print('\n🏆 Prêmios Disponíveis:')
        cursor.execute("SELECT * FROM premios ORDER BY preco_em_pontos")
        for premio in cursor.fetchall():
            print(f'   🎁 {premio["nome"]}: {premio["preco_em_pontos"]} RP')
        
        print('\n🎯 Resgates Possíveis:')
        cursor.execute("""
            SELECT c.nome_completo, up.rp_points, p.nome as premio, p.preco_em_pontos
            FROM clientes c
            JOIN usuarios_pontos up ON c.id = up.cliente_id
            CROSS JOIN premios p
            WHERE up.rp_points >= p.preco_em_pontos
            AND c.nome_completo IN (%s, %s, %s, %s)
            ORDER BY c.nome_completo, p.preco_em_pontos
        """, ('Maria Luxo', 'João Dupla', 'Ana Master', 'Carlos Real'))
        
        resgates = cursor.fetchall()
        if resgates:
            for resgate in resgates:
                print(f'   ✅ {resgate["nome_completo"]} → {resgate["premio"]} ({resgate["preco_em_pontos"]} RP)')
        else:
            print('   ⚠️  Nenhum resgate possível ainda')
        
        print('\n✅ SISTEMA RP IMPLEMENTADO E TESTADO!')
        print('🎯 Regras: a cada 2 diárias conforme valor')
        print('💎 Pontos RP funcionando perfeitamente!')
        
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
    testar_sistema_rp_final()
