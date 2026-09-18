from contextlib import asynccontextmanager
from types import SimpleNamespace

import pytest

from app.repositories.pagamento_repo import PagamentoRepository
from app.services.reserva_publica_confirmation_service import (
    ReservaPublicaConfirmationService,
)


class _ReservaTable:
    def __init__(self):
        self.current = SimpleNamespace(id=31, statusReserva="PENDENTE")
        self.updated_data = None

    async def find_unique(self, where):
        return self.current if where["id"] == self.current.id else None

    async def update(self, where, data):
        self.updated_data = data
        self.current.statusReserva = data["statusReserva"]
        return self.current


class _HospedagemTable:
    def __init__(self):
        self.created_data = None

    async def find_unique(self, where):
        return None

    async def create(self, data):
        self.created_data = data
        return SimpleNamespace(**data)


class _FakeDb:
    def __init__(self):
        self.reserva = _ReservaTable()
        self.hospedagem = _HospedagemTable()

    @asynccontextmanager
    async def tx(self):
        yield self


@pytest.mark.asyncio
async def test_mantem_reserva_pendente_com_pagamento_pendente_e_voucher(monkeypatch):
    db = _FakeDb()
    pagamento_args = {}

    async def criar_pagamento(self, pagamento, idempotency_key=None, status_inicial=None, db=None):
        pagamento_args.update(
            reserva_id=pagamento.reserva_id,
            valor=pagamento.valor,
            metodo=pagamento.metodo,
            idempotency_key=idempotency_key,
            status_inicial=status_inicial,
        )
        return {"id": 90, "status": "PENDENTE"}

    async def emitir_voucher(reserva_id, emitido_por=None, db=None):
        assert db is not None
        return {"id": 44, "codigo": "HR-2026-000044", "status": "EMITIDO"}

    monkeypatch.setattr(PagamentoRepository, "create", criar_pagamento)
    monkeypatch.setattr(
        "app.services.reserva_publica_confirmation_service.gerar_voucher",
        emitir_voucher,
    )

    resultado = await ReservaPublicaConfirmationService(db).registrar_pagamento_pendente_e_voucher(
        reserva_id=31,
        valor_total=640.0,
    )

    assert db.reserva.updated_data is None
    assert resultado["reserva"].statusReserva == "PENDENTE"
    assert db.hospedagem.created_data == {"reservaId": 31, "statusHospedagem": "NAO_INICIADA"}
    assert pagamento_args == {
        "reserva_id": 31,
        "valor": 640.0,
        "metodo": "tef",
        "idempotency_key": "reserva-publica-pendente:31",
        "status_inicial": "PENDENTE",
    }
    assert resultado["pagamento"]["status"] == "PENDENTE"
    assert resultado["voucher"]["codigo"] == "HR-2026-000044"


@pytest.mark.asyncio
async def test_nao_inicia_fluxo_fora_do_estado_pendente():
    db = _FakeDb()
    db.reserva.current.statusReserva = "CANCELADO"

    with pytest.raises(ValueError, match="nao pode iniciar o pagamento"):
        await ReservaPublicaConfirmationService(db).registrar_pagamento_pendente_e_voucher(
            reserva_id=31,
            valor_total=640.0,
        )
