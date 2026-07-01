import json
from types import SimpleNamespace

import pytest

from app.services.programa_pontos_service import ProgramaPontosService
from app.services.real_points_service import RealPointsService
from app.repositories.premio_repo_atomic import PremioRepositoryAtomic
from app.repositories.pontos_repo import PontosRepository
from app.services.pontos_checkout_service import creditar_rp_no_checkout


class FakeModel:
    def __init__(self, *, find_unique_result=None, find_first_result=None):
        self.find_unique_result = find_unique_result
        self.find_first_result = find_first_result

    async def find_unique(self, **kwargs):
        return self.find_unique_result

    async def find_first(self, **kwargs):
        return self.find_first_result


class FakeDbPrograma:
    def __init__(self):
        self.cliente = FakeModel(find_unique_result=SimpleNamespace(id=1, nivelFidelidade=0))
        self.usuariopontos = FakeModel(find_unique_result=SimpleNamespace(saldo=72))
        self.premio = FakeModel(find_first_result=SimpleNamespace(id=10, nome="iPhone 16", precoEmPontos=90, categoria="Tecnologia Real"))
        self.query_calls = 0

    async def query_raw(self, *args):
        self.query_calls += 1
        sql = args[0]
        if "COUNT(*)::int AS rewards_total" in sql:
            saldo = int(args[1] or 0)
            premios = [25, 35, 90, 120]
            return [{
                "rewards_total": len(premios),
                "rewards_unlocked": len([p for p in premios if p <= saldo]),
            }]
        return [{"total": 2}]


def test_aplica_bonus_nivel_experiencia():
    nivel = ProgramaPontosService.nivel_por_codigo(1)
    calculo = ProgramaPontosService.aplicar_bonus_nivel(5, nivel)

    assert calculo["pontos_base"] == 5
    assert calculo["pontos_bonus_nivel"] == 1
    assert calculo["pontos_total"] == 6


def test_aplica_bonus_nivel_real():
    nivel = ProgramaPontosService.nivel_por_codigo(2)
    calculo = ProgramaPontosService.aplicar_bonus_nivel(5, nivel)

    assert calculo["pontos_base"] == 5
    assert calculo["pontos_bonus_nivel"] == 2
    assert calculo["pontos_total"] == 7


@pytest.mark.asyncio
async def test_programa_calcula_barras_nivel_e_premio():
    service = ProgramaPontosService(FakeDbPrograma())

    programa = await service.obter_programa_cliente(1)

    assert programa["success"] is True
    assert programa["nivel"]["nome"] == "EXPERIENCIA"
    assert programa["barra_nivel"]["meta"] == 90
    assert programa["barra_nivel"]["faltam_pontos"] == 18
    assert programa["barra_nivel"]["percentual"] == 55
    assert programa["barra_premios"]["faltam_pontos"] == 18
    assert programa["rewards_unlocked"] == 2
    assert programa["rewards_total"] == 4
    assert programa["barra_premios"]["rewards_unlocked"] == 2
    assert programa["barra_premios"]["rewards_total"] == 4


def test_calculo_pontos_por_suite_e_diarias():
    assert RealPointsService.calcular_rp_oficial("LUXO", 3, 0)[0] == 3
    assert RealPointsService.calcular_rp_oficial("MASTER", 3, 0)[0] == 6
    assert RealPointsService.calcular_rp_oficial("DUPLA", 3, 0)[0] == 9
    assert RealPointsService.calcular_rp_oficial("REAL", 3, 0)[0] == 9


class FakeTransacaoModel:
    def __init__(self):
        self.created_data = None

    async def find_first(self, **kwargs):
        return None

    async def create(self, *, data):
        self.created_data = data
        return SimpleNamespace(id=33)


class FakeUsuarioPontosModel:
    async def create(self, *, data):
        return SimpleNamespace(id=7, saldo=data["saldo"])


class FakeTx:
    def __init__(self):
        self.transacaopontos = FakeTransacaoModel()
        self.usuariopontos = FakeUsuarioPontosModel()
        self.execute_calls = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def query_raw(self, *args):
        sql = args[0]
        if "FROM usuarios_pontos" in sql:
            return [{"id": 7, "saldo": 72}]
        return []

    async def execute_raw(self, *args):
        self.execute_calls.append(args)
        return 1


class FakeDbPontos:
    def __init__(self):
        self._tx = FakeTx()

    def tx(self):
        return self._tx


@pytest.mark.asyncio
async def test_transacao_pendente_nao_altera_saldo_imediatamente():
    db = FakeDbPontos()
    repo = PontosRepository(db)

    resultado = await repo.criar_transacao_pontos(
        cliente_id=1,
        pontos=6,
        tipo="CREDITO",
        origem="CHECKOUT",
        motivo="checkout",
        reserva_id=10,
        status="pendente",
    )

    assert resultado["status"] == "pendente"
    assert resultado["saldo_anterior"] == 72
    assert resultado["saldo_posterior"] == 72
    assert db._tx.execute_calls == []
    assert db._tx.transacaopontos.created_data["status"] == "pendente"


class FakeModelValue:
    def __init__(self, value):
        self.value = value

    async def find_unique(self, **kwargs):
        return self.value

    async def find_first(self, **kwargs):
        return self.value


class FakeDbCheckout(FakeDbPontos):
    def __init__(self, reserva_status="CHECKOUT_REALIZADO", saldo_nivel=0):
        super().__init__()
        self.reserva = FakeModelValue(SimpleNamespace(
            id=10,
            clienteId=1,
            tipoSuite="MASTER",
            numDiarias=2,
            statusReserva=reserva_status,
            codigoReserva="R10",
        ))
        self.cliente = FakeModelValue(SimpleNamespace(id=1, nivelFidelidade=0))
        self.usuariopontos = FakeModelValue(SimpleNamespace(saldo=saldo_nivel))
        self.pontosregra = FakeModelValue(SimpleNamespace(diariasBase=1, rpPorBase=2, temporada=None))
        self.transacaopontos = FakeTransacaoModel()


@pytest.mark.asyncio
async def test_checkout_credita_pontos_imediatamente():
    from datetime import datetime, timezone

    db = FakeDbCheckout()
    checkout_em = datetime(2026, 5, 1, 10, 0, tzinfo=timezone.utc)

    resultado = await creditar_rp_no_checkout(db, reserva_id=10, checkout_datetime=checkout_em)

    assert resultado["success"] is True
    assert resultado["status"] == "liberado"
    assert resultado["liberar_em"] is None
    assert resultado["pontos"] == 4
    assert resultado["pontos_base"] == 4
    assert resultado["pontos_bonus_nivel"] == 0
    assert db._tx.transacaopontos.created_data["status"] == "liberado"
    metadata = json.loads(db._tx.transacaopontos.created_data["metadata"])
    assert metadata["pontos_base"] == 4
    assert metadata["bonus_percentual"] == 0
    assert metadata["pontos_bonus_nivel"] == 0
    assert metadata["pontos_total"] == 4


@pytest.mark.asyncio
async def test_checkout_cai_para_pendente_se_credito_imediato_falhar():
    from datetime import datetime, timezone

    class FakeTxFalhaPrimeiraVez(FakeTx):
        def __init__(self):
            super().__init__()
            self.tentativas = 0

        async def query_raw(self, *args):
            sql = args[0]
            if "FROM usuarios_pontos" in sql:
                self.tentativas += 1
                if self.tentativas == 1:
                    raise RuntimeError("falha simulada de integracao")
                return [{"id": 7, "saldo": 72}]
            return []

    class FakeDbCheckoutFalha(FakeDbCheckout):
        def __init__(self):
            super().__init__()
            self._tx = FakeTxFalhaPrimeiraVez()

        def tx(self):
            return self._tx

    db = FakeDbCheckoutFalha()
    checkout_em = datetime(2026, 5, 1, 10, 0, tzinfo=timezone.utc)

    resultado = await creditar_rp_no_checkout(db, reserva_id=10, checkout_datetime=checkout_em)

    assert resultado["success"] is True
    assert resultado["status"] == "pendente"
    assert resultado["liberar_em"] is not None
    assert db._tx.transacaopontos.created_data["status"] == "pendente"
    metadata = json.loads(db._tx.transacaopontos.created_data["metadata"])
    assert metadata["erro_credito_imediato"]


@pytest.mark.asyncio
async def test_checkout_aplica_bonus_nivel_experiencia():
    from datetime import datetime, timezone

    db = FakeDbCheckout(saldo_nivel=72)
    checkout_em = datetime(2026, 5, 1, 10, 0, tzinfo=timezone.utc)

    resultado = await creditar_rp_no_checkout(db, reserva_id=10, checkout_datetime=checkout_em)

    assert resultado["success"] is True
    assert resultado["pontos_base"] == 4
    assert resultado["pontos_bonus_nivel"] == 1
    assert resultado["pontos"] == 5
    assert resultado["nivel"]["nome"] == "EXPERIENCIA"
    assert db._tx.transacaopontos.created_data["pontos"] == 5
    metadata = json.loads(db._tx.transacaopontos.created_data["metadata"])
    assert metadata["programa"] == "JORNADA_REAL"
    assert metadata["origem"] == "CHECKOUT"
    assert metadata["pontos_base"] == 4
    assert metadata["bonus_percentual"] == 20
    assert metadata["pontos_bonus_nivel"] == 1
    assert metadata["pontos_total"] == 5
    assert metadata["nivel"]["nome"] == "EXPERIENCIA"
    assert metadata["calculo"]["suite_tipo"] == "MASTER"


@pytest.mark.asyncio
async def test_reserva_cancelada_nao_gera_pontos():
    db = FakeDbCheckout(reserva_status="CANCELADA")

    resultado = await creditar_rp_no_checkout(db, reserva_id=10)

    assert resultado["success"] is True
    assert resultado["creditado"] is False
    assert resultado["pontos"] == 0


class FakeCodigoTx:
    async def query_raw(self, *args):
        return []


@pytest.mark.asyncio
async def test_codigo_resgate_formato_real():
    repo = PremioRepositoryAtomic(None)
    codigo = await repo._gerar_codigo_resgate(FakeCodigoTx())

    assert codigo.startswith("REAL-")
    assert len(codigo) == 11
    assert codigo.split("-")[1].isdigit()
