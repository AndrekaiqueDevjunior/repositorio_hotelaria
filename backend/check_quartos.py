#!/usr/bin/env python3

import requests

def verificar_quartos_disponiveis():
    """Verificar quartos disponíveis no sistema"""
    
    base_url = "http://backend:8000"
    
    # Login
    login_data = {'email': 'admin@hotelreal.com.br', 'password': 'admin123'}
    login_resp = requests.post(f'{base_url}/api/v1/login', json=login_data)
    refresh_token = login_resp.json().get('refresh_token')
    refresh_data = {'refresh_token': refresh_token}
    access_resp = requests.post(f'{base_url}/api/v1/refresh', json=refresh_data)
    token = access_resp.json().get('access_token')
    headers = {'Authorization': f'Bearer {token}'}
    
    # Listar quartos
    quartos_resp = requests.get(f'{base_url}/api/v1/quartos', headers=headers)
    print('Quartos Status:', quartos_resp.status_code)
    
    if quartos_resp.status_code == 200:
        quartos = quartos_resp.json()
        print('Resposta completa:', quartos)
        print('Quartos disponíveis:')
        for quarto in quartos.get('data', [])[:10]:
            print(f'  ID: {quarto.get("id")} - Nº: {quarto.get("numero")} - Tipo: {quarto.get("tipo_suite")} - Status: {quarto.get("status")}')
    else:
        print('Erro:', quartos_resp.text[:200])

if __name__ == "__main__":
    verificar_quartos_disponiveis()
