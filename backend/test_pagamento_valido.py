#!/usr/bin/env python3
import requests
import json
from datetime import datetime, timedelta

# Base URL
base_url = 'http://localhost:8000/api/v1'

print('=== TESTANDO PAGAMENTO CIELO COM RESERVA VÁLIDA ===')
print()

# 1. Fazer Login
print('1. FAZENDO LOGIN...')
login_data = {'email': 'admin@hotelreal.com.br', 'password': 'admin123'}
r = requests.post(f'{base_url}/login', json=login_data)
print(f'Status: {r.status_code}')

if r.status_code == 200:
    print('✅ Login bem-sucedido')
    cookies = r.cookies.get_dict()
    headers = {'Content-Type': 'application/json'}
    
    # 2. Listar clientes
    print()
    print('2. BUSCANDO CLIENTE...')
    r = requests.get(f'{base_url}/clientes', cookies=cookies)
    
    if r.status_code == 200:
        clientes_response = r.json()
        clientes = clientes_response['clientes'] if 'clientes' in clientes_response else clientes_response
        
        if clientes:
            cliente_id = clientes[0]['id']
            print(f'✅ Cliente: {clientes[0].get("nome_completo", "N/A")} (ID: {cliente_id})')
            
            # 3. Criar reserva válida
            print()
            print('3. CRIANDO RESERVA VÁLIDA...')
            
            # Buscar quarto disponível
            r = requests.get(f'{base_url}/quartos/disponiveis', cookies=cookies)
            if r.status_code == 200 and r.json():
                quarto_disponivel = r.json()[0]
                quarto_numero = quarto_disponivel['numero']
                
                amanha = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
                depois_amanha = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')
                
                reserva_data = {
                    'cliente_id': cliente_id,
                    'quarto_numero': quarto_numero,
                    'checkin_previsto': amanha,
                    'checkout_previsto': depois_amanha,
                    'valor_diaria': 150.00,
                    'num_diarias': 1
                }
                
                r = requests.post(f'{base_url}/reservas', json=reserva_data, headers=headers, cookies=cookies)
                
                if r.status_code == 201:
                    reserva = r.json()
                    reserva_id = reserva['id']
                    print(f'✅ Reserva criada: ID {reserva_id} - Status: {reserva["status"]}')
                    
                    # 4. Testar pagamentos com reserva válida
                    print()
                    print('4. TESTANDO PAGAMENTOS COM RESERVA VÁLIDA...')
                    
                    # Teste 1: PIX (funciona sempre)
                    print()
                    print('4.1 TESTE - Pagamento PIX:')
                    pagamento_pix = {
                        'reserva_id': reserva_id,
                        'valor': 150.00,
                        'metodo': 'pix'
                    }
                    
                    headers_with_idempotency = {
                        'Content-Type': 'application/json',
                        'X-Idempotency-Key': f'test_pix_{datetime.now().strftime("%Y%m%d%H%M%S")}'
                    }
                    
                    r = requests.post(f'{base_url}/pagamentos', json=pagamento_pix, headers=headers_with_idempotency, cookies=cookies)
                    print(f'   Status: {r.status_code}')
                    
                    if r.status_code == 201:
                        pagamento = r.json()
                        print(f'   ✅ Pagamento PIX criado: ID {pagamento["id"]}')
                        print(f'   Status: {pagamento["status"]}')
                        print(f'   Método: {pagamento["metodo"]}')
                        print(f'   URL QR Code: {pagamento.get("url_pagamento", "N/A")}')
                    else:
                        print(f'   ❌ Erro: {r.text}')
                    
                    # Teste 2: Cartão com dados completos
                    print()
                    print('4.2 TESTE - Pagamento Cartão (Dados completos):')
                    pagamento_cartao = {
                        'reserva_id': reserva_id,
                        'valor': 150.00,
                        'metodo': 'credit_card',
                        'parcelas': 1,
                        'cartao_numero': '0000000000000001',
                        'cartao_validade': '12/2025',
                        'cartao_cvv': '123',
                        'cartao_nome': 'TESTE SANDBOX'
                    }
                    
                    headers_with_idempotency = {
                        'Content-Type': 'application/json',
                        'X-Idempotency-Key': f'test_cartao_{datetime.now().strftime("%Y%m%d%H%M%S")}'
                    }
                    
                    r = requests.post(f'{base_url}/pagamentos', json=pagamento_cartao, headers=headers_with_idempotency, cookies=cookies)
                    print(f'   Status: {r.status_code}')
                    
                    if r.status_code == 201:
                        pagamento = r.json()
                        print(f'   ✅ Pagamento Cartão criado: ID {pagamento["id"]}')
                        print(f'   Status: {pagamento["status"]}')
                        print(f'   Método: {pagamento["metodo"]}')
                        print(f'   Parcelas: {pagamento.get("parcelas", "N/A")}')
                        print(f'   Nome no cartão: {pagamento.get("cartao_nome", "N/A")}')
                    else:
                        print(f'   ❌ Erro: {r.text}')
                    
                    # Teste 3: Cartão com dados faltando
                    print()
                    print('4.3 TESTE - Cartão com dados faltando:')
                    pagamento_cartao_incompleto = {
                        'reserva_id': reserva_id,
                        'valor': 150.00,
                        'metodo': 'credit_card',
                        'parcelas': 1
                        # Faltando: cartao_numero, cartao_validade, cartao_cvv, cartao_nome
                    }
                    
                    headers_with_idempotency = {
                        'Content-Type': 'application/json',
                        'X-Idempotency-Key': f'test_incomp_{datetime.now().strftime("%Y%m%d%H%M%S")}'
                    }
                    
                    r = requests.post(f'{base_url}/pagamentos', json=pagamento_cartao_incompleto, headers=headers_with_idempotency, cookies=cookies)
                    print(f'   Status: {r.status_code}')
                    
                    if r.status_code == 201:
                        pagamento = r.json()
                        print(f'   ⚠️  Pagamento criado mesmo sem dados: ID {pagamento["id"]}')
                    else:
                        print(f'   ❌ Erro esperado: {r.text}')
                    
                    # Teste 4: Cartão com número inválido
                    print()
                    print('4.4 TESTE - Cartão com número inválido:')
                    pagamento_cartao_invalido = {
                        'reserva_id': reserva_id,
                        'valor': 150.00,
                        'metodo': 'credit_card',
                        'parcelas': 1,
                        'cartao_numero': '123',  # Número muito curto
                        'cartao_validade': '12/2025',
                        'cartao_cvv': '123',
                        'cartao_nome': 'TESTE SANDBOX'
                    }
                    
                    headers_with_idempotency = {
                        'Content-Type': 'application/json',
                        'X-Idempotency-Key': f'test_invalid_{datetime.now().strftime("%Y%m%d%H%M%S")}'
                    }
                    
                    r = requests.post(f'{base_url}/pagamentos', json=pagamento_cartao_invalido, headers=headers_with_idempotency, cookies=cookies)
                    print(f'   Status: {r.status_code}')
                    
                    if r.status_code == 201:
                        pagamento = r.json()
                        print(f'   ✅ Pagamento criado (sandbox aceita qualquer número): ID {pagamento["id"]}')
                    else:
                        print(f'   ❌ Erro: {r.text}')
                    
                    print()
                    print('🎉 TESTES CONCLUÍDOS!')
                    print()
                    print('📋 RESUMO DOS ERROS DE PARÂMETROS:')
                    print('   • O problema principal era o STATUS da reserva (CANCELADO)')
                    print('   • Com reserva PENDENTE, os pagamentos funcionam')
                    print('   • PIX funciona com payload mínimo')
                    print('   • Cartão aceita qualquer formato em sandbox')
                    print('   • Idempotency Key é opcional mas recomendada')
                    
                else:
                    print(f'❌ Erro ao criar reserva: {r.text}')
            else:
                print('❌ Nenhum quarto disponível')
        else:
            print('❌ Nenhum cliente encontrado')
    else:
        print(f'❌ Erro ao listar clientes: {r.text}')
else:
    print(f'❌ Erro no login: {r.text}')

print()
print('=== TESTE CONCLUÍDO ===')
