import json
from types import SimpleNamespace

import pytest

from app.services.programa_pontos_service import ProgramaPontosService
from app.services.real_points_service import RealPointsService
from app.repositories.premio_repo_atomic import PremioRepositoryAtomic
from app.repositories.pontos_repo import PontosRepository
from app.services.pontos_checkout_service import creditar_bonus_cupom_no_checkout, creditar_rp_no_checkout


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
        self.usuariopontos = FakeModel(find_unique_result=SimpleNamespace(saldo=72, pontosNivel=72))
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


def test_aplica_bonus_nivel_nao_multiplica_pontos_n():
    # CT01/CT03/CT05: Pontos N sao sempre a pontuacao-base, nunca multiplicados.
    for codigo in (0, 1, 2):
        nivel = ProgramaPontosService.nivel_por_codigo(codigo)
        calculo = ProgramaPontosService.aplicar_bonus_nivel(3, nivel)
        assert calculo["pontos_n"] == 3


def test_aplica_bonus_nivel_1x_no_nivel_inicial():
    # CT01/CT02: nivel 1 (0-49N) nao multiplica Pontos R.
    nivel = ProgramaPontosService.nivel_por_codigo(0)

    luxo = ProgramaPontosService.aplicar_bonus_nivel(1, nivel)
    real = ProgramaPontosService.aplicar_bonus_nivel(3, nivel)

    assert luxo["multiplicador_r"] == 1
    assert luxo["pontos_n"] == 1 and luxo["pontos_r"] == 1
    assert real["pontos_n"] == 3 and real["pontos_r"] == 3


def test_aplica_bonus_nivel_2x_no_segundo_nivel():
    # CT03/CT04: nivel 2 (50-89N) dobra Pontos R.
    nivel = ProgramaPontosService.nivel_por_codigo(1)

    luxo = ProgramaPontosService.aplicar_bonus_nivel(1, nivel)
    real = ProgramaPontosService.aplicar_bonus_nivel(3, nivel)

    assert luxo["multiplicador_r"] == 2
    assert luxo["pontos_n"] == 1 and luxo["pontos_r"] == 2
    assert real["pontos_n"] == 3 and real["pontos_r"] == 6


def test_aplica_bonus_nivel_4x_no_terceiro_nivel():
    # CT05/CT06/CT10: nivel 3 (90N+) aplica 4x sobre Pontos R, nunca sobre N.
    nivel = ProgramaPontosService.nivel_por_codigo(2)

    luxo = ProgramaPontosService.aplicar_bonus_nivel(1, nivel)
    real = ProgramaPontosService.aplicar_bonus_nivel(3, nivel)

    assert luxo["multiplicador_r"] == 4
    assert luxo["pontos_n"] == 1 and luxo["pontos_r"] == 4
    assert real["pontos_n"] == 3 and real["pontos_r"] == 12


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
        self.usuariopontos = FakeModelValue(SimpleNamespace(saldo=saldo_nivel, pontosNivel=saldo_nivel))
        self.pontosregra = FakeModelValue(SimpleNamespace(diariasBase=1, rpPorBase=2, temporada=None))
        self.transacaopontos = FakeTransacaoModel()


class FakeDbBonusCupomAmigo:
    def __init__(self):
        self.reserva = FakeModelValue(SimpleNamespace(id=10, clienteId=1))
        self.cupomuso = FakeModelValue(SimpleNamespace(
            cupom=SimpleNamespace(codigo="AMIGO10ABCD", pontosBonus=50, tipoCampanha="CUPOM_AMIGO")
        ))
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
    assert resultado["pontos_n"] == 4
    assert resultado["pontos_r"] == 4
    assert resultado["multiplicador_r"] == 1
    assert db._tx.transacaopontos.created_data["status"] == "liberado"
    metadata = json.loads(db._tx.transacaopontos.created_data["metadata"])
    assert metadata["pontos_base"] == 4
    assert metadata["pontos_n"] == 4
    assert metadata["multiplicador_r"] == 1
    assert metadata["pontos_r"] == 4


@pytest.mark.parametrize(
    ("tipo_suite", "pontos_esperados", "categoria_esperada"),
    [
        ("LUXO 2º", 2, "LUXO"),
        ("Suíte Luxo 4º EC", 2, "LUXO"),
        ("Suíte Master", 4, "MASTER"),
        ("DUPLA", 6, "DUPLA"),
        ("REAL", 6, "REAL"),
    ],
)
@pytest.mark.asyncio
async def test_checkout_normaliza_variantes_operacionais_de_suite(
    tipo_suite, pontos_esperados, categoria_esperada
):
    from datetime import datetime, timezone

    db = FakeDbCheckout()
    db.reserva.value.tipoSuite = tipo_suite
    # Sem regra encontrada no banco: valida tambem o fallback da tabela oficial.
    db.pontosregra.value = None

    resultado = await creditar_rp_no_checkout(
        db,
        reserva_id=10,
        checkout_datetime=datetime(2026, 5, 1, 10, 0, tzinfo=timezone.utc),
    )

    assert resultado["success"] is True
    assert resultado["creditado"] is True
    assert resultado["pontos"] == pontos_esperados
    assert resultado["metadata"]["calculo"]["suite_tipo"] == categoria_esperada
    assert resultado["metadata"]["calculo"]["suite_tipo_original"] == tipo_suite


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
    assert resultado["pontos_n"] == 4
    assert resultado["pontos_r"] == 8
    assert resultado["multiplicador_r"] == 2
    assert resultado["pontos"] == 8
    assert resultado["nivel"]["nome"] == "EXPERIENCIA"
    assert resultado["progrediu_nivel"] is False
    assert db._tx.transacaopontos.created_data["pontos"] == 8
    metadata = json.loads(db._tx.transacaopontos.created_data["metadata"])
    assert metadata["programa"] == "JORNADA_REAL"
    assert metadata["origem"] == "CHECKOUT"
    assert metadata["pontos_base"] == 4
    assert metadata["pontos_n"] == 4
    assert metadata["multiplicador_r"] == 2
    assert metadata["pontos_r"] == 8
    assert metadata["pontos_n_antes"] == 72
    assert metadata["pontos_n_depois"] == 76
    assert metadata["nivel_antes"]["nome"] == "EXPERIENCIA"
    assert metadata["calculo"]["suite_tipo"] == "MASTER"


@pytest.mark.asyncio
async def test_reserva_cancelada_nao_gera_pontos():
    db = FakeDbCheckout(reserva_status="CANCELADA")

    resultado = await creditar_rp_no_checkout(db, reserva_id=10)

    assert resultado["success"] is True
    assert resultado["creditado"] is False
    assert resultado["pontos"] == 0


@pytest.mark.asyncio
async def test_cupom_amigo_nao_credita_bonus_para_indicado():
    db = FakeDbBonusCupomAmigo()

    resultado = await creditar_bonus_cupom_no_checkout(db, reserva_id=10)

    assert resultado["success"] is True
    assert resultado["creditado"] is False
    assert resultado["pontos"] == 0
    assert "Cupom Amigo" in resultado["motivo"]


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
