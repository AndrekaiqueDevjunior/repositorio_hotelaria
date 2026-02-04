#!/usr/bin/env python3
import requests
import json

# Base URL
base_url = 'http://localhost:8000/api/v1'

print('=== TESTE CRUD COMPLETO ===')
print()

# 1. Fazer Login e obter cookie
print('1. FAZENDO LOGIN...')
login_data = {
    'email': 'admin@hotelreal.com.br',
    'password': 'admin123'
}

r = requests.post(f'{base_url}/login', json=login_data)
print(f'Status: {r.status_code}')

if r.status_code == 200:
    print('✅ Login bem-sucedido')
    # Obter cookie
    cookies = r.cookies.get_dict()
    print(f'Cookies: {cookies}')
    
    # Usar cookie nas requisições seguintes
    headers = {'Content-Type': 'application/json'}
    
    # 2. Criar Quarto
    print()
    print('2. CRIANDO QUARTO...')
    quarto_data = {
        'numero': '101',
        'tipo': 'STANDARD',
        'capacidade': 2,
        'diaria': 150.00,
        'status': 'DISPONIVEL'
    }
    r = requests.post(f'{base_url}/quartos', json=quarto_data, headers=headers, cookies=cookies)
    print(f'Status: {r.status_code}')
    if r.status_code == 201:
        quarto = r.json()
        print(f'✅ Quarto criado: {quarto["numero"]}')
        quarto_numero = quarto['numero']
    else:
        print(f'❌ Erro: {r.text}')
        quarto_numero = '101'
    
    # 3. Criar Cliente
    print()
    print('3. CRIANDO CLIENTE...')
    cliente_data = {
        'nome': 'João Silva',
        'documento': '12345678901',
        'email': 'joao@teste.com',
        'telefone': '21999999999'
    }
    r = requests.post(f'{base_url}/clientes', json=cliente_data, headers=headers, cookies=cookies)
    print(f'Status: {r.status_code}')
    if r.status_code == 201:
        cliente = r.json()
        print(f'✅ Cliente criado: {cliente["nome"]}')
        cliente_id = cliente['id']
    else:
        print(f'❌ Erro: {r.text}')
        cliente_id = 1
    
    # 4. Listar dados
    print()
    print('4. VERIFICANDO DADOS...')
    r = requests.get(f'{base_url}/quartos', cookies=cookies)
    print(f'Quartos: {r.status_code} ({len(r.json())} registros)')
    
    r = requests.get(f'{base_url}/clientes', cookies=cookies)
    print(f'Clientes: {r.status_code} ({len(r.json())} registros)')
    
    r = requests.get(f'{base_url}/reservas', cookies=cookies)
    print(f'Reservas: {r.status_code} ({len(r.json())} registros)')
    
else:
    print(f'❌ Erro no login: {r.text}')

print()
print('=== TESTE CONCLUÍDO ===')
