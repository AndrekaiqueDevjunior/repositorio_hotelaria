"""
Testes para CRUD de Clientes
"""
import pytest
from app.repositories.cliente_repo import ClienteRepository
from app.services.cliente_service import ClienteService
from app.schemas.cliente_schema import ClienteCreate
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
async def cliente_repo(db):
    """Fixture para ClienteRepository"""
    return ClienteRepository(db)


@pytest.fixture
async def cliente_service(db):
    """Fixture para ClienteService"""
    return ClienteService(ClienteRepository(db))


@pytest.mark.asyncio
async def test_criar_cliente(cliente_service, db):
    """Teste: Criar novo cliente"""
    cliente_data = ClienteCreate(
        nome_completo="João Silva",
        documento="12345678901",
        telefone="21999999999",
        email="joao@teste.com"
    )
    
    cliente = await cliente_service.create(cliente_data)
    
    assert cliente is not None
    assert cliente["nome_completo"] == "João Silva"
    assert cliente["documento"] == "12345678901"
    assert cliente["status"] == "ATIVO"
    
    # Limpar
    await db.cliente.delete(where={"id": cliente["id"]})


@pytest.mark.asyncio
async def test_criar_cliente_duplicado(cliente_service, db):
    """Teste: Tentar criar cliente com documento duplicado"""
    cliente_data = ClienteCreate(
        nome_completo="João Silva",
        documento="12345678902",
        telefone="21999999999",
        email="joao@teste.com"
    )
    
    cliente = await cliente_service.create(cliente_data)
    cliente_id = cliente["id"]
    
    # Tentar criar novamente com mesmo documento
    with pytest.raises(Exception):
        await cliente_service.create(cliente_data)
    
    # Limpar
    await db.cliente.delete(where={"id": cliente_id})


@pytest.mark.asyncio
async def test_obter_cliente_por_id(cliente_service, db):
    """Teste: Obter cliente por ID"""
    # Criar cliente
    cliente_data = ClienteCreate(
        nome_completo="Maria Santos",
        documento="98765432100",
        telefone="21888888888",
        email="maria@teste.com"
    )
    
    cliente = await cliente_service.create(cliente_data)
    cliente_id = cliente["id"]
    
    # Obter cliente
    cliente_obtido = await cliente_service.get_by_id(cliente_id)
    
    assert cliente_obtido["id"] == cliente_id
    assert cliente_obtido["nome_completo"] == "Maria Santos"
    
    # Limpar
    await db.cliente.delete(where={"id": cliente_id})


@pytest.mark.asyncio
async def test_obter_cliente_por_documento(cliente_service, db):
    """Teste: Obter cliente por documento"""
    # Criar cliente
    cliente_data = ClienteCreate(
        nome_completo="Pedro Costa",
        documento="11122233344",
        telefone="21777777777",
        email="pedro@teste.com"
    )
    
    cliente = await cliente_service.create(cliente_data)
    documento = cliente["documento"]
    
    # Obter cliente por documento
    cliente_obtido = await cliente_service.get_by_documento(documento)
    
    assert cliente_obtido["documento"] == documento
    assert cliente_obtido["nome_completo"] == "Pedro Costa"
    
    # Limpar
    await db.cliente.delete(where={"id": cliente["id"]})


@pytest.mark.asyncio
async def test_atualizar_cliente(cliente_service, db):
    """Teste: Atualizar cliente"""
    # Criar cliente
    cliente_data = ClienteCreate(
        nome_completo="Ana Lima",
        documento="55566677788",
        telefone="21666666666",
        email="ana@teste.com"
    )
    
    cliente = await cliente_service.create(cliente_data)
    cliente_id = cliente["id"]
    
    # Atualizar cliente
    dados_atualizacao = {
        "nomeCompleto": "Ana Lima Silva",
        "telefone": "21555555555"
    }
    
    cliente_atualizado = await cliente_service.update(cliente_id, dados_atualizacao)
    
    assert cliente_atualizado["nome_completo"] == "Ana Lima Silva"
    assert cliente_atualizado["telefone"] == "21555555555"
    
    # Limpar
    await db.cliente.delete(where={"id": cliente_id})


@pytest.mark.asyncio
async def test_listar_clientes(cliente_service):
    """Teste: Listar todos os clientes"""
    resultado = await cliente_service.list_all()
    
    assert "clientes" in resultado
    assert "total" in resultado
    assert isinstance(resultado["clientes"], list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

