from datetime import datetime
from types import SimpleNamespace

from app.repositories.reserva_repo import ReservaRepository
from app.utils.payment_status import (
    normalizar_status_pagamento_persistido,
    normalizar_status_pagamento_publico,
)


def _reserva(status_pagamento="PENDENTE"):
    agora = datetime(2026, 9, 18, 12, 0, 0)
    pagamento = SimpleNamespace(
        id=10,
        statusPagamento=status_pagamento,
        valor=400.0,
        metodo="tef",
        createdAt=agora,
    )
    voucher = SimpleNamespace(id=7, codigo="HR-2026-000007", status="EMITIDO")
    return SimpleNamespace(
        id=1,
        codigoReserva="RCF-TESTE",
        clienteId=2,
        clienteNome="Cliente Teste",
        quartoNumero="107",
        tipoSuite="LUXO",
        statusReserva="CONFIRMADA",
        checkinPrevisto=agora,
        checkoutPrevisto=agora,
        checkinReal=None,
        checkoutReal=None,
        valorDiaria=100.0,
        valorTotal=400.0,
        numDiarias=4,
        pagamentos=[pagamento],
        voucher=voucher,
        hospedagem=None,
        cupomUso=None,
        cliente=None,
        createdAt=agora,
        updatedAt=agora,
    )


def test_status_publicos_preservam_pending_e_processing():
    assert normalizar_status_pagamento_publico("PENDENTE") == "pending"
    assert normalizar_status_pagamento_publico("PROCESSANDO") == "processing"
    assert normalizar_status_pagamento_publico("PAGO") == "paid"
    assert normalizar_status_pagamento_publico("FALHOU") == "failed"
    assert normalizar_status_pagamento_publico("CANCELADO") == "cancelled"
    assert normalizar_status_pagamento_publico("ESTORNADO") == "refunded"
    assert normalizar_status_pagamento_persistido("PENDENTE") == "PENDENTE"
    assert normalizar_status_pagamento_persistido("PROCESSANDO") == "PROCESSANDO"
    assert normalizar_status_pagamento_persistido("AGUARDANDO_PAGAMENTO") == "PROCESSANDO"


def test_reserva_serializa_estados_separados_e_voucher_disponivel():
    payload = ReservaRepository(SimpleNamespace())._serialize_reserva(_reserva())

    assert payload["reservation_status"] == "CONFIRMADA"
    assert payload["payment_status"] == "pending"
    assert payload["payment_status_raw"] == "PENDENTE"
    assert payload["voucher_available"] is True
    assert payload["voucher"]["codigo"] == "HR-2026-000007"


def test_recarregar_reserva_nao_converte_pending_em_processing():
    repo = ReservaRepository(SimpleNamespace())

    primeiro = repo._serialize_reserva(_reserva("PENDENTE"))
    segundo = repo._serialize_reserva(_reserva("PENDENTE"))

    assert primeiro["payment_status"] == segundo["payment_status"] == "pending"


def test_pagamento_falhou_sem_remover_voucher():
    payload = ReservaRepository(SimpleNamespace())._serialize_reserva(_reserva("FALHOU"))

    assert payload["reservation_status"] == "CONFIRMADA"
    assert payload["payment_status"] == "failed"
    assert payload["voucher_available"] is True
