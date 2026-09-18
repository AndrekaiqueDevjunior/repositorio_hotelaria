from datetime import datetime, timedelta
import json

from app.utils.json_utils import to_json_safe
from app.schemas.pagamento_schema import PagamentoCreate
from app.schemas.reserva_schema import ReservaCreate


def test_reserva_create_aceita_campos_operacionais_do_voucher():
    checkin = datetime.now()
    checkout = checkin + timedelta(days=2)

    reserva = ReservaCreate(
        cliente_id=1,
        quarto_numero="101",
        tipo_suite="LUXO",
        checkin_previsto=checkin,
        checkout_previsto=checkout,
        valor_diaria=250,
        valor_total=500,
        num_diarias=2,
        origem="BOOKING",
        responsavel_nome="Recepcao",
        forma_pagamento="PIX",
        observacoes="Reserva via canal externo",
        telefone_contato="22999999999",
        email_contato="hospede@example.com",
    )

    assert reserva.origem == "BOOKING"
    assert reserva.responsavel_nome == "Recepcao"
    assert reserva.forma_pagamento == "PIX"
    assert reserva.valor_total == 500
    assert reserva.telefone_contato == "22999999999"
    assert reserva.email_contato == "hospede@example.com"


def test_pagamento_create_normaliza_metodos_operacionais():
    assert PagamentoCreate(reserva_id=1, valor=10, metodo="DINHEIRO").metodo == "na_chegada"
    assert PagamentoCreate(reserva_id=1, valor=10, metodo="CREDITO").metodo == "credit_card"
    assert PagamentoCreate(reserva_id=1, valor=10, metodo="DEBITO").metodo == "debit_card"
    assert PagamentoCreate(reserva_id=1, valor=10, metodo="PIX").metodo == "pix"


def test_resposta_da_reserva_converte_datetime_antes_do_json():
    payload = to_json_safe({
        "success": True,
        "data": {"created_at": datetime(2026, 9, 18, 12, 0, 0)},
    })

    assert json.dumps(payload)
    assert payload["data"]["created_at"] == "2026-09-18T12:00:00"
