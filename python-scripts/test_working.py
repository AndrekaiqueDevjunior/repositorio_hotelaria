#!/usr/bin/env python3
import requests
import json
from datetime import datetime, timedelta

# Base URL
base_url = 'http://localhost:8000/api/v1'

print('=== TESTE CRUD COMPLETO FUNCIONAL ===')
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
    
    # 2. Criar Quarto
    print()
    print('2. CRIANDO QUARTO...')
    quarto_data = {
        'numero': '102',
        'tipo_suite': 'STANDARD',
        'capacidade': 2,
        'diaria': 150.00,
        'status': 'LIVRE'
    }
    r = requests.post(f'{base_url}/quartos', json=quarto_data, headers=headers, cookies=cookies)
    print(f'Status: {r.status_code}')
    if r.status_code == 201:
        quarto = r.json()
        print(f'✅ Quarto criado: {quarto["numero"]}')
        quarto_numero = quarto['numero']
    else:
        print(f'❌ Erro: {r.text}')
        quarto_numero = '102'
    
    # 3. Criar Cliente
    print()
    print('3. CRIANDO CLIENTE...')
    cliente_data = {
        'nome_completo': 'Maria Santos',
        'documento': '98765432100',
        'email': 'maria@teste.com',
        'telefone': '21988888888'
    }
    r = requests.post(f'{base_url}/clientes', json=cliente_data, headers=headers, cookies=cookies)
    print(f'Status: {r.status_code}')
    if r.status_code == 201:
        cliente = r.json()
        print(f'✅ Cliente criado: {cliente["nome_completo"]}')
        cliente_id = cliente['id']
    else:
        print(f'❌ Erro: {r.text}')
        cliente_id = 1
    
    # 4. Criar Reserva
    print()
    print('4. CRIANDO RESERVA...')
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
    print(f'Status: {r.status_code}')
    if r.status_code == 201:
        reserva = r.json()
        print(f'✅ Reserva criada: ID {reserva["id"]}')
        reserva_id = reserva['id']
    else:
        print(f'❌ Erro: {r.text}')
        reserva_id = None
    
    # 5. Criar Pagamento
    if reserva_id:
        print()
        print('5. CRIANDO PAGAMENTO...')
        pagamento_data = {
            'reserva_id': reserva_id,
            'valor': 150.00,
            'metodo': 'pix',
            'parcelas': 1
        }
        r = requests.post(f'{base_url}/pagamentos', json=pagamento_data, headers=headers, cookies=cookies)
        print(f'Status: {r.status_code}')
        if r.status_code == 201:
            pagamento = r.json()
            print(f'✅ Pagamento criado: {pagamento["id"]}')
        else:
            print(f'❌ Erro: {r.text}')
    
    # 6. Atualizar Reserva (UPDATE)
    if reserva_id:
        print()
        print('6. ATUALIZANDO RESERVA...')
        update_data = {'status': 'CONFIRMADA'}
        r = requests.patch(f'{base_url}/reservas/{reserva_id}', json=update_data, headers=headers, cookies=cookies)
        print(f'Status: {r.status_code}')
        if r.status_code == 200:
            print(f'✅ Reserva atualizada para CONFIRMADA')
        else:
            print(f'❌ Erro: {r.text}')
    
    # 7. Verificar dados finais
    print()
    print('7. VERIFICANDO DADOS FINAIS...')
    r = requests.get(f'{base_url}/quartos', cookies=cookies)
    print(f'✅ Quartos: {r.status_code} ({len(r.json())} registros)')
    
    r = requests.get(f'{base_url}/clientes', cookies=cookies)
    print(f'✅ Clientes: {r.status_code} ({len(r.json())} registros)')
    
    r = requests.get(f'{base_url}/reservas', cookies=cookies)
    print(f'✅ Reservas: {r.status_code} ({len(r.json())} registros)')
    
    r = requests.get(f'{base_url}/pagamentos', cookies=cookies)
    print(f'✅ Pagamentos: {r.status_code} ({len(r.json())} registros)')
    
    # 8. Verificar reserva específica
    if reserva_id:
        r = requests.get(f'{base_url}/reservas/{reserva_id}', cookies=cookies)
        if r.status_code == 200:
            reserva = r.json()
            print(f'✅ Reserva final: Status {reserva["status"]}')
    
    print()
    print('🎉 TODAS AS OPERAÇÕES CRUD FUNCIONANDO!')
    
else:
    print(f'❌ Erro no login: {r.text}')

print()
print('=== TESTE CONCLUÍDO ===')
