from datetime import timedelta
from types import SimpleNamespace

import pytest

from app.repositories.pontos_repo import PontosRepository
from app.services import notification_service
from app.services.notification_service import NotificationService
from app.utils.datetime_utils import now_utc


class FakeNotificationModel:
    def __init__(self):
        self.created = []
        self.find_first_result = None

    async def find_first(self, where=None):
        return self.find_first_result

    async def create(self, data):
        self.created.append(data)
        return SimpleNamespace(
            id=77,
            titulo=data["titulo"],
            mensagem=data["mensagem"],
            tipo=data["tipo"],
            categoria=data["categoria"],
            perfil=data.get("perfil"),
            lida=data.get("lida", False),
            reservaId=data.get("reservaId"),
            pagamentoId=data.get("pagamentoId"),
            urlAcao=data.get("urlAcao"),
            dataCriacao=now_utc(),
        )


class FakeClienteModel:
    async def find_unique(self, where):
        return SimpleNamespace(
            id=10,
            nomeCompleto="Joao Silva",
            documento="11144477735",
            telefone="+5522999990000",
        )


class FakeDbPremioProximo:
    def __init__(self, log_exists=False):
        self.log_exists = log_exists
        self.notificacao = FakeNotificationModel()
        self.cliente = FakeClienteModel()
        self.execute_calls = []

    async def query_raw(self, query, *args):
        if "FROM logs_jornada" in query:
            return [{"id": 1}] if self.log_exists else []
        return []

    async def execute_raw(self, *args):
        self.execute_calls.append(args)
        return 1


class FakeProgramaPremio:
    def __init__(self, db):
        self.db = db

    async def obter_programa_cliente(self, cliente_id):
        return {
            "success": True,
            "saldo_atual": 85,
            "premio_proximo": True,
            "faltam_pontos_para_proximo_premio": 5,
            "proximo_premio": {"id": 90, "nome": "iPhone 16e", "preco_em_pontos": 90},
        }


class FakeWhatsAppPremio:
    def __init__(self):
        self.calls = []

    async def enviar_aviso_premio_proximo(self, **kwargs):
        self.calls.append(kwargs)
        return {"success": True, "message_sid": "SM-PREMIO"}


@pytest.mark.asyncio
async def test_premio_proximo_envia_whatsapp_e_registra_dedupe(monkeypatch):
    import app.services.programa_pontos_service as programa_module

    fake_whatsapp = FakeWhatsAppPremio()
    monkeypatch.setattr(programa_module, "ProgramaPontosService", FakeProgramaPremio)
    monkeypatch.setattr(notification_service, "get_whatsapp_service", lambda: fake_whatsapp)

    db = FakeDbPremioProximo(log_exists=False)
    notificacao = await NotificationService.notificar_premio_proximo(db, cliente_id=10)

    assert notificacao["id"] == 77
    assert fake_whatsapp.calls[0]["premio_nome"] == "iPhone 16e"
    assert fake_whatsapp.calls[0]["pontos_faltantes"] == 5
    assert any(call[2] == "premio_proximo_whatsapp" for call in db.execute_calls)


@pytest.mark.asyncio
async def test_premio_proximo_nao_duplica_no_mesmo_dia(monkeypatch):
    import app.services.programa_pontos_service as programa_module

    fake_whatsapp = FakeWhatsAppPremio()
    monkeypatch.setattr(programa_module, "ProgramaPontosService", FakeProgramaPremio)
    monkeypatch.setattr(notification_service, "get_whatsapp_service", lambda: fake_whatsapp)

    db = FakeDbPremioProximo(log_exists=True)
    notificacao = await NotificationService.notificar_premio_proximo(db, cliente_id=10)

    assert notificacao is None
    assert fake_whatsapp.calls == []


class FakeDbPontosLiberados:
    def __init__(self):
        self.execute_calls = []

    async def query_raw(self, query, *args):
        if "FROM logs_jornada" in query:
            return []
        if "FROM clientes" in query:
            return [{
                "nome_completo": "Joao Silva",
                "telefone": "+5522999990000",
                "documento": "11144477735",
                "codigo_reserva": "RES-10",
            }]
        return []

    async def execute_raw(self, *args):
        self.execute_calls.append(args)
        return 1


class FakeProgramaSaldo:
    def __init__(self, db):
        self.db = db

    async def obter_programa_cliente(self, cliente_id):
        return {
            "success": True,
            "saldo_atual": 132,
            "faltam_pontos_para_proximo_premio": 8,
            "proximo_premio": {"nome": "Jantar Real"},
        }


class FakeWhatsAppCheckout:
    def __init__(self):
        self.calls = []

    async def enviar_pontos_pos_checkout(self, **kwargs):
        self.calls.append(kwargs)
        return {"success": True, "message_sid": "SM-CHECKOUT"}


@pytest.mark.asyncio
async def test_pontos_liberados_disparam_whatsapp_pos_checkout(monkeypatch):
    import app.repositories.pontos_repo as pontos_module
    import app.services.programa_pontos_service as programa_module
    from app.services import notification_service as notification_module

    fake_whatsapp = FakeWhatsAppCheckout()
    monkeypatch.setattr(programa_module, "ProgramaPontosService", FakeProgramaSaldo)
    monkeypatch.setattr(pontos_module, "get_whatsapp_service", lambda: fake_whatsapp, raising=False)
    monkeypatch.setattr("app.services.whatsapp_service.get_whatsapp_service", lambda: fake_whatsapp)

    async def fake_notificar(db, cliente_id, reserva_id=None):
        return None

    monkeypatch.setattr(notification_module.NotificationService, "notificar_premio_proximo", fake_notificar)

    db = FakeDbPontosLiberados()
    repo = PontosRepository(db)
    await repo._notificar_pontos_liberados({
        "transacao_id": 123,
        "cliente_id": 10,
        "reserva_id": 10,
        "origem": "CHECKOUT",
        "pontos": 60,
        "saldo_posterior": 132,
        "metadata": {"bonus_percentual": 20, "pontos_bonus_nivel": 10},
    })

    assert fake_whatsapp.calls[0]["pontos_ganhos_checkout"] == 60
    assert fake_whatsapp.calls[0]["bonus_percentual"] == 20
    assert any(call[2] == "pontos_pos_checkout_whatsapp" for call in db.execute_calls)
