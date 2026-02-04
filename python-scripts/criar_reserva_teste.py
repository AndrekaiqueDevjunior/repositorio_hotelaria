#!/usr/bin/env python3

import requests
import json

# Criar reserva de teste com status HOSPEDADO para testar checkout
reserva_teste = {
    "cliente_id": 1,
    "quarto_numero": "101",
    "tipo_suite": "LUXO",
    "checkin_previsto": "2026-01-05T15:00:00Z",
    "checkout_previsto": "2026-01-08T12:00:00Z",
    "valor_diaria": 350.00,
    "num_diarias": 3,
    "status_reserva": "HOSPEDADO"  # Forçar status HOSPEDADO para teste
}

try:
    response = requests.post(
        "http://localhost:8000/api/v1/reservas",
        json=reserva_teste,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 201:
        print("✅ Reserva HOSPEDADA criada com sucesso!")
        print(f"ID: {response.json().get('id')}")
        print(f"Código: {response.json().get('codigo_reserva')}")
    else:
        print(f"❌ Erro: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"❌ Erro de conexão: {e}")
    print("Verifique se o backend está rodando em http://localhost:8000")
