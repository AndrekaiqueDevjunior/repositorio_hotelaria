"""
Testes para CRUD de Funcionários
"""
import pytest
from app.repositories.funcionario_repo import FuncionarioRepository
from app.services.funcionario_service import FuncionarioService
from app.schemas.funcionario_schema import FuncionarioCreate, FuncionarioUpdate
from app.core.database import get_db


@pytest.fixture
async def db():
    """Fixture para conexão com banco de dados"""
    db_client = get_db()
    try:
        await db_client.connect()
    except:
        pass  # Já conectado
    
    # Limpar dados antes de cada teste
    await db_client.funcionario.delete_many()
    
    yield db_client
    
    # Limpar dados após cada teste
    await db_client.funcionario.delete_many()


@pytest.fixture
async def funcionario_repo(db):
    """Fixture para FuncionarioRepository"""
    return FuncionarioRepository(db)


@pytest.fixture
async def funcionario_service(db):
    """Fixture para FuncionarioService"""
    return FuncionarioService(FuncionarioRepository(db))


@pytest.mark.asyncio
async def test_criar_funcionario(funcionario_service, db):
    """Teste: Criar novo funcionário"""
    funcionario_data = FuncionarioCreate(
        nome="João Silva",
        email="joao.silva@hotel.com",
        perfil="RECEPCIONISTA",
        status="ATIVO",
        senha="senha123"
    )
    
    funcionario = await funcionario_service.create(funcionario_data)
    
    assert funcionario is not None
    assert funcionario["nome"] == "João Silva"
    assert funcionario["email"] == "joao.silva@hotel.com"
    assert funcionario["perfil"] == "RECEPCIONISTA"
    assert funcionario["status"] == "ATIVO"
    
    # Limpar
    await db.funcionario.delete(where={"id": funcionario["id"]})


@pytest.mark.asyncio
async def test_criar_funcionario_duplicado(funcionario_service, db):
    """Teste: Tentar criar funcionário com email duplicado"""
    # Limpar antes
    await db.funcionario.delete_many()
    
    funcionario_data = FuncionarioCreate(
        nome="Maria Santos",
        email="maria@hotel.com",
        perfil="ADMIN",
        status="ATIVO",
        senha="senha123"
    )
    
    funcionario = await funcionario_service.create(funcionario_data)
    funcionario_id = funcionario["id"]
    
    # Tentar criar novamente com mesmo email
    with pytest.raises(Exception):
        await funcionario_service.create(funcionario_data)
    
    # Limpar
    await db.funcionario.delete(where={"id": funcionario_id})


@pytest.mark.asyncio
async def test_obter_funcionario_por_id(funcionario_service, db):
    """Teste: Obter funcionário por ID"""
    # Limpar antes
    await db.funcionario.delete_many()
    
    funcionario_data = FuncionarioCreate(
        nome="Pedro Costa",
        email="pedro@hotel.com",
        perfil="GERENTE",
        status="ATIVO",
        senha="senha123"
    )
    
    funcionario = await funcionario_service.create(funcionario_data)
    funcionario_id = funcionario["id"]
    
    # Obter funcionário
    funcionario_obtido = await funcionario_service.get_by_id(funcionario_id)
    
    assert funcionario_obtido["id"] == funcionario_id
    assert funcionario_obtido["nome"] == "Pedro Costa"
    
    # Limpar
    await db.funcionario.delete(where={"id": funcionario_id})


@pytest.mark.asyncio
async def test_obter_funcionario_por_email(funcionario_service, db):
    """Teste: Obter funcionário por email"""
    # Limpar antes
    await db.funcionario.delete_many()
    
    funcionario_data = FuncionarioCreate(
        nome="Ana Lima",
        email="ana@hotel.com",
        perfil="RECEPCIONISTA",
        status="ATIVO",
        senha="senha123"
    )
    
    funcionario = await funcionario_service.create(funcionario_data)
    email = funcionario["email"]
    
    # Obter funcionário por email
    funcionario_obtido = await funcionario_service.get_by_email(email)
    
    assert funcionario_obtido["email"] == email
    assert funcionario_obtido["nome"] == "Ana Lima"
    
    # Limpar
    await db.funcionario.delete(where={"id": funcionario["id"]})


@pytest.mark.asyncio
async def test_atualizar_funcionario(funcionario_service, db):
    """Teste: Atualizar funcionário"""
    # Limpar antes
    await db.funcionario.delete_many()
    
    funcionario_data = FuncionarioCreate(
        nome="Carlos Oliveira",
        email="carlos@hotel.com",
        perfil="RECEPCIONISTA",
        status="ATIVO",
        senha="senha123"
    )
    
    funcionario = await funcionario_service.create(funcionario_data)
    funcionario_id = funcionario["id"]
    
    # Atualizar funcionário
    dados_atualizacao = FuncionarioUpdate(
        nome="Carlos Oliveira Silva",
        perfil="GERENTE"
    )
    
    funcionario_atualizado = await funcionario_service.update(funcionario_id, dados_atualizacao)
    
    assert funcionario_atualizado["nome"] == "Carlos Oliveira Silva"
    assert funcionario_atualizado["perfil"] == "GERENTE"
    
    # Limpar
    await db.funcionario.delete(where={"id": funcionario_id})


@pytest.mark.asyncio
async def test_listar_funcionarios(funcionario_service):
    """Teste: Listar todos os funcionários"""
    funcionarios = await funcionario_service.list_all()
    
    assert isinstance(funcionarios, list)


@pytest.mark.asyncio
async def test_listar_funcionarios_por_perfil(funcionario_service, db):
    """Teste: Listar funcionários por perfil"""
    # Limpar antes
    await db.funcionario.delete_many()
    
    # Criar funcionários com diferentes perfis
    funcionario1 = await funcionario_service.create(FuncionarioCreate(
        nome="Admin 1",
        email="admin1@hotel.com",
        perfil="ADMIN",
        status="ATIVO",
        senha="senha123"
    ))
    
    funcionario2 = await funcionario_service.create(FuncionarioCreate(
        nome="Recepcionista 1",
        email="rec1@hotel.com",
        perfil="RECEPCIONISTA",
        status="ATIVO",
        senha="senha123"
    ))
    
    # Listar funcionários ADMIN
    funcionarios_admin = await funcionario_service.list_by_perfil("ADMIN")
    
    assert len(funcionarios_admin) >= 1
    assert any(f["email"] == "admin1@hotel.com" for f in funcionarios_admin)
    
    # Limpar
    await db.funcionario.delete(where={"id": funcionario1["id"]})
    await db.funcionario.delete(where={"id": funcionario2["id"]})


@pytest.mark.asyncio
async def test_listar_funcionarios_por_status(funcionario_service, db):
    """Teste: Listar funcionários por status"""
    # Limpar antes
    await db.funcionario.delete_many()
    
    # Criar funcionários com diferentes status
    funcionario1 = await funcionario_service.create(FuncionarioCreate(
        nome="Ativo 1",
        email="ativo1@hotel.com",
        perfil="RECEPCIONISTA",
        status="ATIVO",
        senha="senha123"
    ))
    
    funcionario2 = await funcionario_service.create(FuncionarioCreate(
        nome="Inativo 1",
        email="inativo1@hotel.com",
        perfil="RECEPCIONISTA",
        status="INATIVO",
        senha="senha123"
    ))
    
    # Listar funcionários ATIVOS
    funcionarios_ativos = await funcionario_service.list_by_status("ATIVO")
    
    assert len(funcionarios_ativos) >= 1
    assert any(f["email"] == "ativo1@hotel.com" for f in funcionarios_ativos)
    
    # Limpar
    await db.funcionario.delete(where={"id": funcionario1["id"]})
    await db.funcionario.delete(where={"id": funcionario2["id"]})


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

