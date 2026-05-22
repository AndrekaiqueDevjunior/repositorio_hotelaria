from datetime import datetime
from types import SimpleNamespace

import pytest

from app.services.disponibilidade_service import DisponibilidadeService


class _FakeQuartoTable:
    def __init__(self):
        self.rows = [
            SimpleNamespace(numero="101", tipoSuite="LUXO", status="LIVRE"),
            SimpleNamespace(numero="102", tipoSuite="LUXO", status="LIVRE"),
        ]

    async def find_unique(self, where):
        numero = where["numero"]
        return next((q for q in self.rows if q.numero == numero), None)

    async def find_many(self, where=None):
        rows = self.rows
        if where and "tipoSuite" in where:
            rows = [q for q in rows if q.tipoSuite == where["tipoSuite"]]
        if where and "status" in where and "notIn" in where["status"]:
            blocked = set(where["status"]["notIn"])
            rows = [q for q in rows if q.status not in blocked]
        return rows


class _FakeReservaTable:
    def __init__(self):
        self.rows = [
            SimpleNamespace(
                id=1,
                codigoReserva="RCF-1",
                clienteNome="Cliente",
                quartoNumero="101",
                statusReserva="CONFIRMADA",
                checkinPrevisto=datetime(2026, 6, 10, 12),
                checkoutPrevisto=datetime(2026, 6, 12, 11),
            )
        ]

    async def find_many(self, where=None, include=None):
        rows = self.rows

        quarto_filter = (where or {}).get("quartoNumero")
        if isinstance(quarto_filter, dict) and "in" in quarto_filter:
            allowed = set(quarto_filter["in"])
            rows = [r for r in rows if r.quartoNumero in allowed]
        elif quarto_filter:
            rows = [r for r in rows if r.quartoNumero == quarto_filter]

        status_filter = ((where or {}).get("statusReserva") or {}).get("in")
        if status_filter:
            allowed_status = set(status_filter)
            rows = [r for r in rows if r.statusReserva in allowed_status]

        checkin_lt = ((where or {}).get("checkinPrevisto") or {}).get("lt")
        checkout_gt = ((where or {}).get("checkoutPrevisto") or {}).get("gt")
        if checkin_lt is not None:
            rows = [r for r in rows if r.checkinPrevisto < checkin_lt]
        if checkout_gt is not None:
            rows = [r for r in rows if r.checkoutPrevisto > checkout_gt]

        return rows


class _FakeDb:
    def __init__(self):
        self.quarto = _FakeQuartoTable()
        self.reserva = _FakeReservaTable()


@pytest.mark.asyncio
async def test_disponibilidade_permita_reserva_colada_no_checkout():
    service = DisponibilidadeService(_FakeDb())

    result = await service.verificar_disponibilidade(
        "101",
        datetime(2026, 6, 12, 11),
        datetime(2026, 6, 14, 11),
    )

    assert result["disponivel"] is True


@pytest.mark.asyncio
async def test_disponibilidade_bloqueia_reserva_sobreposta():
    service = DisponibilidadeService(_FakeDb())

    result = await service.verificar_disponibilidade(
        "101",
        datetime(2026, 6, 11, 12),
        datetime(2026, 6, 13, 11),
    )

    assert result["disponivel"] is False
    assert result["conflitos"][0]["codigo"] == "RCF-1"


@pytest.mark.asyncio
async def test_listar_quartos_disponiveis_remove_apenas_quartos_com_conflito():
    service = DisponibilidadeService(_FakeDb())

    result = await service.listar_quartos_disponiveis(
        datetime(2026, 6, 11, 12),
        datetime(2026, 6, 13, 11),
        "LUXO",
    )

    assert [q["numero"] for q in result] == ["102"]
