import os

import pytest

os.environ.setdefault("CIELO_MERCHANT_ID", "test-merchant")
os.environ.setdefault("CIELO_MERCHANT_KEY", "test-key")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")

from app.api.v1 import jornada_routes


class FakePontosRepository:
    def __init__(self, db):
        self.db = db

    async def get_saldo(self, customer_id):
        return {"success": True, "saldo": 72}


class FakeProgramaPontosService:
    def __init__(self, db):
        self.db = db

    async def obter_programa_cliente(self, customer_id):
        return {
            "success": True,
            "nivel": {"nome": "EXPERIENCIA", "pontos_minimos": 50, "bonus_percentual": 20},
            "saldo_atual": 72,
            "total_pontos_nivel": 72,
            "total_resgatado": 20,
            "rewards_unlocked": 2,
            "rewards_total": 4,
            "barra_nivel": {
                "meta": 90,
                "faltam_pontos": 18,
                "percentual": 55,
                "proximo_nivel": {"nome": "REAL", "pontos_minimos": 90, "bonus_percentual": 40},
            },
            "barra_premios": {
                "meta": 90,
                "faltam_pontos": 18,
                "percentual": 80,
                "rewards_unlocked": 2,
                "rewards_total": 4,
            },
            "proximo_premio": {"id": 3, "nome": "iPhone 16", "preco_em_pontos": 90},
        }


class FakeDisponibilidadeService:
    last_call = None

    def __init__(self, db):
        self.db = db

    async def listar_quartos_disponiveis(self, checkin, checkout, tipo_suite):
        FakeDisponibilidadeService.last_call = {
            "checkin": checkin,
            "checkout": checkout,
            "tipo_suite": tipo_suite,
        }
        return [
            {"numero": "203", "tipo_suite": "REAL", "status": "LIVRE"},
        ]


@pytest.mark.asyncio
async def test_loyalty_customer_expoe_progresso_de_premios(monkeypatch):
    async def fake_get_customer_by_document(customer_ref):
        return {"id": 10, "nome_completo": "Joao Silva", "documento": customer_ref}

    monkeypatch.setattr(jornada_routes, "_get_customer_by_document", fake_get_customer_by_document)
    monkeypatch.setattr(jornada_routes, "get_db", lambda: object())
    monkeypatch.setattr(jornada_routes, "PontosRepository", FakePontosRepository)
    monkeypatch.setattr(jornada_routes, "ProgramaPontosService", FakeProgramaPontosService)

    result = await jornada_routes.obter_loyalty_customer("52998224725", _rate_limit=None)

    assert result["redeemable_points"] == 72
    assert result["rewards_unlocked"] == 2
    assert result["rewards_total"] == 4
    assert result["barra_premios"]["rewards_unlocked"] == 2
    assert result["barra_premios"]["rewards_total"] == 4


@pytest.mark.asyncio
async def test_availability_alias_lista_quartos_disponiveis(monkeypatch):
    monkeypatch.setattr(jornada_routes, "get_db", lambda: object())
    monkeypatch.setattr(jornada_routes, "DisponibilidadeService", FakeDisponibilidadeService)

    result = await jornada_routes.listar_availability(
        checkin="2026-06-16",
        checkout="2026-06-18",
        suite_type="real",
        _rate_limit=None,
    )

    assert result == [
        {
            "room_id": "203",
            "room": "203",
            "numero": "203",
            "suite_type": "REAL",
            "tipo_suite": "REAL",
            "status": "LIVRE",
            "available": True,
            "disponivel": True,
        }
    ]
    assert FakeDisponibilidadeService.last_call["tipo_suite"] == "REAL"
