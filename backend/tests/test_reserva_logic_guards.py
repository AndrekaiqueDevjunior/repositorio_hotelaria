from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest

from app.core.state_validators import StateValidator
from app.repositories.reserva_repo import ReservaRepository


def test_state_validator_aceita_status_legados_e_novos():
    validator = StateValidator()

    assert validator.validar_acao_confirmar_reserva("PENDENTE", "APROVADO")[0]
    assert validator.validar_acao_confirmar_reserva("PENDENTE_PAGAMENTO", "CONFIRMADO")[0]
    assert validator.validar_acao_checkin("CONFIRMADA", "PAGO", "NAO_INICIADA")[0]
    assert validator.validar_acao_checkin("CHECKIN_LIBERADO", "AUTHORIZED", "NAO_INICIADA")[0]

    pode_cancelar_checkout, _ = validator.validar_acao_cancelar_reserva(
        "CHECKOUT_REALIZADO",
        "CHECKOUT_REALIZADO",
    )
    assert not pode_cancelar_checkout


class _FakeQuartoTable:
    async def find_unique(self, where):
        numero = where["numero"]
        if numero == "202A":
            return SimpleNamespace(id=77, numero=numero, status="LIVRE")
        return None


class _FakeReservaTable:
    def __init__(self):
        self.updated_data = None
        checkin = datetime.now() + timedelta(days=2)
        checkout = checkin + timedelta(days=2)
        self.current = SimpleNamespace(
            id=10,
            codigoReserva="RCF-TESTE",
            clienteId=1,
            clienteNome="Cliente Teste",
            quartoId=12,
            quartoNumero="101",
            tipoSuite="LUXO",
            statusReserva="PENDENTE",
            checkinPrevisto=checkin,
            checkoutPrevisto=checkout,
            checkinReal=None,
            checkoutReal=None,
            valorDiaria=350,
            valorTotal=700,
            numDiarias=2,
            origem="PARTICULAR",
            responsavelNome=None,
            formaPagamento=None,
            observacoes=None,
            telefoneContato=None,
            emailContato=None,
            createdAt=checkin,
            updatedAt=checkin,
        )

    async def find_unique(self, where, include=None):
        return self.current

    async def find_many(self, where=None, include=None):
        return []

    async def update(self, where, data):
        self.updated_data = data
        for key, value in data.items():
            setattr(self.current, key, value)
        return self.current


class _FakeDb:
    def __init__(self):
        self.quarto = _FakeQuartoTable()
        self.reserva = _FakeReservaTable()


class _FakeCupomUsoTable:
    def __init__(self, valor_final):
        self.valor_final = valor_final
        self.where = None

    async def find_first(self, where):
        self.where = where
        return SimpleNamespace(valorFinal=self.valor_final)


@pytest.mark.asyncio
async def test_update_quarto_numero_tambem_atualiza_quarto_id():
    db = _FakeDb()
    repo = ReservaRepository(db)

    await repo.update(10, {"quarto_numero": "202A"})

    assert db.reserva.updated_data["quartoNumero"] == "202A"
    assert db.reserva.updated_data["quartoId"] == 77


@pytest.mark.asyncio
async def test_valor_total_devido_usa_total_com_desconto_do_cupom():
    db = SimpleNamespace(cupomuso=_FakeCupomUsoTable(valor_final=630.0))
    repo = ReservaRepository(db)
    reserva = SimpleNamespace(valorTotal=700.0, valorDiaria=350.0, numDiarias=2)

    valor_total = await repo._obter_valor_total_devido(10, reserva)

    assert valor_total == 630.0
    assert db.cupomuso.where == {"reservaId": 10}
