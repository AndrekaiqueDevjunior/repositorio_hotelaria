"""
Testes de API para Clientes - Testes de integração HTTP
"""
import pytest
import httpx
from datetime import datetime
from app.main import app


@pytest.fixture
async def client():
    """Cliente HTTP para testes"""
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
@pytest.mark.integration
async def test_listar_clientes(client):
    """Teste: Listar todos os clientes via API"""
    response = await client.get("/api/v1/clientes")
    assert response.status_code == 200
    data = response.json()
    assert "clientes" in data
    assert "total" in data
    assert isinstance(data["clientes"], list)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_criar_cliente(client):
    """Teste: Criar cliente via API"""
    documento = f"API{datetime.now().strftime('%Y%m%d%H%M%S')}"
    response = await client.post(
        "/api/v1/clientes",
        json={
            "nome_completo": "Cliente Teste API",
            "documento": documento,
            "telefone": "21999999999",
            "email": "testeapi@teste.com"
        }
    )
    
    assert response.status_code == 200
    cliente = response.json()
    assert cliente["nome_completo"] == "Cliente Teste API"
    assert cliente["documento"] == documento
    assert cliente["status"] == "ATIVO"
    
    # Nota: Dados de teste ficam no banco (não há endpoint DELETE)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_obter_cliente_por_id(client):
    """Teste: Obter cliente por ID via API"""
    # Criar cliente
    documento = f"API{datetime.now().strftime('%Y%m%d%H%M%S')}"
    create_response = await client.post(
        "/api/v1/clientes",
        json={
            "nome_completo": "Cliente Get Test",
            "documento": documento,
            "telefone": "21888888888"
        }
    )
    cliente = create_response.json()
    cliente_id = cliente["id"]
    
    # Obter cliente
    get_response = await client.get(f"/api/v1/clientes/{cliente_id}")
    assert get_response.status_code == 200
    cliente_obtido = get_response.json()
    
    assert cliente_obtido["id"] == cliente_id
    assert cliente_obtido["nome_completo"] == "Cliente Get Test"
    
    # Nota: Dados de teste ficam no banco


@pytest.mark.asyncio
@pytest.mark.integration
async def test_obter_cliente_por_documento(client):
    """Teste: Obter cliente por documento via API"""
    documento = f"API{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Criar cliente
    create_response = await client.post(
        "/api/v1/clientes",
        json={
            "nome_completo": "Cliente Doc Test",
            "documento": documento,
            "telefone": "21777777777"
        }
    )
    cliente = create_response.json()
    
    # Obter por documento
    get_response = await client.get(f"/api/v1/clientes/documento/{documento}")
    assert get_response.status_code == 200
    cliente_obtido = get_response.json()
    
    assert cliente_obtido["documento"] == documento
    
    # Nota: Dados de teste ficam no banco


@pytest.mark.asyncio
@pytest.mark.integration
async def test_atualizar_cliente(client):
    """Teste: Atualizar cliente via API"""
    documento = f"API{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Criar cliente
    create_response = await client.post(
        "/api/v1/clientes",
        json={
            "nome_completo": "Cliente Update Test",
            "documento": documento,
            "telefone": "21666666666"
        }
    )
    cliente = create_response.json()
    cliente_id = cliente["id"]
    
    # Atualizar cliente
    update_response = await client.put(
        f"/api/v1/clientes/{cliente_id}",
        json={
            "nomeCompleto": "Cliente Atualizado",
            "telefone": "21555555555"
        }
    )
    assert update_response.status_code == 200
    cliente_atualizado = update_response.json()
    
    assert cliente_atualizado["nome_completo"] == "Cliente Atualizado"
    assert cliente_atualizado["telefone"] == "21555555555"
    
    # Nota: Dados de teste ficam no banco

