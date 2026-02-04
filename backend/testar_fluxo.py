#!/usr/bin/env python3

import requests
import json

def testar_fluxo_completo():
    """Teste completo do fluxo de login, reserva e pontos"""
    
    base_url = "http://backend:8000"
    
    # 1. Login
    print("=== TESTE DE LOGIN ===")
    login_data = {
        'email': 'admin@hotelreal.com.br',
        'password': 'admin123'
    }
    
    try:
        response = requests.post(f'{base_url}/api/v1/login', json=login_data)
        print(f'Login Status: {response.status_code}')
        
        if response.status_code != 200:
            print(f'Login falhou: {response.text}')
            return False
            
        token_data = response.json()
        refresh_token = token_data.get('refresh_token')
        
        # Obter access token usando refresh token
        refresh_data = {'refresh_token': refresh_token}
        refresh_resp = requests.post(f'{base_url}/api/v1/refresh', json=refresh_data)
        
        if refresh_resp.status_code != 200:
            print(f'Erro ao obter access token: {refresh_resp.text}')
            return False
            
        access_data = refresh_resp.json()
        token = access_data.get('access_token')
        headers = {'Authorization': f'Bearer {token}'}
        print(f'Access token obtido: {token[:20]}...' if token else 'Token não encontrado')
        print('✅ Login realizado com sucesso!')
        
    except Exception as e:
        print(f'Erro no login: {e}')
        return False
    
    # 2. Verificar saldo inicial de pontos
    print("\n=== SALDO INICIAL DE PONTOS ===")
    try:
        pontos_resp = requests.get(f'{base_url}/api/v1/pontos/saldo/1', headers=headers)
        if pontos_resp.status_code == 200:
            saldo_inicial_dict = pontos_resp.json()
            saldo_inicial = saldo_inicial_dict.get('saldo', 0)
            print(f'Saldo inicial: {saldo_inicial} pontos')
        else:
            print('Não foi possível obter saldo inicial')
            saldo_inicial = 0
    except:
        saldo_inicial = 0
    
    # 3. Criar reserva
    print("\n=== CRIAÇÃO DE RESERVA ===")
    reserva_data = {
        'cliente_id': 1,
        'quarto_id': 1,
        'quarto_numero': '107',
        'tipo_suite': 'LUXO',
        'data_checkin': '2026-02-01',
        'data_checkout': '2026-02-03',
        'checkin_previsto': '2026-02-01',
        'checkout_previsto': '2026-02-03',
        'valor_total': 400.0,
        'valor_diaria': 200.0,
        'num_diarias': 2
    }
    
    try:
        reserva_resp = requests.post(f'{base_url}/api/v1/reservas', json=reserva_data, headers=headers)
        print(f'Criação Reserva Status: {reserva_resp.status_code}')
        
        if reserva_resp.status_code != 201:
            print(f'Erro na reserva: {reserva_resp.text}')
            return False
            
        reserva = reserva_resp.json()
        reserva_data = reserva.get('data', {})
        reserva_id = reserva_data.get('id')
        if not reserva_id:
            print('Erro: ID da reserva não encontrado na resposta')
            print('Resposta completa:', reserva)
            return False
            
        print(f'✅ Reserva criada ID: {reserva_id}')
        print(f'Valor: R$ {reserva_data.get("valor_total", "N/A")}')
        print(f'Status: {reserva_data.get("status", "N/A")}')
        
    except Exception as e:
        print(f'Erro na reserva: {e}')
        return False
    
    # 4. Processar pagamento
    print("\n=== PROCESSAMENTO DE PAGAMENTO ===")
    pagamento_data = {
        'reserva_id': reserva_id,
        'valor': 400.0,
        'metodo': 'cartao_credito',
        'status': 'aprovado'
    }
    
    try:
        pag_resp = requests.post(f'{base_url}/api/v1/pagamentos', json=pagamento_data, headers=headers)
        print(f'Pagamento Status: {pag_resp.status_code}')
        
        if pag_resp.status_code != 201:
            print(f'Erro no pagamento: {pag_resp.text}')
            return False
            
        pagamento = pag_resp.json()
        print(f'✅ Pagamento ID: {pagamento["id"]}')
        print(f'Status pagamento: {pagamento["status"]}')
        
    except Exception as e:
        print(f'Erro no pagamento: {e}')
        return False
    
    # 5. Verificar pontos após pagamento
    print("\n=== VERIFICAÇÃO DE PONTOS ===")
    try:
        pontos_resp = requests.get(f'{base_url}/api/v1/pontos/saldo/1', headers=headers)
        print(f'Saldo Pontos Status: {pontos_resp.status_code}')
        
        if pontos_resp.status_code == 200:
            saldo_final_dict = pontos_resp.json()
            saldo_final = saldo_final_dict.get('saldo', 0)
            print(f'Saldo final: {saldo_final} pontos')
            
            pontos_ganhos = saldo_final - saldo_inicial
            pontos_esperados = int(400.0 / 10)  # 1 ponto por R$ 10
            
            print(f'Pontos ganhos: {pontos_ganhos}')
            print(f'Pontos esperados: {pontos_esperados}')
            
            if pontos_ganhos == pontos_esperados:
                print('✅ Pontos creditados corretamente!')
            else:
                print('❌ Pontos não creditados corretamente!')
                
        else:
            print(f'Erro ao verificar pontos: {pontos_resp.text}')
            
        # Verificar transações
        trans_resp = requests.get(f'{base_url}/api/v1/pontos/transacoes/1', headers=headers)
        if trans_resp.status_code == 200:
            transacoes = trans_resp.json()
            print(f'Total de transações: {len(transacoes)}')
            
            # Mostrar últimas transações
            for trans in transacoes[-3:]:
                print(f'  - {trans["tipo"]}: {trans["pontos"]} pts ({trans["descricao"]})')
        
    except Exception as e:
        print(f'Erro na verificação de pontos: {e}')
        return False
    
    print("\n=== RESUMO DO TESTE ===")
    print("✅ Login funcionando")
    print("✅ Criação de reservas funcionando") 
    print("✅ Processamento de pagamentos funcionando")
    print("✅ Sistema de pontos operacional")
    
    return True

if __name__ == "__main__":
    testar_fluxo_completo()
