"""
Testes para CRUD de Pagamentos
"""
import pytest
from app.repositories.pagamento_repo import PagamentoRepository
from app.repositories.reserva_repo import ReservaRepository
from app.repositories.cliente_repo import ClienteRepository
from app.services.pagamento_service import PagamentoService
from app.schemas.pagamento_schema import PagamentoCreate
from app.core.database import get_db
from datetime import datetime, timedelta


@pytest.fixture
async def db():
    """Fixture para conexão com banco de dados"""
    db_client = get_db()
    try:
        await db_client.connect()
    except:
        pass  # Já conectado
    
    # Limpar dados antes de cada teste
    await db_client.pagamento.delete_many()
    await db_client.reserva.delete_many()
    await db_client.cliente.delete_many()
    
    yield db_client
    
    # Limpar dados após cada teste
    await db_client.pagamento.delete_many()
    await db_client.reserva.delete_many()
    await db_client.cliente.delete_many()


@pytest.fixture
async def cliente_teste(db):
    """Criar cliente de teste"""
    cliente = await db.cliente.create(
        data={
            "nomeCompleto": "Cliente Pagamento Teste",
            "documento": "99988877766",
            "telefone": "21999999999",
            "email": "pagamento@teste.com"
        }
    )
    yield cliente
    try:
        await db.cliente.delete(where={"id": cliente.id})
    except:
        pass


@pytest.fixture
async def quarto_teste(db):
    """Criar quarto de teste"""
    quarto = await db.quarto.create(
        data={
            "numero": "999",
            "tipoSuite": "LUXO",
            "status": "LIVRE"
        }
    )
    yield quarto
    try:
        await db.quarto.delete(where={"id": quarto.id})
    except:
        pass


@pytest.fixture
async def reserva_teste(db, cliente_teste, quarto_teste):
    """Criar reserva de teste"""
    checkin = datetime.now() + timedelta(days=1)
    checkout = datetime.now() + timedelta(days=3)
    
    reserva = await db.reserva.create(
        data={
            "codigoReserva": "TEST-001",
            "clienteId": cliente_teste.id,
            "quartoNumero": quarto_teste.numero,
            "tipoSuite": "LUXO",
            "clienteNome": cliente_teste.nomeCompleto,
            "checkinPrevisto": checkin,
            "checkoutPrevisto": checkout,
            "valorDiaria": 200.0,
            "numDiarias": 2,
            "status": "PENDENTE",
            "statusReserva": "PENDENTE"
        }
    )
    yield reserva
    try:
        await db.reserva.delete(where={"id": reserva.id})
    except:
        pass


@pytest.fixture
async def pagamento_service(db):
    """Fixture para PagamentoService"""
    return PagamentoService(PagamentoRepository(db))


@pytest.mark.asyncio
async def test_criar_pagamento(pagamento_service, reserva_teste, db):
    """Teste: Criar novo pagamento"""
    # Limpar antes
    await db.pagamento.delete_many()
    
    pagamento_data = PagamentoCreate(
        reserva_id=reserva_teste.id,
        valor=400.0,
        metodo="credit_card",
        parcelas=1,
        cartao_numero="4111111111111111",
        cartao_validade="12/25",
        cartao_cvv="123",
        cartao_nome="TESTE CARTAO"
    )
    
    pagamento = await pagamento_service.create(pagamento_data)
    
    assert pagamento is not None
    assert pagamento["valor"] == 400.0
    assert pagamento["metodo"] == "credit_card"
    
    # Limpar
    await db.pagamento.delete(where={"id": pagamento["id"]})


@pytest.mark.asyncio
async def test_obter_pagamento_por_id(pagamento_service, reserva_teste, db):
    """Teste: Obter pagamento por ID"""
    # Limpar antes
    await db.pagamento.delete_many()
    
    pagamento_data = PagamentoCreate(
        reserva_id=reserva_teste.id,
        valor=300.0,
        metodo="pix"
    )
    
    pagamento = await pagamento_service.create(pagamento_data)
    pagamento_id = pagamento["id"]
    
    # Obter pagamento
    pagamento_obtido = await pagamento_service.get_by_id(pagamento_id)
    
    assert pagamento_obtido["id"] == pagamento_id
    assert pagamento_obtido["valor"] == 300.0
    
    # Limpar
    await db.pagamento.delete(where={"id": pagamento_id})


@pytest.mark.asyncio
async def test_listar_pagamentos_por_reserva(pagamento_service, reserva_teste, db):
    """Teste: Listar pagamentos de uma reserva"""
    # Limpar antes
    await db.pagamento.delete_many()
    
    # Criar múltiplos pagamentos para a mesma reserva
    pagamento1_data = PagamentoCreate(
        reserva_id=reserva_teste.id,
        valor=200.0,
        metodo="credit_card"
    )
    
    pagamento2_data = PagamentoCreate(
        reserva_id=reserva_teste.id,
        valor=200.0,
        metodo="pix"
    )
    
    pagamento1 = await pagamento_service.create(pagamento1_data)
    pagamento2 = await pagamento_service.create(pagamento2_data)
    
    # Listar pagamentos da reserva
    pagamentos = await pagamento_service.list_by_reserva(reserva_teste.id)
    
    assert len(pagamentos) >= 2
    
    # Limpar
    await db.pagamento.delete(where={"id": pagamento1["id"]})
    await db.pagamento.delete(where={"id": pagamento2["id"]})


@pytest.mark.asyncio
async def test_cancelar_pagamento(pagamento_service, reserva_teste, db):
    """Teste: Cancelar pagamento"""
    # Limpar antes
    await db.pagamento.delete_many()
    
    pagamento_data = PagamentoCreate(
        reserva_id=reserva_teste.id,
        valor=500.0,
        metodo="credit_card"
    )
    
    pagamento = await pagamento_service.create(pagamento_data)
    pagamento_id = pagamento["id"]
    
    # Cancelar pagamento
    pagamento_cancelado = await pagamento_service.cancelar_pagamento(pagamento_id)
    
    assert pagamento_cancelado["status"] in ["CANCELADO", "CANCELLED", "CANCELED"]
    
    # Limpar
    await db.pagamento.delete(where={"id": pagamento_id})


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

