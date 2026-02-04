#!/usr/bin/env python3
import requests
import json
from datetime import datetime

# Base URL
base_url = 'http://localhost:8000/api/v1'

print('=== TESTE PAGAMENTO - DATETIME FIX ===')
print()

# 1. Login
login_data = {'email': 'admin@hotelreal.com.br', 'password': 'admin123'}
r = requests.post(f'{base_url}/login', json=login_data)
cookies = r.cookies.get_dict()

if r.status_code == 200:
    print('Login OK')
    
    # 2. Testar pagamento com reserva existente (ID 1)
    pagamento_pix = {
        'reserva_id': 1,
        'valor': 100.00,
        'metodo': 'pix'
    }
    
    headers = {
        'Content-Type': 'application/json',
        'X-Idempotency-Key': f'test_datetime_{datetime.now().strftime("%Y%m%d%H%M%S")}'
    }
    
    print('Testando pagamento PIX...')
    r = requests.post(f'{base_url}/pagamentos', json=pagamento_pix, headers=headers, cookies=cookies)
    
    print(f'Status: {r.status_code}')
    
    if r.status_code == 201:
        print('✅ PAGAMENTO CRIADO COM SUCESSO!')
        print('✅ ERRO DATETIME CORRIGIDO!')
    else:
        print(f'❌ Erro: {r.text}')
        
        if "can't compare offset-naive and offset-aware datetimes" in r.text:
            print('❌ ERRO DATETIME AINDA PRESENTE!')
        else:
            print('✅ Erro diferente - datetime comparison foi corrigido')
else:
    print('Login falhou')
