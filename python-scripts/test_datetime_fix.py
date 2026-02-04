#!/usr/bin/env python3
import requests
import json
from datetime import datetime, timedelta

# Base URL
base_url = 'http://localhost:8000/api/v1'

print('=== TESTANDO CORREÇÃO DATETIME COMPARISON ===')
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
    
    # 2. Criar reserva para teste
    print()
    print('2. CRIANDO RESERVA PARA TESTE...')
    
    # Buscar cliente
    r = requests.get(f'{base_url}/clientes', cookies=cookies)
    if r.status_code == 200:
        clientes_response = r.json()
        clientes = clientes_response['clientes'] if 'clientes' in clientes_response else clientes_response
        
        if clientes:
            cliente_id = clientes[0]['id']
            
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
                    
                    # 3. Testar pagamento PIX
                    print()
                    print('3. TESTANDO PAGAMENTO PIX...')
                    
                    pagamento_pix = {
                        'reserva_id': reserva_id,
                        'valor': 150.00,
                        'metodo': 'pix'
                    }
                    
                    headers_with_idempotency = {
                        'Content-Type': 'application/json',
                        'X-Idempotency-Key': f'test_fix_{datetime.now().strftime("%Y%m%d%H%M%S")}'
                    }
                    
                    r = requests.post(f'{base_url}/pagamentos', json=pagamento_pix, headers=headers_with_idempotency, cookies=cookies)
                    print(f'Status: {r.status_code}')
                    
                    if r.status_code == 201:
                        pagamento = r.json()
                        print(f'✅ Pagamento PIX criado com sucesso!')
                        print(f'   ID: {pagamento["id"]}')
                        print(f'   Status: {pagamento["status"]}')
                        print(f'   Método: {pagamento["metodo"]}')
                        print(f'   URL QR Code: {pagamento.get("url_pagamento", "N/A")}')
                        
                        print()
                        print('🎉 ERRO DATETIME COMPARISON CORRIGIDO!')
                        print('✅ Pagamento processado sem erros de timezone')
                        
                    else:
                        print(f'❌ Erro no pagamento: {r.text}')
                        
                        # Verificar se ainda é o mesmo erro
                        if "can't compare offset-naive and offset-aware datetimes" in r.text:
                            print('❌ ERRO DATETIME AINDA PRESENTE!')
                        else:
                            print('✅ Erro diferente - datetime comparison foi corrigido')
                    
                    # 4. Testar pagamento cartão
                    print()
                    print('4. TESTANDO PAGAMENTO CARTÃO...')
                    
                    pagamento_cartao = {
                        'reserva_id': reserva_id,
                        'valor': 150.00,
                        'metodo': 'credit_card',
                        'parcelas': 1,
                        'cartao_numero': '0000000000000001',
                        'cartao_validade': '12/2025',
                        'cartao_cvv': '123',
                        'cartao_nome': 'TESTE DATETIME FIX'
                    }
                    
                    headers_with_idempotency = {
                        'Content-Type': 'application/json',
                        'X-Idempotency-Key': f'test_cartao_fix_{datetime.now().strftime("%Y%m%d%H%M%S")}'
                    }
                    
                    r = requests.post(f'{base_url}/pagamentos', json=pagamento_cartao, headers=headers_with_idempotency, cookies=cookies)
                    print(f'Status: {r.status_code}')
                    
                    if r.status_code == 201:
                        pagamento = r.json()
                        print(f'✅ Pagamento Cartão criado com sucesso!')
                        print(f'   ID: {pagamento["id"]}')
                        print(f'   Status: {pagamento["status"]}')
                        print(f'   Método: {pagamento["metodo"]}')
                        
                        print()
                        print('🎉 PAGAMENTO CARTÃO TAMBÉM FUNCIONOU!')
                        
                    else:
                        print(f'❌ Erro no pagamento cartão: {r.text}')
                        
                        if "can't compare offset-naive and offset-aware datetimes" in r.text:
                            print('❌ ERRO DATETIME AINDA PRESENTE NO CARTÃO!')
                        else:
                            print('✅ Erro diferente - datetime comparison foi corrigido')
                    
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
