#!/usr/bin/env python3
import requests
import json

# Base URL
base_url = 'http://localhost:8000/api/v1'

print('=== TESTANDO ENDPOINTS DE PONTOS ===')
print()

# 1. Fazer Login
print('1. FAZENDO LOGIN...')
login_data = {'email': 'admin@hotelreal.com.br', 'password': 'admin123'}
r = requests.post(f'{base_url}/login', json=login_data)
print(f'Status: {r.status_code}')

if r.status_code == 200:
    print('✅ Login bem-sucedido')
    cookies = r.cookies.get_dict()
    
    # 2. Listar clientes
    print()
    print('2. LISTANDO CLIENTES...')
    r = requests.get(f'{base_url}/clientes', cookies=cookies)
    print(f'Status: {r.status_code}')
    
    if r.status_code == 200:
        clientes_response = r.json()
        clientes = clientes_response['clientes'] if 'clientes' in clientes_response else clientes_response
        
        if clientes:
            cliente_id = clientes[0]['id']
            print(f'✅ Usando cliente: {clientes[0].get("nome_completo", "N/A")} (ID: {cliente_id})')
            
            # 3. Testar saldo
            print()
            print('3. TESTANDO SALDO...')
            r = requests.get(f'{base_url}/pontos/saldo/{cliente_id}', cookies=cookies)
            print(f'Status: {r.status_code}')
            if r.status_code == 200:
                saldo = r.json()
                print(f'✅ Saldo: {saldo}')
            else:
                print(f'❌ Erro: {r.text}')
            
            # 4. Testar histórico
            print()
            print('4. TESTANDO HISTÓRICO...')
            r = requests.get(f'{base_url}/pontos/historico/{cliente_id}?limit=10', cookies=cookies)
            print(f'Status: {r.status_code}')
            if r.status_code == 200:
                historico = r.json()
                print(f'✅ Histórico: {len(historico.get("transacoes", []))} transações')
                if historico.get("transacoes"):
                    print(f'   Primeira transação: {historico["transacoes"][0]}')
            else:
                print(f'❌ Erro: {r.text}')
            
            # 5. Testar estatísticas
            print()
            print('5. TESTANDO ESTATÍSTICAS...')
            r = requests.get(f'{base_url}/pontos/estatisticas', cookies=cookies)
            print(f'Status: {r.status_code}')
            if r.status_code == 200:
                stats = r.json()
                print(f'✅ Estatísticas: {stats}')
            else:
                print(f'❌ Erro: {r.text}')
                
        else:
            print('❌ Nenhum cliente encontrado')
    else:
        print(f'❌ Erro ao listar clientes: {r.text}')
else:
    print(f'❌ Erro no login: {r.text}')

print()
print('=== TESTE CONCLUÍDO ===')
