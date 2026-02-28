#!/usr/bin/env python3
import requests
import json
from datetime import datetime

# Base URL
base_url = 'http://localhost:8000/api/v1'

print('=== TESTANDO PAGAMENTO CIELO SANDBOX ===')
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
    print('2. BUSCANDO CLIENTE PARA TESTE...')
    r = requests.get(f'{base_url}/clientes', cookies=cookies)
    
    if r.status_code == 200:
        clientes_response = r.json()
        clientes = clientes_response['clientes'] if 'clientes' in clientes_response else clientes_response
        
        if clientes:
            cliente_id = clientes[0]['id']
            print(f'✅ Cliente encontrado: {clientes[0].get("nome_completo", "N/A")} (ID: {cliente_id})')
            
            # 3. Criar uma reserva para teste
            print()
            print('3. CRIANDO RESERVA PARA TESTE...')
            
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
                    print(f'✅ Reserva criada: ID {reserva_id}')
                    
                    # 4. Testar pagamento com diferentes parâmetros
                    print()
                    print('4. TESTANDO PAGAMENTOS...')
                    
                    # Teste 1: Pagamento completo (cartão)
                    print()
                    print('4.1 TESTE - Pagamento Cartão Crédito (Completo):')
                    pagamento_cartao = {
                        'reserva_id': reserva_id,
                        'valor': 150.00,
                        'metodo': 'credit_card',
                        'parcelas': 1,
                        'cartao_numero': '0000000000000001',  // Cartão teste sandbox
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
                        print(f'   ✅ Pagamento criado: ID {pagamento["id"]}')
                        print(f'   Status: {pagamento["status"]}')
                        print(f'   Método: {pagamento["metodo"]}')
                    else:
                        print(f'   ❌ Erro: {r.text}')
                    
                    # Teste 2: Pagamento com parâmetros faltando
                    print()
                    print('4.2 TESTE - Pagamento com Parâmetros Faltando:')
                    pagamento_incompleto = {
                        'reserva_id': reserva_id,
                        'valor': 150.00,
                        'metodo': 'credit_card'
                        // Faltando: cartao_numero, cartao_validade, etc.
                    }
                    
                    headers_with_idempotency = {
                        'Content-Type': 'application/json',
                        'X-Idempotency-Key': f'test_incompleto_{datetime.now().strftime("%Y%m%d%H%M%S")}'
                    }
                    
                    r = requests.post(f'{base_url}/pagamentos', json=pagamento_incompleto, headers=headers_with_idempotency, cookies=cookies)
                    print(f'   Status: {r.status_code}')
                    
                    if r.status_code != 201:
                        print(f'   ❌ Erro esperado: {r.text}')
                    else:
                        print(f'   ⚠️  Pagamento criado inesperadamente')
                    
                    # Teste 3: Pagamento PIX
                    print()
                    print('4.3 TESTE - Pagamento PIX:')
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
                        print(f'   URL QR Code: {pagamento.get("url_pagamento", "N/A")}')
                    else:
                        print(f'   ❌ Erro: {r.text}')
                    
                    # Teste 4: Pagamento com valor inválido
                    print()
                    print('4.4 TESTE - Pagamento com Valor Inválido:')
                    pagamento_invalido = {
                        'reserva_id': reserva_id,
                        'valor': -50.00,  // Valor negativo
                        'metodo': 'credit_card',
                        'cartao_numero': '0000000000000001',
                        'cartao_validade': '12/2025',
                        'cartao_cvv': '123',
                        'cartao_nome': 'TESTE SANDBOX'
                    }
                    
                    headers_with_idempotency = {
                        'Content-Type': 'application/json',
                        'X-Idempotency-Key': f'test_invalido_{datetime.now().strftime("%Y%m%d%H%M%S")}'
                    }
                    
                    r = requests.post(f'{base_url}/pagamentos', json=pagamento_invalido, headers=headers_with_idempotency, cookies=cookies)
                    print(f'   Status: {r.status_code}')
                    
                    if r.status_code != 201:
                        print(f'   ❌ Erro esperado: {r.text}')
                    else:
                        print(f'   ⚠️  Pagamento criado inesperadamente')
                    
                    # Teste 5: Pagamento sem idempotency key
                    print()
                    print('4.5 TESTE - Pagamento sem Idempotency Key:')
                    pagamento_sem_key = {
                        'reserva_id': reserva_id,
                        'valor': 150.00,
                        'metodo': 'pix'
                    }
                    
                    r = requests.post(f'{base_url}/pagamentos', json=pagamento_sem_key, headers=headers, cookies=cookies)
                    print(f'   Status: {r.status_code}')
                    
                    if r.status_code == 201:
                        pagamento = r.json()
                        print(f'   ✅ Pagamento criado sem idempotency: ID {pagamento["id"]}')
                    else:
                        print(f'   ❌ Erro: {r.text}')
                    
                    print()
                    print('🎉 TESTES CONCLUÍDOS!')
                    print()
                    print('📋 RESUMO DOS TESTES:')
                    print('   1. Pagamento cartão completo: Verificado')
                    print('   2. Pagamento parâmetros faltando: Verificado')
                    print('   3. Pagamento PIX: Verificado')
                    print('   4. Valor inválido: Verificado')
                    print('   5. Sem idempotency key: Verificado')
                    
                else:
                    print(f'❌ Erro ao criar reserva: {r.text}')
            else:
                print('❌ Nenhum quarto disponível encontrado')
        else:
            print('❌ Nenhum cliente encontrado')
    else:
        print(f'❌ Erro ao listar clientes: {r.text}')
else:
    print(f'❌ Erro no login: {r.text}')

print()
print('=== TESTE CONCLUÍDO ===')
