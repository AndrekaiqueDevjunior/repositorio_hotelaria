import requests
import json

# Verificar primeira página (limit=20, offset=0)
response = requests.get(
    "http://localhost:8000/api/v1/reservas",
    headers={"Cookie": "hotel_auth_token=fake-jwt-token"},
    params={"limit": 20, "offset": 0}
)

if response.status_code == 200:
    data = response.json()
    reservas = data.get("reservas", [])
    
    print(f"📄 Página 1: {len(reservas)} reservas")
    
    # Procurar CHECKED_OUT na página 1
    checkouts_page1 = [r for r in reservas if r.get("status") == "CHECKED_OUT"]
    print(f"✅ Check-outs na página 1: {len(checkouts_page1)}")
    
    if checkouts_page1:
        for checkout in checkouts_page1:
            print(f"  ID {checkout['id']}: {checkout['cliente_nome']}")
    
    # Verificar segunda página
    response2 = requests.get(
        "http://localhost:8000/api/v1/reservas",
        headers={"Cookie": "hotel_auth_token=fake-jwt-token"},
        params={"limit": 20, "offset": 20}
    )
    
    if response2.status_code == 200:
        data2 = response2.json()
        reservas2 = data2.get("reservas", [])
        
        print(f"\n📄 Página 2: {len(reservas2)} reservas")
        
        # Procurar CHECKED_OUT na página 2
        checkouts_page2 = [r for r in reservas2 if r.get("status") == "CHECKED_OUT"]
        print(f"✅ Check-outs na página 2: {len(checkouts_page2)}")
        
        if checkouts_page2:
            for checkout in checkouts_page2:
                print(f"  ID {checkout['id']}: {checkout['cliente_nome']}")
                
else:
    print(f"❌ Erro: {response.status_code}")
    print(response.text)
