#!/usr/bin/env python3
import requests
import json
from datetime import datetime, timedelta

# Base URL
base_url = 'http://localhost:8000/api/v1'

print('=== TESTE CRUD COMPLETO ===')
print()

# 1. Criar Quarto
print('1. CRIANDO QUARTO...')
quarto_data = {
    'numero': '101',
    'tipo': 'STANDARD',
    'capacidade': 2,
    'diaria': 150.00,
    'status': 'DISPONIVEL'
}
try:
    r = requests.post(f'{base_url}/quartos', json=quarto_data)
    print(f'Status: {r.status_code}')
    if r.status_code == 201:
        quarto = r.json()
        print(f'Quarto criado: {quarto["numero"]}')
        quarto_numero = quarto['numero']
    else:
        print(f'Erro: {r.text}')
        quarto_numero = '101'
except Exception as e:
    print(f'Erro: {e}')
    quarto_numero = '101'

print()

# 2. Criar Cliente
print('2. CRIANDO CLIENTE...')
cliente_data = {
    'nome': 'João Silva',
    'documento': '12345678901',
    'email': 'joao@teste.com',
    'telefone': '21999999999'
}
try:
    r = requests.post(f'{base_url}/clientes', json=cliente_data)
    print(f'Status: {r.status_code}')
    if r.status_code == 201:
        cliente = r.json()
        print(f'Cliente criado: {cliente["nome"]}')
        cliente_id = cliente['id']
    else:
        print(f'Erro: {r.text}')
        cliente_id = 1
except Exception as e:
    print(f'Erro: {e}')
    cliente_id = 1

print()

# 3. Criar Reserva
print('3. CRIANDO RESERVA...')
amanha = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
depois_amanha = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')

reserva_data = {
    'cliente_id': cliente_id,
    'quarto_numero': quarto_numero,
    'data_checkin': amanha,
    'data_checkout': depois_amanha,
    'valor_total': 150.00
}
try:
    r = requests.post(f'{base_url}/reservas', json=reserva_data)
    print(f'Status: {r.status_code}')
    if r.status_code == 201:
        reserva = r.json()
        print(f'Reserva criada: ID {reserva["id"]}')
        reserva_id = reserva['id']
    else:
        print(f'Erro: {r.text}')
        reserva_id = None
except Exception as e:
    print(f'Erro: {e}')
    reserva_id = None

print()

# 4. Criar Pagamento
if reserva_id:
    print('4. CRIANDO PAGAMENTO...')
    pagamento_data = {
        'reserva_id': reserva_id,
        'valor': 150.00,
        'metodo': 'pix',
        'parcelas': 1
    }
    try:
        r = requests.post(f'{base_url}/pagamentos', json=pagamento_data)
        print(f'Status: {r.status_code}')
        if r.status_code == 201:
            pagamento = r.json()
            print(f'Pagamento criado: {pagamento["id"]}')
        else:
            print(f'Erro: {r.text}')
    except Exception as e:
        print(f'Erro: {e}')

print()

# 5. Listar todos os dados
print('5. VERIFICANDO DADOS CRIADOS...')
try:
    # Listar quartos
    r = requests.get(f'{base_url}/quartos')
    print(f'Quartos: {r.status_code} ({len(r.json())} registros)')
    
    # Listar clientes
    r = requests.get(f'{base_url}/clientes')
    print(f'Clientes: {r.status_code} ({len(r.json())} registros)')
    
    # Listar reservas
    r = requests.get(f'{base_url}/reservas')
    print(f'Reservas: {r.status_code} ({len(r.json())} registros)')
    
except Exception as e:
    print(f'Erro: {e}')

print()
print('=== TESTE CONCLUÍDO ===')
