#!/usr/bin/env python3
import requests
import json
from datetime import datetime

# Base URL
base_url = 'http://localhost:8000/api/v1'

print('=== TESTANDO PAGAMENTO CIELO - VERIFICACAO DE PARAMETROS ===')
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
    
    # 2. Testar diferentes cenários de pagamento
    print()
    print('2. TESTANDO CENÁRIOS DE PAGAMENTO...')
    
    # Teste 1: Payload mínimo (só campos obrigatórios)
    print()
    print('2.1 TESTE - Payload Mínimo (Apenas campos obrigatórios):')
    payload_minimo = {
        'reserva_id': 1,  # ID existente
        'valor': 150.00,
        'metodo': 'pix'
    }
    
    headers_with_idempotency = {
        'Content-Type': 'application/json',
        'X-Idempotency-Key': f'test_min_{datetime.now().strftime("%Y%m%d%H%M%S")}'
    }
    
    r = requests.post(f'{base_url}/pagamentos', json=payload_minimo, headers=headers_with_idempotency, cookies=cookies)
    print(f'   Status: {r.status_code}')
    print(f'   Response: {r.text[:200]}...' if len(r.text) > 200 else f'   Response: {r.text}')
    
    # Teste 2: Payload completo cartão
    print()
    print('2.2 TESTE - Payload Completo Cartão:')
    payload_cartao = {
        'reserva_id': 1,
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
    
    r = requests.post(f'{base_url}/pagamentos', json=payload_cartao, headers=headers_with_idempotency, cookies=cookies)
    print(f'   Status: {r.status_code}')
    print(f'   Response: {r.text[:200]}...' if len(r.text) > 200 else f'   Response: {r.text}')
    
    # Teste 3: Cartão sem dados obrigatórios
    print()
    print('2.3 TESTE - Cartão sem dados obrigatórios:')
    payload_cartao_incompleto = {
        'reserva_id': 1,
        'valor': 150.00,
        'metodo': 'credit_card'
        # Faltando: cartao_numero, cartao_validade, cartao_cvv, cartao_nome
    }
    
    headers_with_idempotency = {
        'Content-Type': 'application/json',
        'X-Idempotency-Key': f'test_incomp_{datetime.now().strftime("%Y%m%d%H%M%S")}'
    }
    
    r = requests.post(f'{base_url}/pagamentos', json=payload_cartao_incompleto, headers=headers_with_idempotency, cookies=cookies)
    print(f'   Status: {r.status_code}')
    print(f'   Response: {r.text[:200]}...' if len(r.text) > 200 else f'   Response: {r.text}')
    
    # Teste 4: Método inválido
    print()
    print('2.4 TESTE - Método inválido:')
    payload_metodo_invalido = {
        'reserva_id': 1,
        'valor': 150.00,
        'metodo': 'metodo_inexistente'
    }
    
    headers_with_idempotency = {
        'Content-Type': 'application/json',
        'X-Idempotency-Key': f'test_invalid_{datetime.now().strftime("%Y%m%d%H%M%S")}'
    }
    
    r = requests.post(f'{base_url}/pagamentos', json=payload_metodo_invalido, headers=headers_with_idempotency, cookies=cookies)
    print(f'   Status: {r.status_code}')
    print(f'   Response: {r.text[:200]}...' if len(r.text) > 200 else f'   Response: {r.text}')
    
    # Teste 5: Valor zero
    print()
    print('2.5 TESTE - Valor zero:')
    payload_zero = {
        'reserva_id': 1,
        'valor': 0.00,
        'metodo': 'pix'
    }
    
    headers_with_idempotency = {
        'Content-Type': 'application/json',
        'X-Idempotency-Key': f'test_zero_{datetime.now().strftime("%Y%m%d%H%M%S")}'
    }
    
    r = requests.post(f'{base_url}/pagamentos', json=payload_zero, headers=headers_with_idempotency, cookies=cookies)
    print(f'   Status: {r.status_code}')
    print(f'   Response: {r.text[:200]}...' if len(r.text) > 200 else f'   Response: {r.text}')
    
    # Teste 6: Reserva inexistente
    print()
    print('2.6 TESTE - Reserva inexistente:')
    payload_reserva_inexistente = {
        'reserva_id': 99999,  # ID que não existe
        'valor': 150.00,
        'metodo': 'pix'
    }
    
    headers_with_idempotency = {
        'Content-Type': 'application/json',
        'X-Idempotency-Key': f'test_reserva_{datetime.now().strftime("%Y%m%d%H%M%S")}'
    }
    
    r = requests.post(f'{base_url}/pagamentos', json=payload_reserva_inexistente, headers=headers_with_idempotency, cookies=cookies)
    print(f'   Status: {r.status_code}')
    print(f'   Response: {r.text[:200]}...' if len(r.text) > 200 else f'   Response: {r.text}')
    
    # Teste 7: Sem headers
    print()
    print('2.7 TESTE - Sem headers de autenticação:')
    payload_sem_auth = {
        'reserva_id': 1,
        'valor': 150.00,
        'metodo': 'pix'
    }
    
    r = requests.post(f'{base_url}/pagamentos', json=payload_sem_auth, headers=headers)
    print(f'   Status: {r.status_code}')
    print(f'   Response: {r.text[:200]}...' if len(r.text) > 200 else f'   Response: {r.text}')
    
    print()
    print('🎉 TESTES CONCLUÍDOS!')
    print()
    print('📋 ANÁLISE DOS ERROS:')
    print('   • Verifique os status codes e mensagens de erro')
    print('   • Compare com o schema esperado')
    print('   • Identifique campos obrigatórios faltando')
    print('   • Verifique validações de negócio')
    
else:
    print(f'❌ Erro no login: {r.text}')

print()
print('=== TESTE CONCLUÍDO ===')
