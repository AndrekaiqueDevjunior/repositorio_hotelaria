"""
Testes de API para Reservas - Testes de integração HTTP
Estes testes fazem requisições HTTP reais à API
"""
import pytest
import httpx
from datetime import datetime, timedelta
from app.main import app


@pytest.fixture
async def client():
    """Cliente HTTP para testes"""
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def cliente_teste(client):
    """Criar cliente de teste via API"""
    response = await client.post(
        "/api/v1/clientes",
        json={
            "nome_completo": "Cliente Teste API",
            "documento": f"API{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "telefone": "21999999999",
            "email": "testeapi@teste.com"
        }
    )
    assert response.status_code == 200
    cliente = response.json()
    yield cliente
    
    # Limpar após teste (via banco de dados se necessário)
    # Nota: Não há endpoint DELETE, então os dados ficam no banco de teste


@pytest.fixture
async def quarto_teste(client):
    """Criar quarto de teste via API"""
    numero = f"API{datetime.now().strftime('%H%M%S')}"
    response = await client.post(
        "/api/v1/quartos",
        json={
            "numero": numero,
            "tipo_suite": "LUXO",
            "status": "LIVRE"
        }
    )
    assert response.status_code == 200
    quarto = response.json()
    yield quarto
    
    # Limpar após teste (via banco de dados se necessário)
    # Nota: Não há endpoint DELETE, então os dados ficam no banco de teste


@pytest.mark.asyncio
@pytest.mark.integration
async def test_listar_reservas(client):
    """Teste: Listar todas as reservas"""
    response = await client.get("/api/v1/reservas")
    assert response.status_code == 200
    data = response.json()
    assert "reservas" in data
    assert "total" in data
    assert isinstance(data["reservas"], list)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_criar_reserva(client, cliente_teste, quarto_teste):
    """Teste: Criar nova reserva via API"""
    checkin = (datetime.now() + timedelta(days=1)).isoformat()
    checkout = (datetime.now() + timedelta(days=3)).isoformat()
    
    response = await client.post(
        "/api/v1/reservas",
        json={
            "cliente_id": cliente_teste["id"],
            "quarto_numero": quarto_teste["numero"],
            "tipo_suite": "LUXO",
            "checkin_previsto": checkin,
            "checkout_previsto": checkout,
            "valor_diaria": 150.00,
            "num_diarias": 2
        }
    )
    
    assert response.status_code == 200
    reserva = response.json()
    assert reserva["cliente_id"] == cliente_teste["id"]
    assert reserva["quarto_numero"] == quarto_teste["numero"]
    assert reserva["status"] == "PENDENTE"
    assert "valor_total" in reserva


@pytest.mark.asyncio
@pytest.mark.integration
async def test_checkin_reserva(client, cliente_teste, quarto_teste):
    """Teste: Realizar check-in via API"""
    # Criar reserva
    checkin = (datetime.now() + timedelta(days=1)).isoformat()
    checkout = (datetime.now() + timedelta(days=3)).isoformat()
    
    create_response = await client.post(
        "/api/v1/reservas",
        json={
            "cliente_id": cliente_teste["id"],
            "quarto_numero": quarto_teste["numero"],
            "tipo_suite": "LUXO",
            "checkin_previsto": checkin,
            "checkout_previsto": checkout,
            "valor_diaria": 150.00,
            "num_diarias": 2
        }
    )
    reserva = create_response.json()
    reserva_id = reserva["id"]
    
    # Realizar check-in
    checkin_response = await client.post(f"/api/v1/reservas/{reserva_id}/checkin")
    assert checkin_response.status_code == 200
    reserva_checkin = checkin_response.json()
    
    assert reserva_checkin["status"] == "HOSPEDADO"
    assert reserva_checkin["checkin_realizado"] is not None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_checkout_reserva(client, cliente_teste, quarto_teste):
    """Teste: Realizar check-out via API"""
    # Criar reserva
    checkin = (datetime.now() + timedelta(days=1)).isoformat()
    checkout = (datetime.now() + timedelta(days=3)).isoformat()
    
    create_response = await client.post(
        "/api/v1/reservas",
        json={
            "cliente_id": cliente_teste["id"],
            "quarto_numero": quarto_teste["numero"],
            "tipo_suite": "LUXO",
            "checkin_previsto": checkin,
            "checkout_previsto": checkout,
            "valor_diaria": 150.00,
            "num_diarias": 2
        }
    )
    reserva = create_response.json()
    reserva_id = reserva["id"]
    
    # Check-in primeiro
    await client.post(f"/api/v1/reservas/{reserva_id}/checkin")
    
    # Realizar check-out
    checkout_response = await client.post(f"/api/v1/reservas/{reserva_id}/checkout")
    assert checkout_response.status_code == 200
    reserva_checkout = checkout_response.json()
    
    assert reserva_checkout["status"] == "CHECKED_OUT"
    assert reserva_checkout["checkout_realizado"] is not None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_cancelar_reserva(client, cliente_teste, quarto_teste):
    """Teste: Cancelar reserva via API"""
    # Criar reserva
    checkin = (datetime.now() + timedelta(days=1)).isoformat()
    checkout = (datetime.now() + timedelta(days=3)).isoformat()
    
    create_response = await client.post(
        "/api/v1/reservas",
        json={
            "cliente_id": cliente_teste["id"],
            "quarto_numero": quarto_teste["numero"],
            "tipo_suite": "LUXO",
            "checkin_previsto": checkin,
            "checkout_previsto": checkout,
            "valor_diaria": 150.00,
            "num_diarias": 2
        }
    )
    reserva = create_response.json()
    reserva_id = reserva["id"]
    
    # Cancelar reserva
    cancel_response = await client.patch(f"/api/v1/reservas/{reserva_id}/cancelar")
    assert cancel_response.status_code == 200
    reserva_cancelada = cancel_response.json()
    
    assert reserva_cancelada["status"] == "CANCELADO"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_obter_reserva_por_id(client, cliente_teste, quarto_teste):
    """Teste: Obter reserva por ID via API"""
    # Criar reserva
    checkin = (datetime.now() + timedelta(days=1)).isoformat()
    checkout = (datetime.now() + timedelta(days=3)).isoformat()
    
    create_response = await client.post(
        "/api/v1/reservas",
        json={
            "cliente_id": cliente_teste["id"],
            "quarto_numero": quarto_teste["numero"],
            "tipo_suite": "LUXO",
            "checkin_previsto": checkin,
            "checkout_previsto": checkout,
            "valor_diaria": 150.00,
            "num_diarias": 2
        }
    )
    reserva = create_response.json()
    reserva_id = reserva["id"]
    
    # Obter reserva
    get_response = await client.get(f"/api/v1/reservas/{reserva_id}")
    assert get_response.status_code == 200
    reserva_obtida = get_response.json()
    
    assert reserva_obtida["id"] == reserva_id
    assert reserva_obtida["cliente_id"] == cliente_teste["id"]

