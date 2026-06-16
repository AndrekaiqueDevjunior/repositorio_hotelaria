from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.services.indicacao_service import IndicacaoService, PONTOS_CONVITE_REAL


class FakeModel:
    def __init__(self, *, find_unique_result=None, find_first_result=None):
        self.find_unique_result = find_unique_result
        self.find_first_result = find_first_result

    async def find_unique(self, **kwargs):
        return self.find_unique_result

    async def find_first(self, **kwargs):
        return self.find_first_result


class FakeRepo:
    def __init__(self, existing=None):
        self.existing = existing
        self.created = None

    async def get_by_cpf_indicado(self, cpf):
        return self.existing

    async def create(self, data):
        self.created = data
        return {
            "id": 1,
            "cliente_indicador_id": data["clienteIndicadorId"],
            "cliente_indicado_id": data.get("clienteIndicadoId"),
            "reserva_id": None,
            "transacao_pontos_id": None,
            "cpf_indicador": data["cpfIndicador"],
            "cpf_indicado": data["cpfIndicado"],
            "status": data["status"],
            "data_envio": data["dataEnvio"],
            "data_reserva": None,
            "data_checkin": None,
            "data_checkout": None,
            "pontos_creditados": False,
        }


class NoopTx:
    def __init__(self, rows):
        self.rows = rows

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def query_raw(self, *args):
        return self.rows


class FakeDbForCheckoutDuplicado:
    def __init__(self):
        self.reserva = FakeModel(
            find_unique_result=SimpleNamespace(
                id=10,
                clienteId=2,
                codigoReserva="RCF-1",
                checkoutReal=None,
                cliente=SimpleNamespace(documento="22233344455"),
                hospedagem=SimpleNamespace(checkoutRealizadoEm=None),
            )
        )

    def tx(self):
        return NoopTx([
            {
                "id": 7,
                "cliente_indicador_id": 1,
                "pontos_creditados": True,
            }
        ])


class FakeTransacaoPontosCredito:
    def __init__(self):
        self.created_data = None

    async def find_first(self, **kwargs):
        return None

    async def create(self, data):
        self.created_data = data
        return SimpleNamespace(id=123)


class FakeUsuarioPontosCredito:
    async def create(self, data):
        return SimpleNamespace(id=55, saldo=data["saldo"])


class FakeTxForCheckoutCredito:
    def __init__(self):
        self.query_calls = 0
        self.execute_calls = []
        self.transacaopontos = FakeTransacaoPontosCredito()
        self.usuariopontos = FakeUsuarioPontosCredito()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def query_raw(self, *args):
        self.query_calls += 1
        if self.query_calls == 1:
            return [
                {
                    "id": 7,
                    "cliente_indicador_id": 1,
                    "pontos_creditados": False,
                }
            ]
        return [{"id": 55, "saldo": 12}]

    async def execute_raw(self, *args):
        self.execute_calls.append(args)
        return None


class FakeDbForCheckoutCredito:
    def __init__(self):
        self.tx_context = FakeTxForCheckoutCredito()
        self.reserva = FakeModel(
            find_unique_result=SimpleNamespace(
                id=10,
                clienteId=2,
                codigoReserva="RCF-1",
                checkoutReal=None,
                cliente=SimpleNamespace(documento="22233344455"),
                hospedagem=SimpleNamespace(checkoutRealizadoEm=None),
            )
        )

    def tx(self):
        return self.tx_context


class FakeDbForStatus:
    def __init__(self):
        self.cliente = FakeModel(find_unique_result=SimpleNamespace(id=1, documento="12345678909", nivelFidelidade=0))
        self.usuariopontos = FakeModel(find_unique_result=SimpleNamespace(saldo=12))
        self.premio = FakeModel(find_first_result=SimpleNamespace(id=4, nome="Voucher especial", precoEmPontos=15, categoria="GERAL"))
        self.query_calls = 0

    async def query_raw(self, *args):
        self.query_calls += 1
        if self.query_calls == 1:
            return [{"total": 12}]
        return [{"total": 0}]


@pytest.mark.asyncio
async def test_bloqueia_autoindicacao():
    db = SimpleNamespace(
        cliente=FakeModel(find_unique_result=SimpleNamespace(id=1, documento="123.456.789-09")),
    )
    service = IndicacaoService(db)
    service.repo = FakeRepo()
    service._buscar_cliente_por_documento = lambda documento: None

    with pytest.raises(HTTPException) as exc:
        await service.criar_indicacao(1, "12345678909")

    assert exc.value.status_code == 400
    assert "Autoindica" in exc.value.detail


@pytest.mark.asyncio
async def test_bloqueia_cpf_indicado_duplicado():
    db = SimpleNamespace(
        cliente=FakeModel(find_unique_result=SimpleNamespace(id=1, documento="12345678909")),
    )
    service = IndicacaoService(db)
    service.repo = FakeRepo(existing={"id": 99})
    service._buscar_cliente_por_documento = lambda documento: None

    with pytest.raises(HTTPException) as exc:
        await service.criar_indicacao(1, "22233344455")

    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_checkout_duplicado_nao_credita_novamente():
    service = IndicacaoService(FakeDbForCheckoutDuplicado())

    resultado = await service.processar_credito_indicacao_apos_checkout(10)

    assert resultado["success"] is True
    assert resultado["creditado"] is False
    assert resultado["idempotente"] is True


@pytest.mark.asyncio
async def test_checkout_credita_50_pontos_para_indicador():
    assert PONTOS_CONVITE_REAL == 50
    db = FakeDbForCheckoutCredito()
    service = IndicacaoService(db)

    resultado = await service.processar_credito_indicacao_apos_checkout(10, funcionario_id=9)

    assert resultado["success"] is True
    assert resultado["creditado"] is True
    assert resultado["pontos"] == 50
    assert resultado["saldo_anterior"] == 12
    assert resultado["saldo_posterior"] == 62

    transacao = db.tx_context.transacaopontos.created_data
    assert transacao["clienteId"] == 1
    assert transacao["funcionarioId"] == 9
    assert transacao["reservaId"] == 10
    assert transacao["origem"] == "CONVITE_REAL"
    assert transacao["pontos"] == 50
    assert transacao["saldoAnterior"] == 12
    assert transacao["saldoPosterior"] == 62


@pytest.mark.asyncio
async def test_calcula_faltam_pontos_para_proximo_premio():
    db = FakeDbForStatus()
    service = IndicacaoService(db)
    service.repo = SimpleNamespace(list_by_indicador=lambda cliente_id: _async_return([]))

    resultado = await service.obter_status_cliente(1)

    assert resultado["saldo_atual"] == 12
    assert resultado["faltam_pontos_para_proximo_premio"] == 3
    assert resultado["proximo_premio"]["preco_em_pontos"] == 15


async def _async_return(value):
    return value
