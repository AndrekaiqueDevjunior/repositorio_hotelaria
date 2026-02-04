import requests
import json

# Buscar reservas
response = requests.get(
    "http://localhost:8000/api/v1/reservas",
    headers={"Cookie": "hotel_auth_token=fake-jwt-token"},
    params={"limit": 100, "offset": 0}
)

if response.status_code == 200:
    data = response.json()
    reservas = data.get("reservas", [])
    
    # Contar status
    status_count = {}
    checkouts = []
    
    for reserva in reservas:
        status = reserva.get("status", "UNKNOWN")
        status_count[status] = status_count.get(status, 0) + 1
        
        if status == "CHECKED_OUT":
            checkouts.append({
                "id": reserva.get("id"),
                "cliente": reserva.get("cliente_nome"),
                "quarto": reserva.get("quarto_numero")
            })
    
    print("🔍 Contagem de status:")
    for status, count in sorted(status_count.items()):
        print(f"  {status}: {count}")
    
    print(f"\n✅ Check-outs encontrados ({len(checkouts)}):")
    for checkout in checkouts:
        print(f"  ID {checkout['id']}: {checkout['cliente']} - Quarto {checkout['quarto']}")
        
else:
    print(f"❌ Erro: {response.status_code}")
    print(response.text)
