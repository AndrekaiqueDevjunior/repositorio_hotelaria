"""
Testes para CRUD de Reservas - Check-in e Check-out
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from app.repositories.reserva_repo import ReservaRepository
from app.repositories.cliente_repo import ClienteRepository
from app.repositories.quarto_repo import QuartoRepository
from app.services.reserva_service import ReservaService
from app.schemas.reserva_schema import ReservaCreate
from app.core.database import get_db, connect_db, disconnect_db


@pytest.fixture
async def db():
    """Fixture para conexão com banco de dados"""
    db_client = get_db()
    try:
        await db_client.connect()
    except:
        pass  # Já conectado
    yield db_client


@pytest.fixture
async def cliente_teste(db):
    """Criar cliente de teste"""
    cliente = await db.cliente.create(
        data={
            "nomeCompleto": "Cliente Teste",
            "documento": "12345678900",
            "telefone": "21999999999",
            "email": "teste@teste.com"
        }
    )
    yield cliente
    # Limpar após teste
    try:
        await db.cliente.delete(where={"id": cliente.id})
    except:
        pass


@pytest.fixture
async def quarto_teste(db):
    """Criar quarto de teste"""
    quarto = await db.quarto.create(
        data={
            "numero": "101",
            "tipoSuite": "LUXO",
            "status": "LIVRE"
        }
    )
    yield quarto
    # Limpar após teste
    try:
        await db.quarto.delete(where={"id": quarto.id})
    except:
        pass


@pytest.fixture
async def reserva_repo(db):
    """Fixture para ReservaRepository"""
    return ReservaRepository(db)


@pytest.fixture
async def reserva_service(db):
    """Fixture para ReservaService"""
    return ReservaService(
        ReservaRepository(db),
        ClienteRepository(db),
        QuartoRepository(db)
    )


@pytest.mark.asyncio
async def test_criar_reserva(reserva_service, cliente_teste, quarto_teste):
    """Teste: Criar nova reserva"""
    checkin = datetime.now() + timedelta(days=1)
    checkout = datetime.now() + timedelta(days=3)
    
    reserva_data = ReservaCreate(
        cliente_id=cliente_teste.id,
        quarto_numero=quarto_teste.numero,
        tipo_suite="LUXO",
        checkin_previsto=checkin,
        checkout_previsto=checkout,
        valor_diaria=150.00,
        num_diarias=2
    )
    
    reserva = await reserva_service.create(reserva_data)
    
    assert reserva is not None
    assert reserva["cliente_id"] == cliente_teste.id
    assert reserva["quarto_numero"] == quarto_teste.numero
    assert reserva["status"] == "PENDENTE"
    assert reserva["valor_total"] == 300.00  # 2 diárias * 150
    
    # Limpar
    db = get_db()
    await db.reserva.delete(where={"id": reserva["id"]})


@pytest.mark.asyncio
async def test_checkin_reserva(reserva_service, cliente_teste, quarto_teste, db):
    """Teste: Realizar check-in de reserva"""
    # Criar reserva
    checkin = datetime.now() + timedelta(days=1)
    checkout = datetime.now() + timedelta(days=3)
    
    reserva_data = ReservaCreate(
        cliente_id=cliente_teste.id,
        quarto_numero=quarto_teste.numero,
        tipo_suite="LUXO",
        checkin_previsto=checkin,
        checkout_previsto=checkout,
        valor_diaria=150.00,
        num_diarias=2
    )
    
    reserva = await reserva_service.create(reserva_data)
    reserva_id = reserva["id"]
    
    # Realizar check-in
    reserva_checkin = await reserva_service.checkin(reserva_id)
    
    assert reserva_checkin["status"] == "HOSPEDADO"
    assert reserva_checkin["checkin_realizado"] is not None
    
    # Verificar se quarto foi atualizado
    quarto = await db.quarto.find_unique(where={"numero": quarto_teste.numero})
    assert quarto.status == "OCUPADO"
    
    # Limpar
    await db.reserva.delete(where={"id": reserva_id})


@pytest.mark.asyncio
async def test_checkout_reserva(reserva_service, cliente_teste, quarto_teste, db):
    """Teste: Realizar check-out de reserva"""
    # Criar reserva
    checkin = datetime.now() + timedelta(days=1)
    checkout = datetime.now() + timedelta(days=3)
    
    reserva_data = ReservaCreate(
        cliente_id=cliente_teste.id,
        quarto_numero=quarto_teste.numero,
        tipo_suite="LUXO",
        checkin_previsto=checkin,
        checkout_previsto=checkout,
        valor_diaria=150.00,
        num_diarias=2
    )
    
    reserva = await reserva_service.create(reserva_data)
    reserva_id = reserva["id"]
    
    # Realizar check-in primeiro
    await reserva_service.checkin(reserva_id)
    
    # Realizar check-out
    reserva_checkout = await reserva_service.checkout(reserva_id)
    
    assert reserva_checkout["status"] == "CHECKED_OUT"
    assert reserva_checkout["checkout_realizado"] is not None
    
    # Verificar se quarto foi liberado
    quarto = await db.quarto.find_unique(where={"numero": quarto_teste.numero})
    assert quarto.status == "LIVRE"
    
    # Limpar
    await db.reserva.delete(where={"id": reserva_id})


@pytest.mark.asyncio
async def test_checkin_reserva_nao_pendente(reserva_service, cliente_teste, quarto_teste, db):
    """Teste: Tentar check-in de reserva que não está pendente"""
    # Criar reserva
    checkin = datetime.now() + timedelta(days=1)
    checkout = datetime.now() + timedelta(days=3)
    
    reserva_data = ReservaCreate(
        cliente_id=cliente_teste.id,
        quarto_numero=quarto_teste.numero,
        tipo_suite="LUXO",
        checkin_previsto=checkin,
        checkout_previsto=checkout,
        valor_diaria=150.00,
        num_diarias=2
    )
    
    reserva = await reserva_service.create(reserva_data)
    reserva_id = reserva["id"]
    
    # Realizar check-in
    await reserva_service.checkin(reserva_id)
    
    # Tentar check-in novamente (deve falhar)
    with pytest.raises(Exception):
        await reserva_service.checkin(reserva_id)
    
    # Limpar
    await db.reserva.delete(where={"id": reserva_id})


@pytest.mark.asyncio
async def test_checkout_reserva_nao_hospedada(reserva_service, cliente_teste, quarto_teste, db):
    """Teste: Tentar check-out de reserva que não está hospedada"""
    # Criar reserva
    checkin = datetime.now() + timedelta(days=1)
    checkout = datetime.now() + timedelta(days=3)
    
    reserva_data = ReservaCreate(
        cliente_id=cliente_teste.id,
        quarto_numero=quarto_teste.numero,
        tipo_suite="LUXO",
        checkin_previsto=checkin,
        checkout_previsto=checkout,
        valor_diaria=150.00,
        num_diarias=2
    )
    
    reserva = await reserva_service.create(reserva_data)
    reserva_id = reserva["id"]
    
    # Tentar check-out sem check-in (deve falhar)
    with pytest.raises(Exception):
        await reserva_service.checkout(reserva_id)
    
    # Limpar
    await db.reserva.delete(where={"id": reserva_id})


@pytest.mark.asyncio
async def test_cancelar_reserva(reserva_service, cliente_teste, quarto_teste, db):
    """Teste: Cancelar reserva"""
    # Criar reserva
    checkin = datetime.now() + timedelta(days=1)
    checkout = datetime.now() + timedelta(days=3)
    
    reserva_data = ReservaCreate(
        cliente_id=cliente_teste.id,
        quarto_numero=quarto_teste.numero,
        tipo_suite="LUXO",
        checkin_previsto=checkin,
        checkout_previsto=checkout,
        valor_diaria=150.00,
        num_diarias=2
    )
    
    reserva = await reserva_service.create(reserva_data)
    reserva_id = reserva["id"]
    
    # Cancelar reserva
    reserva_cancelada = await reserva_service.cancelar(reserva_id)
    
    assert reserva_cancelada["status"] == "CANCELADO"
    
    # Limpar
    await db.reserva.delete(where={"id": reserva_id})


@pytest.mark.asyncio
async def test_listar_reservas(reserva_service):
    """Teste: Listar todas as reservas"""
    resultado = await reserva_service.list_all()
    
    assert "reservas" in resultado
    assert "total" in resultado
    assert isinstance(resultado["reservas"], list)


@pytest.mark.asyncio
async def test_obter_reserva_por_id(reserva_service, cliente_teste, quarto_teste, db):
    """Teste: Obter reserva por ID"""
    # Criar reserva
    checkin = datetime.now() + timedelta(days=1)
    checkout = datetime.now() + timedelta(days=3)
    
    reserva_data = ReservaCreate(
        cliente_id=cliente_teste.id,
        quarto_numero=quarto_teste.numero,
        tipo_suite="LUXO",
        checkin_previsto=checkin,
        checkout_previsto=checkout,
        valor_diaria=150.00,
        num_diarias=2
    )
    
    reserva = await reserva_service.create(reserva_data)
    reserva_id = reserva["id"]
    
    # Obter reserva
    reserva_obtida = await reserva_service.get_by_id(reserva_id)
    
    assert reserva_obtida["id"] == reserva_id
    assert reserva_obtida["cliente_id"] == cliente_teste.id
    
    # Limpar
    await db.reserva.delete(where={"id": reserva_id})


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

