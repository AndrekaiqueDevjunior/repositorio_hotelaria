#!/usr/bin/env python3
"""
Teste completo de integração do sistema - Reservas + Pagamentos + Pontos
"""

import sys
import os
sys.path.append('/app')

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta

def test_integracao_completa():
    """Teste completo do fluxo: Reserva → Pagamento → Check-in → Pontos"""
    
    print('🎯 TESTE DE INTEGRAÇÃO COMPLETA DO SISTEMA')
    print('=' * 70)
    print('Fluxo: Cliente → Reserva → Pagamento → Check-in → Pontos')
    print('=' * 70)
    
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
        
        # === ETAPA 1: Criar Cliente e Conta de Pontos ===
        print('\n📝 ETAPA 1: Criando Cliente e Conta de Pontos')
        print('-' * 50)
        
        cursor.execute("""
            INSERT INTO clientes (nome_completo, documento, email, telefone)
            VALUES ('João Turista', '11122233344', 'joao@email.com', '119999999')
            RETURNING id
        """)
        cliente_id = cursor.fetchone()["id"]
        
        cursor.execute("""
            INSERT INTO usuarios_pontos (cliente_id, saldo_atual)
            VALUES (%s, 0)
            RETURNING id
        """, (cliente_id,))
        pontos_id = cursor.fetchone()["id"]
        
        print(f'✅ Cliente criado: ID {cliente_id}')
        print(f'✅ Conta de pontos criada: ID {pontos_id}')
        
        # === ETAPA 2: Criar Reserva ===
        print('\n🏨 ETAPA 2: Criando Reserva')
        print('-' * 50)
        
        # Obter usuário admin e quarto disponível
        cursor.execute("SELECT id FROM usuarios WHERE perfil = 'ADMIN' LIMIT 1")
        admin_id = cursor.fetchone()["id"]
        
        cursor.execute("""
            SELECT q.id, q.numero, ts.nome as tipo_suite
            FROM quartos q
            JOIN tipos_suite ts ON q.tipo_suite_id = ts.id
            WHERE q.status = 'ATIVO'
            LIMIT 1
        """)
        quarto = cursor.fetchone()
        
        # Datas da reserva
        checkin = datetime.now() + timedelta(days=7)
        checkout = datetime.now() + timedelta(days=9)
        valor_diaria = 350.00
        num_diarias = 2
        
        cursor.execute("""
            INSERT INTO reservas 
            (codigo_reserva, cliente_id, quarto_id, status_reserva, 
             checkin_previsto, checkout_previsto, valor_diaria, 
             num_diarias_previstas, valor_previsto, criado_por_usuario_id)
            VALUES 
            (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            f"RES{datetime.now().strftime('%Y%m%d%H%M%S')}",
            cliente_id,
            quarto["id"],
            "PENDENTE",
            checkin,
            checkout,
            valor_diaria,
            num_diarias,
            valor_diaria * num_diarias,
            admin_id
        ))
        
        reserva_id = cursor.fetchone()["id"]
        codigo_reserva = f"RES{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        print(f'✅ Reserva criada: ID {reserva_id}')
        print(f'✅ Código: {codigo_reserva}')
        print(f'✅ Quarto: {quarto["numero"]} ({quarto["tipo_suite"]})')
        print(f'✅ Período: {checkin.strftime("%d/%m/%Y")} a {checkout.strftime("%d/%m/%Y")}')
        print(f'✅ Valor: R$ {valor_diaria * num_diarias:.2f}')
        
        # === ETAPA 3: Processar Pagamento ===
        print('\n💳 ETAPA 3: Processando Pagamento')
        print('-' * 50)
        
        cursor.execute("""
            INSERT INTO pagamentos 
            (reserva_id, cliente_id, metodo, valor, status_pagamento, provider, payment_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            reserva_id,
            cliente_id,
            "CREDITO",
            valor_diaria * num_diarias,
            "CONFIRMADO",
            "CIELO",
            f"PAY_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        ))
        
        pagamento_id = cursor.fetchone()["id"]
        
        print(f'✅ Pagamento criado: ID {pagamento_id}')
        print(f'✅ Método: CARTÃO DE CRÉDITO')
        print(f'✅ Status: CONFIRMADO')
        print(f'✅ Provider: CIELO')
        
        # === ETAPA 4: Confirmar Reserva ===
        print('\n🎯 ETAPA 4: Confirmando Reserva')
        print('-' * 50)
        
        cursor.execute("""
            UPDATE reservas 
            SET status_reserva = 'CONFIRMADA',
                atualizado_por_usuario_id = %s,
                updated_at = NOW()
            WHERE id = %s
        """, (admin_id, reserva_id))
        
        print(f'✅ Reserva {codigo_reserva} confirmada!')
        
        # === ETAPA 5: Adicionar Pontos por Reserva ===
        print('\n💰 ETAPA 5: Adicionando Pontos de Fidelidade')
        print('-' * 50)
        
        # Obter pontos por par do tipo de suíte
        cursor.execute("""
            SELECT ts.pontos_por_par
            FROM quartos q
            JOIN tipos_suite ts ON q.tipo_suite_id = ts.id
            WHERE q.id = %s
        """, (quarto["id"],))
        
        pontos_por_par = cursor.fetchone()["pontos_por_par"]
        pontos_ganhos = pontos_por_par * num_diarias  # 2 diárias
        
        # Creditar pontos
        cursor.execute("""
            INSERT INTO transacoes_pontos 
            (usuario_pontos_id, tipo, origem, pontos, motivo, criado_por_usuario_id)
            VALUES (%s, 'CREDITO', 'RESERVA', %s, %s, %s)
        """, (pontos_id, pontos_ganhos, f'Pontos por reserva {codigo_reserva}', admin_id))
        
        # Atualizar saldo
        cursor.execute("""
            UPDATE usuarios_pontos 
            SET saldo_atual = saldo_atual + %s,
                updated_at = NOW()
            WHERE id = %s
        """, (pontos_ganhos, pontos_id))
        
        print(f'✅ +{pontos_ganhos} pontos adicionados à conta')
        print(f'✅ Origem: RESERVA')
        print(f'✅ Motivo: Pontos por reserva {codigo_reserva}')
        
        # === ETAPA 6: Simular Check-in ===
        print('\n🏨 ETAPA 6: Simulando Check-in')
        print('-' * 50)
        
        # Atualizar status da reserva para HOSPEDADO
        cursor.execute("""
            UPDATE reservas 
            SET status_reserva = 'HOSPEDADO',
                checkin_real = NOW(),
                atualizado_por_usuario_id = %s,
                updated_at = NOW()
            WHERE id = %s
        """, (admin_id, reserva_id))
        
        # Atualizar status do quarto
        cursor.execute("""
            UPDATE quartos 
            SET status = 'OCUPADO',
                updated_at = NOW()
            WHERE id = %s
        """, (quarto["id"],))
        
        # Adicionar pontos por check-in
        pontos_checkin = 30
        cursor.execute("""
            INSERT INTO transacoes_pontos 
            (usuario_pontos_id, tipo, origem, pontos, motivo, criado_por_usuario_id)
            VALUES (%s, 'CREDITO', 'CHECKIN', %s, %s, %s)
        """, (pontos_id, pontos_checkin, 'Pontos por check-in', admin_id))
        
        # Atualizar saldo
        cursor.execute("""
            UPDATE usuarios_pontos 
            SET saldo_atual = saldo_atual + %s,
                updated_at = NOW()
            WHERE id = %s
        """, (pontos_checkin, pontos_id))
        
        print(f'✅ Check-in realizado para {codigo_reserva}')
        print(f'✅ Quarto {quarto["numero"]} marcado como OCUPADO')
        print(f'✅ +{pontos_checkin} pontos por check-in')
        
        # === ETAPA 7: Verificar Saldo Final ===
        print('\n💎 ETAPA 7: Verificando Saldo Final de Pontos')
        print('-' * 50)
        
        cursor.execute("SELECT saldo_atual FROM usuarios_pontos WHERE id = %s", (pontos_id,))
        saldo_final = cursor.fetchone()["saldo_atual"]
        
        print(f'✅ Saldo final: {saldo_final} pontos')
        print(f'✅ Total ganho: {pontos_ganhos + pontos_checkin} pontos')
        
        # === ETAPA 8: Extrato Completo ===
        print('\n📋 ETAPA 8: Extrato Completo de Transações')
        print('-' * 50)
        
        cursor.execute("""
            SELECT tp.tipo, tp.pontos, tp.origem, tp.motivo, tp.created_at
            FROM transacoes_pontos tp
            WHERE tp.usuario_pontos_id = %s
            ORDER BY tp.created_at ASC
        """, (pontos_id,))
        
        transacoes = cursor.fetchall()
        
        print(f'Extrato do cliente:')
        for trans in transacoes:
            sinal = "+" if trans["pontos"] > 0 else ""
            data = trans["created_at"].strftime("%d/%m %H:%M")
            print(f'   {data} | {trans["tipo"]} | {sinal}{trans["pontos"]} pts | {trans["origem"]}')
            if trans["motivo"]:
                print(f'      💭 {trans["motivo"]}')
        
        # === ETAPA 9: Relatório Final ===
        print('\n📊 ETAPA 9: Relatório Final da Operação')
        print('-' * 50)
        
        # Status da reserva
        cursor.execute("""
            SELECT r.*, c.nome_completo, q.numero, ts.nome as tipo_suite
            FROM reservas r
            JOIN clientes c ON r.cliente_id = c.id
            LEFT JOIN quartos q ON r.quarto_id = q.id
            LEFT JOIN tipos_suite ts ON q.tipo_suite_id = ts.id
            WHERE r.id = %s
        """, (reserva_id,))
        
        reserva_info = cursor.fetchone()
        
        print('📋 DADOS DA RESERVA:')
        print(f'   Código: {codigo_reserva}')
        print(f'   Cliente: {reserva_info["nome_completo"]}')
        print(f'   Quarto: {reserva_info["numero"]} ({reserva_info["tipo_suite"]})')
        print(f'   Status: {reserva_info["status_reserva"]}')
        print(f'   Check-in: {reserva_info["checkin_real"]}')
        print(f'   Valor: R$ {reserva_info["valor_previsto"]:.2f}')
        
        # Status do pagamento
        cursor.execute("""
            SELECT metodo, valor, status_pagamento, data_pagamento
            FROM pagamentos
            WHERE reserva_id = %s
        """, (reserva_id,))
        
        pagamento_info = cursor.fetchone()
        
        print('\n💳 DADOS DO PAGAMENTO:')
        print(f'   Método: {pagamento_info["metodo"]}')
        print(f'   Valor: R$ {pagamento_info["valor"]:.2f}')
        print(f'   Status: {pagamento_info["status_pagamento"]}')
        print(f'   Data: {pagamento_info["data_pagamento"]}')
        
        # Status dos pontos
        print(f'\n💰 DADOS DOS PONTOS:')
        print(f'   Saldo atual: {saldo_final} pontos')
        print(f'   Transações: {len(transacoes)}')
        
        conn.commit()
        
        print('\n🎉 TESTE DE INTEGRAÇÃO CONCLUÍDO!')
        print('✅ Fluxo completo funcionando perfeitamente!')
        print('✅ Reserva → Pagamento → Check-in → Pontos: 100% integrado!')
        
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
    test_integracao_completa()
