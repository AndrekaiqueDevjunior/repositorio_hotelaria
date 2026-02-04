#!/usr/bin/env python3

import requests

def cancelar_reserva_cliente():
    """Cancelar reserva existente do cliente 1"""
    
    base_url = "http://backend:8000"
    
    # Login
    login_data = {'email': 'admin@hotelreal.com.br', 'password': 'admin123'}
    login_resp = requests.post(f'{base_url}/api/v1/login', json=login_data)
    refresh_token = login_resp.json().get('refresh_token')
    refresh_data = {'refresh_token': refresh_token}
    access_resp = requests.post(f'{base_url}/api/v1/refresh', json=refresh_data)
    token = access_resp.json().get('access_token')
    headers = {'Authorization': f'Bearer {token}'}
    
    # Buscar reservas do cliente 1
    reservas_resp = requests.get(f'{base_url}/api/v1/reservas/cliente/1', headers=headers)
    print('Reservas cliente:', reservas_resp.status_code)
    
    if reservas_resp.status_code == 200:
        reservas = reservas_resp.json()
        print('Reservas encontradas:', len(reservas) if isinstance(reservas, list) else len(reservas.get('data', [])))
        
        lista_reservas = reservas if isinstance(reservas, list) else reservas.get('data', [])
        for res in lista_reservas:
            print(f'  ID: {res.get("id")} - Código: {res.get("codigo_reserva")} - Status: {res.get("status")}')
            
            # Cancelar primeira reserva encontrada
            reserva_id = res.get('id')
            cancel_resp = requests.delete(f'{base_url}/api/v1/reservas/{reserva_id}', headers=headers)
            print(f'  Cancelamento Status: {cancel_resp.status_code}')
            if cancel_resp.status_code == 204:
                print('  ✅ Reserva cancelada com sucesso!')
            else:
                print(f'  Erro cancelamento: {cancel_resp.text[:100]}')
    else:
        print('Erro ao buscar reservas:', reservas_resp.text[:200])

if __name__ == "__main__":
    cancelar_reserva_cliente()
