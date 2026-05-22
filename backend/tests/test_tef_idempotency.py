import pytest
import sys
import types

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


class FakePagamentoRepo:
    def __init__(self):
        self.by_key = {}
        self.created = 0
        self.updated = 0

    async def get_by_idempotency_key(self, idempotency_key):
        return self.by_key.get(idempotency_key)

    async def create(self, pagamento, idempotency_key=None):
        self.created += 1
        registro = {
            "id": self.created,
            "reserva_id": pagamento.reserva_id,
            "valor": pagamento.valor,
            "metodo": pagamento.metodo,
            "status": "PENDENTE",
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


@pytest.mark.asyncio
async def test_pagamento_tef_finalizado_reusa_idempotency_key():
    repo = FakePagamentoRepo()
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
    assert repo.created == 1
    assert repo.updated == 1


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
