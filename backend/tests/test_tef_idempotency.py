import pytest
import sys
import types
import asyncio

sys.modules.setdefault(
    "requests",
    types.SimpleNamespace(RequestException=Exception),
)

fake_cielo_service = types.ModuleType("app.services.cielo_service")


class FakeCieloAPI:
    pass


fake_cielo_service.CieloAPI = FakeCieloAPI
sys.modules.setdefault("app.services.cielo_service", fake_cielo_service)

fake_cache_module = types.ModuleType("app.core.cache")


class FakeCache:
    redis = None

    async def get(self, key):
        return None

    async def set(self, key, value, ttl=300):
        return None

    async def delete(self, key):
        return None


fake_cache_module.cache = FakeCache()
sys.modules.setdefault("app.core.cache", fake_cache_module)

fake_utils_cache_module = types.ModuleType("app.utils.cache")


def fake_cache_result(*args, **kwargs):
    def decorator(func):
        return func
    return decorator


def fake_invalidate_cache_pattern(*args, **kwargs):
    return None


fake_utils_cache_module.cache_result = fake_cache_result
fake_utils_cache_module.invalidate_cache_pattern = fake_invalidate_cache_pattern
sys.modules.setdefault("app.utils.cache", fake_utils_cache_module)

from app.services.pagamento_service import PagamentoService
from app.services.tef_service import TEF_FINALIZED_SESSIONS, TEF_INTERACTIVE_SESSIONS, TefService


class FakeTxReserva:
    async def find_unique(self, where):
        return types.SimpleNamespace(statusReserva="PENDENTE")

    async def update(self, where, data):
        return types.SimpleNamespace(id=where["id"], **data)


class NoopTx:
    def __init__(self):
        self.reserva = FakeTxReserva()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeRepoDb:
    def tx(self):
        return NoopTx()


class FakePagamentoRepo:
    def __init__(self, valor_oficial=100.0):
        self.by_key = {}
        self.created = 0
        self.updated = 0
        self.valor_oficial = valor_oficial
        self.valor_consultas = []
        self.db = FakeRepoDb()

    async def get_by_idempotency_key(self, idempotency_key):
        return self.by_key.get(idempotency_key)

    async def obter_valor_esperado_reserva(self, reserva_id, reserva=None):
        self.valor_consultas.append(reserva_id)
        return self.valor_oficial

    async def create(self, pagamento, idempotency_key=None, db=None, status_inicial=None):
        self.created += 1
        registro = {
            "id": self.created,
            "reserva_id": pagamento.reserva_id,
            "valor": pagamento.valor,
            "metodo": pagamento.metodo,
            "status": status_inicial or "PENDENTE",
        }
        if idempotency_key:
            self.by_key[idempotency_key] = registro
        return registro

    async def update_status(self, pagamento_id, status, **kwargs):
        self.updated += 1
        for registro in self.by_key.values():
            if registro["id"] == pagamento_id:
                registro.update(
                    {
                        "status": "PAGO" if status == "APROVADO" else status,
                        "nsu": kwargs.get("cielo_payment_id"),
                        "tef_autorizacao": kwargs.get("tef_autorizacao"),
                    }
                )
                return dict(registro)
        return {"id": pagamento_id, "status": status}


class FakeStartTefService:
    def __init__(self):
        self.calls = []

    async def iniciar_fluxo_interativo(self, **kwargs):
        self.calls.append(kwargs)
        return {"success": True, "session_id": kwargs.get("session_id"), "valor": kwargs["valor"]}


class FakeTefService:
    async def finalizar_fluxo_interativo(self, session_id, confirm, param_adic=None):
        return {
            "success": True,
            "finalizado": True,
            "aprovado": True,
            "status": "APROVADO",
            "nsu": "123456",
            "autorizacao": "999999",
            "message": "Transacao aprovada",
        }


class SlowCountingTefService:
    def __init__(self):
        self.calls = 0

    async def finalizar_fluxo_interativo(self, session_id, confirm, param_adic=None):
        self.calls += 1
        await asyncio.sleep(0.02)
        return {
            "success": True,
            "finalizado": True,
            "aprovado": True,
            "status": "APROVADO",
            "nsu": "123456",
            "autorizacao": "999999",
            "message": "Transacao aprovada",
        }


class SlowPagamentoRepo(FakePagamentoRepo):
    async def create(self, pagamento, idempotency_key=None, db=None, status_inicial=None):
        await asyncio.sleep(0.02)
        return await super().create(
            pagamento,
            idempotency_key=idempotency_key,
            db=db,
            status_inicial=status_inicial,
        )


@pytest.mark.asyncio
async def test_iniciar_fluxo_tef_usa_valor_oficial_com_desconto():
    repo = FakePagamentoRepo(valor_oficial=90.0)
    service = PagamentoService(repo)
    service.tef_service = FakeStartTefService()

    result = await service.iniciar_fluxo_tef(
        reserva_id=10,
        valor=100.0,
        session_id="sess-cupom",
    )

    assert result["success"] is True
    assert service.tef_service.calls[0]["valor"] == 90.0
    assert repo.valor_consultas == [10]


@pytest.mark.asyncio
async def test_pagamento_tef_finalizado_reusa_idempotency_key():
    repo = FakePagamentoRepo(valor_oficial=90.0)
    service = PagamentoService(repo)
    service.tef_service = FakeTefService()

    primeiro = await service.finalizar_fluxo_tef(
        reserva_id=10,
        valor=100.0,
        session_id="sess-1",
        confirm=True,
        idempotency_key="tef-chave-1",
    )
    segundo = await service.finalizar_fluxo_tef(
        reserva_id=10,
        valor=100.0,
        session_id="sess-1",
        confirm=True,
        idempotency_key="tef-chave-1",
    )

    assert primeiro["success"] is True
    assert segundo["idempotent_replay"] is True
    assert primeiro["valor"] == 90.0
    assert repo.created == 1
    assert repo.updated == 1


@pytest.mark.asyncio
async def test_pagamento_tef_finalizado_concorrente_usa_um_registro():
    repo = SlowPagamentoRepo()
    tef_service = SlowCountingTefService()
    service = PagamentoService(repo)
    service.tef_service = tef_service

    primeiro, segundo = await asyncio.gather(
        service.finalizar_fluxo_tef(
            reserva_id=10,
            valor=100.0,
            session_id="sess-race",
            confirm=True,
            idempotency_key="tef-chave-race",
        ),
        service.finalizar_fluxo_tef(
            reserva_id=10,
            valor=100.0,
            session_id="sess-race",
            confirm=True,
            idempotency_key="tef-chave-race",
        ),
    )

    assert primeiro["success"] is True
    assert segundo["success"] is True
    assert segundo["idempotent_replay"] is True
    assert repo.created == 1
    assert repo.updated == 1
    assert tef_service.calls == 1


@pytest.mark.asyncio
async def test_finalizar_fluxo_interativo_replay_de_sessao_finalizada(monkeypatch):
    TEF_INTERACTIVE_SESSIONS.clear()
    TEF_FINALIZED_SESSIONS.clear()
    service = TefService()
    calls = {"finish": 0}

    TEF_INTERACTIVE_SESSIONS["sess-final"] = {
        "session_id": "sess-final",
        "tax_invoice_number": "123",
        "tax_invoice_date": "20260522",
        "tax_invoice_time": "120000",
        "function_id": 3,
        "aprovado_pre_finish": True,
        "cupom_cliente": "cupom cliente",
        "cupom_estabelecimento": "cupom loja",
        "nsu": "123456",
        "autorizacao": "999999",
        "tipo_campos": [],
        "nfpag": {},
        "eventos": [],
        "created_at": __import__("datetime").datetime.now(),
        "last_activity_at": __import__("datetime").datetime.now(),
    }

    def fake_request(method, path, payload):
        calls["finish"] += 1
        return {"serviceStatus": 0, "serviceMessage": "Transacao aprovada"}

    async def fake_store_reference(session):
        return None

    monkeypatch.setattr(service, "_request", fake_request)
    monkeypatch.setattr(service, "_store_approved_transaction_reference", fake_store_reference)

    primeiro = await service.finalizar_fluxo_interativo("sess-final", confirm=True)
    segundo = await service.finalizar_fluxo_interativo("sess-final", confirm=True)

    assert primeiro["success"] is True
    assert segundo["idempotent_replay"] is True
    assert segundo["nsu"] == "123456"
    assert calls["finish"] == 1


@pytest.mark.asyncio
async def test_fluxo_real_cria_sessao_remota_e_preserva_idempotency_key(monkeypatch):
    TEF_INTERACTIVE_SESSIONS.clear()
    TEF_FINALIZED_SESSIONS.clear()
    service = TefService()
    service.agente_mode = "real"
    calls = []

    def fake_request(method, path, payload=None):
        payload = payload or {}
        calls.append((method, path, dict(payload)))
        if path == "/session":
            return {"serviceStatus": 0, "sessionId": "remote-1"}
        if path == "/startTransaction":
            assert payload["sessionId"] == "remote-1"
            return {"serviceStatus": 0, "clisitefStatus": 10000, "sessionId": "remote-1"}
        if path == "/continueTransaction":
            assert payload["sessionId"] == "remote-1"
            return {
                "serviceStatus": 0,
                "clisitefStatus": 10000,
                "commandId": 21,
                "fieldId": 0,
                "fieldMinLength": 1,
                "fieldMaxLength": 1,
                "data": "1:Credito",
            }
        raise AssertionError(f"chamada inesperada: {method} {path}")

    monkeypatch.setattr(service, "_request", fake_request)

    result = await service.iniciar_fluxo_interativo(
        valor=10.0,
        reserva_id=123,
        function_id=3,
        session_id="idem-1",
    )

    assert result["success"] is True
    assert result["session_id"] == "idem-1"
    assert TEF_INTERACTIVE_SESSIONS["idem-1"]["remote_session_id"] == "remote-1"
    assert [call[1] for call in calls] == ["/session", "/startTransaction", "/continueTransaction"]


@pytest.mark.asyncio
async def test_finalizar_fluxo_real_usa_sessao_remota(monkeypatch):
    TEF_INTERACTIVE_SESSIONS.clear()
    TEF_FINALIZED_SESSIONS.clear()
    service = TefService()
    service.agente_mode = "real"

    TEF_INTERACTIVE_SESSIONS["idem-2"] = {
        "session_id": "idem-2",
        "remote_session_id": "remote-2",
        "tax_invoice_number": "123",
        "tax_invoice_date": "20260522",
        "tax_invoice_time": "120000",
        "function_id": 3,
        "aprovado_pre_finish": True,
        "cupom_cliente": "",
        "cupom_estabelecimento": "",
        "nsu": "123456",
        "autorizacao": "999999",
        "tipo_campos": [],
        "nfpag": {},
        "eventos": [],
        "created_at": __import__("datetime").datetime.now(),
        "last_activity_at": __import__("datetime").datetime.now(),
    }

    def fake_request(method, path, payload):
        assert path == "/finishTransaction"
        assert payload["sessionId"] == "remote-2"
        return {"serviceStatus": 0, "serviceMessage": "Transacao aprovada"}

    async def fake_store_reference(session):
        return None

    monkeypatch.setattr(service, "_request", fake_request)
    monkeypatch.setattr(service, "_store_approved_transaction_reference", fake_store_reference)

    result = await service.finalizar_fluxo_interativo("idem-2", confirm=True)

    assert result["success"] is True
    assert result["finalizado"] is True
