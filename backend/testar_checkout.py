#!/usr/bin/env python3

import requests
import json

# Login para obter token
login_data = {
    "email": "admin@hotelreal.com.br",
    "password": "admin123"
}

print("🔐 Fazendo login...")
try:
    login_response = requests.post(
        "http://localhost:8000/api/v1/auth/login",
        json=login_data,
        headers={"Content-Type": "application/json"}
    )
    
    if login_response.status_code == 200:
        token = login_response.json().get("access_token")
        print("✅ Login successful!")
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Criar reserva CONFIRMADA primeiro
        reserva_data = {
            "cliente_id": 1,
            "quarto_numero": "101",
            "tipo_suite": "LUXO",
            "checkin_previsto": "2026-01-05T15:00:00Z",
            "checkout_previsto": "2026-01-08T12:00:00Z",
            "valor_diaria": 350.00,
            "num_diarias": 3
        }
        
        print("📋 Criando reserva CONFIRMADA...")
        reserva_response = requests.post(
            "http://localhost:8000/api/v1/reservas",
            json=reserva_data,
            headers=headers
        )
        
        if reserva_response.status_code == 201:
            reserva = reserva_response.json()
            reserva_id = reserva.get("id")
            print(f"✅ Reserva criada: ID {reserva_id}, Status: {reserva.get('status')}")
            
            # Simular check-in para mudar status para HOSPEDADO
            print("🔑 Simulando check-in...")
            checkin_data = {
                "hospede_titular_nome": "Teste Checkout",
                "hospede_titular_documento": "123456789",
                "num_hospedes_real": 1,
                "caucao_cobrada": 200.00,
                "documentos_conferidos": True,
                "pagamento_validado": True,
                "termos_aceitos": True
            }
            
            checkin_response = requests.post(
                f"http://localhost:8000/api/v1/reservas/{reserva_id}/checkin",
                json=checkin_data,
                headers=headers
            )
            
            if checkin_response.status_code == 200:
                print("✅ Check-in realizado! Status deve ser HOSPEDADO")
                
                # Verificar status atual
                status_response = requests.get(
                    f"http://localhost:8000/api/v1/reservas/{reserva_id}",
                    headers=headers
                )
                
                if status_response.status_code == 200:
                    status_atual = status_response.json().get("status")
                    print(f"📊 Status atual da reserva: {status_atual}")
                    
                    if status_atual == "HOSPEDADO":
                        print("🎯 PERFEITO! Agora o botão CHECKOUT deve aparecer no frontend!")
                        print("📱 Acesse http://localhost:3000/dashboard/reservas para testar")
                    else:
                        print(f"❌ Status inesperado: {status_atual}")
                        
            else:
                print(f"❌ Erro no check-in: {checkin_response.status_code}")
                print(checkin_response.text)
                
        else:
            print(f"❌ Erro ao criar reserva: {reserva_response.status_code}")
            print(reserva_response.text)
            
    else:
        print(f"❌ Erro no login: {login_response.status_code}")
        print(login_response.text)
        
except Exception as e:
    print(f"❌ Erro: {e}")
    print("Verifique se o backend está rodando em http://localhost:8000")
