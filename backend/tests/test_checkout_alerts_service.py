from types import SimpleNamespace

import pytest

from app.services.checkout_alert_service import CheckoutAlertService
from app.utils.datetime_utils import now_utc


class FakeNotificationModel:
    def __init__(self):
        self.created = []

    async def find_first(self, where=None):
        return None

    async def create(self, data):
        self.created.append(data)
        return SimpleNamespace(
            id=44,
            titulo=data["titulo"],
            mensagem=data["mensagem"],
            tipo=data["tipo"],
            categoria=data["categoria"],
            perfil=data.get("perfil"),
            lida=False,
            reservaId=data.get("reservaId"),
            pagamentoId=data.get("pagamentoId"),
            urlAcao=data.get("urlAcao"),
            dataCriacao=now_utc(),
        )


class FakeDbCheckoutAlerts:
    def __init__(self):
        self.notificacao = FakeNotificationModel()
        self.mark_seen = False

    async def query_raw(self, query, *args):
        if "UPDATE notificacoes" in query:
            self.mark_seen = True
            return [{"id": 44}]
        return [{
            "id": 10,
            "codigo_reserva": "RES-10",
            "cliente_nome": "Joao Silva",
            "quarto_numero": "201",
            "checkout_previsto": now_utc(),
            "status_reserva": "HOSPEDADO",
            "status_hospedagem": "CHECKIN_REALIZADO",
            "notificacao_id": None,
        }]


@pytest.mark.asyncio
async def test_checkout_alert_pending_cria_notificacao_e_payload_sonoro():
    db = FakeDbCheckoutAlerts()
    service = CheckoutAlertService(db)

    result = await service.listar_pendentes(limit=20)

    assert result["success"] is True
    assert result["total"] == 1
    alert = result["alerts"][0]
    assert alert["reservation_id"] == 10
    assert alert["room"] == "201"
    assert alert["viewed"] is False
    assert alert["alert_sound"] is True
    assert db.notificacao.created[0]["categoria"] == "checkout_pendente"


@pytest.mark.asyncio
async def test_checkout_alert_marcar_visto():
    db = FakeDbCheckoutAlerts()
    service = CheckoutAlertService(db)

    result = await service.marcar_visto(10)

    assert result["success"] is True
    assert result["viewed"] is True
    assert result["notifications_marked"] == 1
    assert db.mark_seen is True

