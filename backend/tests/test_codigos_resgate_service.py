from datetime import timedelta

import pytest

from app.repositories.premio_repo_atomic import PremioRepositoryAtomic
from app.utils.datetime_utils import now_utc


class FakeTxCodigo:
    def __init__(self, row):
        self.row = row
        self.execute_calls = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def query_raw(self, *args):
        return [self.row] if self.row else []

    async def execute_raw(self, *args):
        self.execute_calls.append(args)
        return 1


class FakeDbCodigo:
    def __init__(self, row):
        self._tx = FakeTxCodigo(row)

    def tx(self):
        return self._tx


@pytest.mark.asyncio
async def test_codigo_expirado_e_marcado_como_expirado():
    row = {
        "id": 1,
        "resgate_id": 10,
        "cliente_id": 20,
        "premio_id": 30,
        "premio_nome": "iPhone 16",
        "premio_categoria": "Tecnologia Real",
        "status": "ativo",
        "valido_ate": now_utc() - timedelta(days=1),
    }
    repo = PremioRepositoryAtomic(FakeDbCodigo(row))

    resultado = await repo.validar_codigo_resgate("REAL-123456")

    assert resultado["success"] is True
    assert resultado["valido"] is False
    assert resultado["error"] == "Codigo expirado"
    assert len(repo.db._tx.execute_calls) == 2


@pytest.mark.asyncio
async def test_codigo_nao_pode_ser_usado_duas_vezes():
    row = {
        "id": 1,
        "resgate_id": 10,
        "cliente_id": 20,
        "premio_id": 30,
        "premio_nome": "iPhone 16",
        "status": "utilizado",
        "valido_ate": now_utc() + timedelta(days=10),
    }
    repo = PremioRepositoryAtomic(FakeDbCodigo(row))

    resultado = await repo.usar_codigo_resgate("REAL-123456")

    assert resultado["success"] is False
    assert "utilizado" in resultado["error"]
    assert repo.db._tx.execute_calls == []
