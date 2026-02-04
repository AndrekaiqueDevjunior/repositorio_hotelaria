#!/usr/bin/env python3
import requests

# Base URL
base_url = 'http://localhost:8000/api/v1'

print('=== VERIFICANDO RESERVAS EXISTENTES ===')
print()

# 1. Fazer Login
r = requests.post(f'{base_url}/login', json={'email': 'admin@hotelreal.com.br', 'password': 'admin123'})
cookies = r.cookies.get_dict()

if r.status_code == 200:
    # 2. Listar reservas
    r = requests.get(f'{base_url}/reservas', cookies=cookies)
    
    if r.status_code == 200:
        reservas = r.json()
        print(f'Total de reservas: {len(reservas)}')
        print()
        
        for res in reservas:
            print(f'ID: {res["id"]} - Status: {res["status"]} - Cliente: {res.get("clienteNome", "N/A")}')
        
        # 3. Testar pagamento com primeira reserva não cancelada
        print()
        print('=== TESTANDO PAGAMENTO COM RESERVA EXISTENTE ===')
        
        for res in reservas:
            if res["status"] not in ["CANCELADO", "CHECKED_OUT"]:
                print(f'Testando com reserva ID {res["id"]} - Status: {res["status"]}')
                
                # Testar PIX
                pagamento_pix = {
                    'reserva_id': res["id"],
                    'valor': 100.00,
                    'metodo': 'pix'
                }
                
                headers = {
                    'Content-Type': 'application/json',
                    'X-Idempotency-Key': f'test_{res["id"]}'
                }
                
                r = requests.post(f'{base_url}/pagamentos', json=pagamento_pix, headers=headers, cookies=cookies)
                print(f'Status: {r.status_code}')
                
                if r.status_code == 201:
                    pagamento = r.json()
                    print(f'✅ Pagamento criado: ID {pagamento["id"]}')
                    print(f'   Status: {pagamento["status"]}')
                    print(f'   Método: {pagamento["metodo"]}')
                    break
                else:
                    print(f'❌ Erro: {r.text}')
                    print()
    else:
        print('Erro ao listar reservas')
else:
    print('Erro no login')

print()
print('=== VERIFICACAO CONCLUÍDA ===')
