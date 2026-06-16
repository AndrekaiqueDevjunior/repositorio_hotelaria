from datetime import timedelta
from types import SimpleNamespace

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


class FakeCodigoResgateModel:
    def __init__(self, tx):
        self.tx = tx
        self.create_calls = []

    async def create(self, data):
        self.create_calls.append(data)
        return SimpleNamespace(id=2, codigo=data["codigo"])


class FakeTxRenovar:
    def __init__(self):
        self.execute_calls = []
        self.query_calls = []
        self.codigoresgate = FakeCodigoResgateModel(self)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def query_raw(self, query, *args):
        self.query_calls.append((query, args))
        if "FROM resgates_premios" in query and "FOR UPDATE" in query:
            return [{"id": 10, "cliente_id": 20, "premio_id": 30, "status": "aguardando_uso"}]
        if "UPDATE codigos_resgate" in query and "RETURNING codigo" in query:
            return [{"codigo": "REAL-OLD001"}]
        return []

    async def execute_raw(self, *args):
        self.execute_calls.append(args)
        return 1


class FakeDbRenovar:
    def __init__(self):
        self._tx = FakeTxRenovar()

    def tx(self):
        return self._tx


class FakeTxExpirar:
    def __init__(self):
        self.execute_calls = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def query_raw(self, query, *args):
        if "UPDATE codigos_resgate" in query:
            return [
                {"id": 1, "resgate_id": 10, "codigo": "REAL-EXP001"},
                {"id": 2, "resgate_id": 11, "codigo": "REAL-EXP002"},
            ]
        return []

    async def execute_raw(self, *args):
        self.execute_calls.append(args)
        return 1


class FakeDbExpirar:
    def __init__(self):
        self._tx = FakeTxExpirar()

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


@pytest.mark.asyncio
async def test_renovar_codigo_cancela_antigo_e_cria_novo():
    repo = PremioRepositoryAtomic(FakeDbRenovar())

    async def fake_gerar_codigo(transaction):
        return "REAL-NEW001"

    repo._gerar_codigo_resgate = fake_gerar_codigo

    resultado = await repo.renovar_codigo_resgate(
        resgate_id=10,
        funcionario_id=7,
        dias_validade=15,
    )

    assert resultado["success"] is True
    assert resultado["codigo_resgate"] == "REAL-NEW001"
    assert resultado["codigos_cancelados"] == ["REAL-OLD001"]

    create_call = repo.db._tx.codigoresgate.create_calls[0]
    assert create_call["resgateId"] == 10
    assert create_call["codigo"] == "REAL-NEW001"
    assert create_call["status"] == "ativo"
    assert create_call["funcionarioId"] == 7

    assert len(repo.db._tx.execute_calls) == 2


@pytest.mark.asyncio
async def test_job_expira_codigos_resgate_vencidos():
    repo = PremioRepositoryAtomic(FakeDbExpirar())

    resultado = await repo.expirar_codigos_vencidos()

    assert resultado["success"] is True
    assert resultado["codigos_expirados"] == 2
    assert [item["codigo"] for item in resultado["expirados"]] == [
        "REAL-EXP001",
        "REAL-EXP002",
    ]
    assert len(repo.db._tx.execute_calls) == 2
    assert repo.db._tx.execute_calls[0][-1] == "REAL-EXP001"
