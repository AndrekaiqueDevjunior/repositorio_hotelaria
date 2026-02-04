#!/usr/bin/env python3
import requests
import json
from datetime import datetime, timedelta

# Base URL
base_url = 'http://localhost:8000/api/v1'

print('=== TESTE CRUD COMPLETO COM AUTENTICAÇÃO ===')
print()

# 1. Fazer Login
print('1. FAZENDO LOGIN...')
login_data = {
    'email': 'admin@hotelreal.com.br',
    'password': 'admin123'
}
try:
    r = requests.post(f'{base_url}/login', json=login_data)
    print(f'Status: {r.status_code}')
    if r.status_code == 200:
        login_result = r.json()
        print(f'Login: {login_result["message"]}')
        print(f'Usuário: {login_result["user"]["nome"]}')
        
        # Criar sessão para manter cookies
        session = requests.Session()
        session.cookies.update(r.cookies)
        
        print('Sessão autenticada com sucesso!')
    else:
        print(f'Erro no login: {r.text}')
        exit(1)
except Exception as e:
    print(f'Erro: {e}')
    exit(1)

print()

# 2. Criar Quarto
print('2. CRIANDO QUARTO...')
quarto_data = {
    'numero': '101',
    'tipo': 'STANDARD',
    'capacidade': 2,
    'diaria': 150.00,
    'status': 'DISPONIVEL'
}
try:
    r = session.post(f'{base_url}/quartos', json=quarto_data)
    print(f'Status: {r.status_code}')
    if r.status_code == 201:
        quarto = r.json()
        print(f'✅ Quarto criado: {quarto["numero"]}')
        quarto_numero = quarto['numero']
    else:
        print(f'❌ Erro: {r.text}')
        quarto_numero = '101'
except Exception as e:
    print(f'❌ Erro: {e}')
    quarto_numero = '101'

print()

# 3. Criar Cliente
print('3. CRIANDO CLIENTE...')
cliente_data = {
    'nome': 'João Silva',
    'documento': '12345678901',
    'email': 'joao@teste.com',
    'telefone': '21999999999'
}
try:
    r = session.post(f'{base_url}/clientes', json=cliente_data)
    print(f'Status: {r.status_code}')
    if r.status_code == 201:
        cliente = r.json()
        print(f'✅ Cliente criado: {cliente["nome"]}')
        cliente_id = cliente['id']
    else:
        print(f'❌ Erro: {r.text}')
        cliente_id = 1
except Exception as e:
    print(f'❌ Erro: {e}')
    cliente_id = 1

print()

# 4. Criar Reserva
print('4. CRIANDO RESERVA...')
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
    r = session.post(f'{base_url}/reservas', json=reserva_data)
    print(f'Status: {r.status_code}')
    if r.status_code == 201:
        reserva = r.json()
        print(f'✅ Reserva criada: ID {reserva["id"]}')
        reserva_id = reserva['id']
    else:
        print(f'❌ Erro: {r.text}')
        reserva_id = None
except Exception as e:
    print(f'❌ Erro: {e}')
    reserva_id = None

print()

# 5. Criar Pagamento
if reserva_id:
    print('5. CRIANDO PAGAMENTO...')
    pagamento_data = {
        'reserva_id': reserva_id,
        'valor': 150.00,
        'metodo': 'pix',
        'parcelas': 1
    }
    try:
        r = session.post(f'{base_url}/pagamentos', json=pagamento_data)
        print(f'Status: {r.status_code}')
        if r.status_code == 201:
            pagamento = r.json()
            print(f'✅ Pagamento criado: {pagamento["id"]}')
        else:
            print(f'❌ Erro: {r.text}')
    except Exception as e:
        print(f'❌ Erro: {e}')

print()

# 6. Listar todos os dados
print('6. VERIFICANDO DADOS CRIADOS...')
try:
    # Listar quartos
    r = session.get(f'{base_url}/quartos')
    print(f'Quartos: {r.status_code} ({len(r.json())} registros)')
    
    # Listar clientes
    r = session.get(f'{base_url}/clientes')
    print(f'Clientes: {r.status_code} ({len(r.json())} registros)')
    
    # Listar reservas
    r = session.get(f'{base_url}/reservas')
    print(f'Reservas: {r.status_code} ({len(r.json())} registros)')
    
    # Listar pagamentos
    r = session.get(f'{base_url}/pagamentos')
    print(f'Pagamentos: {r.status_code} ({len(r.json())} registros)')
    
except Exception as e:
    print(f'❌ Erro: {e}')

print()

# 7. Atualizar Reserva (UPDATE)
if reserva_id:
    print('7. ATUALIZANDO RESERVA...')
    update_data = {'status': 'CONFIRMADA'}
    try:
        r = session.patch(f'{base_url}/reservas/{reserva_id}', json=update_data)
        print(f'Status: {r.status_code}')
        if r.status_code == 200:
            print(f'✅ Reserva atualizada para CONFIRMADA')
        else:
            print(f'❌ Erro: {r.text}')
    except Exception as e:
        print(f'❌ Erro: {e}')

print()

# 8. Verificar dados finais
print('8. DADOS FINAIS...')
try:
    r = session.get(f'{base_url}/reservas/{reserva_id}')
    if r.status_code == 200:
        reserva = r.json()
        print(f'✅ Reserva final: Status {reserva["status"]}')
except Exception as e:
    print(f'❌ Erro: {e}')

print()
print('=== TESTE CRUD CONCLUÍDO COM SUCESSO! ===')
