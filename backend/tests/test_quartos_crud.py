"""
Testes para CRUD de Quartos
"""
import pytest
from app.repositories.quarto_repo import QuartoRepository
from app.services.quarto_service import QuartoService
from app.schemas.quarto_schema import QuartoCreate, QuartoUpdate, StatusQuarto, TipoSuite
from app.core.database import get_db, connect_db, disconnect_db


@pytest.fixture
async def db():
    """Fixture para conexão com banco de dados"""
    db_client = get_db()
    try:
        await db_client.connect()
    except:
        pass  # Já conectado
    
    # Limpar dados antes de cada teste
    await db_client.quarto.delete_many()
    
    yield db_client
    
    # Limpar dados após cada teste
    await db_client.quarto.delete_many()


@pytest.fixture
async def quarto_repo(db):
    """Fixture para QuartoRepository"""
    return QuartoRepository(db)


@pytest.fixture
async def quarto_service(db):
    """Fixture para QuartoService"""
    return QuartoService(QuartoRepository(db))


@pytest.mark.asyncio
async def test_criar_quarto(quarto_service, db):
    """Teste: Criar novo quarto"""
    quarto_data = QuartoCreate(
        numero="201",
        tipo_suite=TipoSuite.LUXO,
        status=StatusQuarto.LIVRE
    )
    
    quarto = await quarto_service.create(quarto_data)
    
    assert quarto is not None
    assert quarto["numero"] == "201"
    assert quarto["tipo_suite"] == TipoSuite.LUXO
    assert quarto["status"] == StatusQuarto.LIVRE
    
    # Limpar
    await db.quarto.delete(where={"id": quarto["id"]})


@pytest.mark.asyncio
async def test_criar_quarto_duplicado(quarto_service, db):
    """Teste: Tentar criar quarto com número duplicado"""
    # Limpar antes
    await db.quarto.delete_many()
    
    quarto_data = QuartoCreate(
        numero="202",
        tipo_suite=TipoSuite.MASTER,
        status=StatusQuarto.LIVRE
    )
    
    quarto = await quarto_service.create(quarto_data)
    quarto_id = quarto["id"]
    
    # Tentar criar novamente com mesmo número
    with pytest.raises(Exception):
        await quarto_service.create(quarto_data)
    
    # Limpar
    await db.quarto.delete(where={"id": quarto_id})


@pytest.mark.asyncio
async def test_obter_quarto_por_numero(quarto_service, db):
    """Teste: Obter quarto por número"""
    # Limpar antes
    await db.quarto.delete_many()
    
    # Criar quarto
    quarto_data = QuartoCreate(
        numero="203",
        tipo_suite=TipoSuite.REAL,
        status=StatusQuarto.LIVRE
    )
    
    quarto = await quarto_service.create(quarto_data)
    numero = quarto["numero"]
    
    # Obter quarto
    quarto_obtido = await quarto_service.get_by_numero(numero)
    
    assert quarto_obtido["numero"] == numero
    assert quarto_obtido["tipo_suite"] == TipoSuite.REAL
    
    # Limpar
    await db.quarto.delete(where={"id": quarto["id"]})


@pytest.mark.asyncio
async def test_atualizar_quarto(quarto_service, db):
    """Teste: Atualizar quarto"""
    # Limpar antes
    await db.quarto.delete_many()
    
    # Criar quarto
    quarto_data = QuartoCreate(
        numero="204",
        tipo_suite=TipoSuite.LUXO,
        status=StatusQuarto.LIVRE
    )
    
    quarto = await quarto_service.create(quarto_data)
    numero = quarto["numero"]
    
    # Atualizar quarto
    dados_atualizacao = QuartoUpdate(
        tipo_suite=TipoSuite.MASTER,
        status=StatusQuarto.OCUPADO
    )
    
    quarto_atualizado = await quarto_service.update(numero, dados_atualizacao)
    
    assert quarto_atualizado["tipo_suite"] == TipoSuite.MASTER
    assert quarto_atualizado["status"] == StatusQuarto.OCUPADO
    
    # Limpar
    await db.quarto.delete(where={"id": quarto["id"]})


@pytest.mark.asyncio
async def test_atualizar_status_quarto(quarto_service, db):
    """Teste: Atualizar apenas status do quarto"""
    # Limpar antes
    await db.quarto.delete_many()
    
    # Criar quarto
    quarto_data = QuartoCreate(
        numero="205",
        tipo_suite=TipoSuite.LUXO,
        status=StatusQuarto.LIVRE
    )
    
    quarto = await quarto_service.create(quarto_data)
    numero = quarto["numero"]
    
    # Atualizar status
    quarto_atualizado = await quarto_service.update_status(numero, StatusQuarto.MANUTENCAO)
    
    assert quarto_atualizado["status"] == StatusQuarto.MANUTENCAO
    
    # Limpar
    await db.quarto.delete(where={"id": quarto["id"]})


@pytest.mark.asyncio
async def test_listar_quartos(quarto_service):
    """Teste: Listar todos os quartos"""
    quartos = await quarto_service.list_all()
    
    assert isinstance(quartos, list)


@pytest.mark.asyncio
async def test_listar_quartos_por_status(quarto_service, db):
    """Teste: Listar quartos por status"""
    # Limpar antes
    await db.quarto.delete_many()
    
    # Criar quartos com diferentes status
    quarto1 = await quarto_service.create(QuartoCreate(
        numero="301",
        tipo_suite=TipoSuite.LUXO,
        status=StatusQuarto.LIVRE
    ))
    
    quarto2 = await quarto_service.create(QuartoCreate(
        numero="302",
        tipo_suite=TipoSuite.MASTER,
        status=StatusQuarto.OCUPADO
    ))
    
    # Listar quartos livres
    quartos_livres = await quarto_service.list_by_status(StatusQuarto.LIVRE)
    
    assert len(quartos_livres) >= 1
    assert any(q["numero"] == "301" for q in quartos_livres)
    
    # Limpar
    await db.quarto.delete(where={"id": quarto1["id"]})
    await db.quarto.delete(where={"id": quarto2["id"]})


@pytest.mark.asyncio
async def test_listar_quartos_disponiveis(quarto_service, db):
    """Teste: Listar quartos disponíveis"""
    # Limpar antes
    await db.quarto.delete_many()
    
    # Criar quartos
    quarto1 = await quarto_service.create(QuartoCreate(
        numero="401",
        tipo_suite=TipoSuite.LUXO,
        status=StatusQuarto.LIVRE
    ))
    
    quarto2 = await quarto_service.create(QuartoCreate(
        numero="402",
        tipo_suite=TipoSuite.MASTER,
        status=StatusQuarto.OCUPADO
    ))
    
    # Listar disponíveis
    quartos_disponiveis = await quarto_service.get_disponiveis()
    
    assert len(quartos_disponiveis) >= 1
    assert all(q["status"] == StatusQuarto.LIVRE for q in quartos_disponiveis)
    
    # Limpar
    await db.quarto.delete(where={"id": quarto1["id"]})
    await db.quarto.delete(where={"id": quarto2["id"]})


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

