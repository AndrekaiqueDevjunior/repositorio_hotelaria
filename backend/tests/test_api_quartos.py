"""
Testes de API para Quartos - Testes de integração HTTP
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
async def test_listar_quartos(client):
    """Teste: Listar todos os quartos via API"""
    response = await client.get("/api/v1/quartos")
    assert response.status_code == 200
    quartos = response.json()
    assert isinstance(quartos, list)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_criar_quarto(client):
    """Teste: Criar quarto via API"""
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
    assert quarto["numero"] == numero
    assert quarto["tipo_suite"] == "LUXO"
    assert quarto["status"] == "LIVRE"
    
    # Nota: Dados de teste ficam no banco


@pytest.mark.asyncio
@pytest.mark.integration
async def test_obter_quarto_por_numero(client):
    """Teste: Obter quarto por número via API"""
    numero = f"API{datetime.now().strftime('%H%M%S')}"
    
    # Criar quarto
    create_response = await client.post(
        "/api/v1/quartos",
        json={
            "numero": numero,
            "tipo_suite": "MASTER",
            "status": "LIVRE"
        }
    )
    quarto = create_response.json()
    
    # Obter quarto
    get_response = await client.get(f"/api/v1/quartos/{numero}")
    assert get_response.status_code == 200
    quarto_obtido = get_response.json()
    
    assert quarto_obtido["numero"] == numero
    assert quarto_obtido["tipo_suite"] == "MASTER"
    
    # Nota: Dados de teste ficam no banco


@pytest.mark.asyncio
@pytest.mark.integration
async def test_atualizar_quarto(client):
    """Teste: Atualizar quarto via API"""
    numero = f"API{datetime.now().strftime('%H%M%S')}"
    
    # Criar quarto
    create_response = await client.post(
        "/api/v1/quartos",
        json={
            "numero": numero,
            "tipo_suite": "LUXO",
            "status": "LIVRE"
        }
    )
    quarto = create_response.json()
    
    # Atualizar quarto
    update_response = await client.put(
        f"/api/v1/quartos/{numero}",
        json={
            "tipo_suite": "MASTER",
            "status": "OCUPADO"
        }
    )
    assert update_response.status_code == 200
    quarto_atualizado = update_response.json()
    
    assert quarto_atualizado["tipo_suite"] == "MASTER"
    assert quarto_atualizado["status"] == "OCUPADO"
    
    # Nota: Dados de teste ficam no banco


@pytest.mark.asyncio
@pytest.mark.integration
async def test_atualizar_status_quarto(client):
    """Teste: Atualizar status do quarto via API"""
    numero = f"API{datetime.now().strftime('%H%M%S')}"
    
    # Criar quarto
    create_response = await client.post(
        "/api/v1/quartos",
        json={
            "numero": numero,
            "tipo_suite": "LUXO",
            "status": "LIVRE"
        }
    )
    quarto = create_response.json()
    
    # Atualizar status (usando query parameter ou body)
    update_response = await client.patch(
        f"/api/v1/quartos/{numero}/status?status=MANUTENCAO"
    )
    assert update_response.status_code == 200
    quarto_atualizado = update_response.json()
    
    assert quarto_atualizado["status"] == "MANUTENCAO"
    
    # Nota: Dados de teste ficam no banco


@pytest.mark.asyncio
@pytest.mark.integration
async def test_listar_quartos_disponiveis(client):
    """Teste: Listar quartos disponíveis via API"""
    response = await client.get("/api/v1/quartos/disponiveis")
    assert response.status_code == 200
    quartos = response.json()
    assert isinstance(quartos, list)
    # Todos devem estar livres
    for quarto in quartos:
        assert quarto["status"] == "LIVRE"

