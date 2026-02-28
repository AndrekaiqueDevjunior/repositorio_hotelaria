"""
Configuração global para testes pytest
"""
import pytest
from app.core.database import get_db, connect_db, disconnect_db


@pytest.fixture(scope="function", autouse=True)
async def setup_database():
    """Configurar banco de dados para testes"""
    try:
        await connect_db()
        yield
    finally:
        await disconnect_db()

