from datetime import timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.services.cupom_service import (
    CUPOM_AMIGO_DESCONTO_PADRAO,
    CUPOM_AMIGO_LIMITE_USOS_PADRAO,
    CupomService,
)
from app.utils.datetime_utils import now_utc


class FakeClienteTable:
    async def find_unique(self, where):
        return SimpleNamespace(id=where["id"], nomeCompleto="Joana da Silva")


class FakeMeuCupomRepo:
    def __init__(self):
        self.db = SimpleNamespace(cliente=FakeClienteTable())
        self.cupom_amigo = None
        self.created = None

    async def get_amigo_by_cliente(self, cliente_id):
        return dict(self.cupom_amigo) if self.cupom_amigo else None

    async def get_by_codigo(self, codigo):
        return None

    async def create(self, data, criado_por=None):
        self.created = {"data": data, "criado_por": criado_por}
        cupom = {
            "id": 33,
            "codigo": data["codigo"],
            "descricao": data.get("descricao"),
            "tipo_desconto": data["tipo_desconto"],
            "valor_desconto": float(data["valor_desconto"]),
            "pontos_bonus": data.get("pontos_bonus") or 0,
            "data_inicio": data["data_inicio"].isoformat(),
            "data_fim": data["data_fim"].isoformat(),
            "limite_total_usos": data.get("limite_total_usos"),
            "limite_por_cliente": data.get("limite_por_cliente"),
            "total_usos": 0,
            "ativo": data.get("ativo", True),
            "status": "active",
            "tipo_campanha": data.get("tipo_campanha"),
            "cliente_indicador_id": data.get("cliente_indicador_id"),
        }
        self.cupom_amigo = cupom
        return dict(cupom)

    async def get_admin_by_codigo(self, codigo, include_usages=True, usage_limit=25):
        return {"codigo": codigo, "usages": [{"customer_name": "Pedro Alves", "discount_amount": 50.0}]}


def _cupom_amigo(**overrides):
    cupom = {
        "id": 1,
        "codigo": "AMIGO5AB12",
        "valor_desconto": 10.0,
        "pontos_bonus": 0,
        "data_fim": (now_utc() + timedelta(days=30)).isoformat(),
        "limite_total_usos": 5,
        "total_usos": 0,
        "ativo": True,
        "status": "active",
        "tipo_campanha": "CUPOM_AMIGO",
        "cliente_indicador_id": 5,
    }
    cupom.update(overrides)
    return cupom


@pytest.mark.asyncio
async def test_meu_cupom_cria_automaticamente_quando_nao_existe():
    repo = FakeMeuCupomRepo()
    service = CupomService(repo)

    cupom = await service.obter_ou_criar_cupom_amigo_cliente(5)

    assert repo.created is not None
    assert repo.created["data"]["tipo_campanha"] == "CUPOM_AMIGO"
    assert repo.created["data"]["cliente_indicador_id"] == 5
    assert repo.created["data"]["valor_desconto"] == CUPOM_AMIGO_DESCONTO_PADRAO
    assert repo.created["data"]["limite_total_usos"] == CUPOM_AMIGO_LIMITE_USOS_PADRAO
    assert cupom["status_efetivo"] == "active"
    assert cupom["link_rastreado"].startswith("http")
    assert "cupom=" in cupom["link_rastreado"]


@pytest.mark.asyncio
async def test_meu_cupom_devolve_existente_com_links_sem_criar_outro():
    repo = FakeMeuCupomRepo()
    repo.cupom_amigo = _cupom_amigo()
    service = CupomService(repo)

    cupom = await service.obter_ou_criar_cupom_amigo_cliente(5)

    assert repo.created is None
    assert cupom["codigo"] == "AMIGO5AB12"
    assert cupom["status_efetivo"] == "active"
    assert "AMIGO5AB12" in cupom["link_rastreado"]


@pytest.mark.asyncio
async def test_status_efetivo_detecta_expirado_por_data_mesmo_com_status_active():
    repo = FakeMeuCupomRepo()
    repo.cupom_amigo = _cupom_amigo(data_fim=(now_utc() - timedelta(days=1)).isoformat())
    service = CupomService(repo)

    cupom = await service.obter_ou_criar_cupom_amigo_cliente(5)

    assert cupom["status_efetivo"] == "expired"


@pytest.mark.asyncio
async def test_status_efetivo_detecta_esgotado_por_limite_de_usos():
    repo = FakeMeuCupomRepo()
    repo.cupom_amigo = _cupom_amigo(total_usos=5)
    service = CupomService(repo)

    cupom = await service.obter_ou_criar_cupom_amigo_cliente(5)

    assert cupom["status_efetivo"] == "max_usage_reached"


@pytest.mark.asyncio
async def test_gerar_novo_cupom_bloqueia_quando_atual_ainda_ativo():
    repo = FakeMeuCupomRepo()
    repo.cupom_amigo = _cupom_amigo()
    service = CupomService(repo)

    with pytest.raises(HTTPException) as exc:
        await service.gerar_novo_cupom_amigo_cliente(5)

    assert exc.value.status_code == 400
    assert repo.created is None


@pytest.mark.asyncio
async def test_gerar_novo_cupom_quando_atual_expirou():
    repo = FakeMeuCupomRepo()
    repo.cupom_amigo = _cupom_amigo(data_fim=(now_utc() - timedelta(days=1)).isoformat())
    service = CupomService(repo)

    novo = await service.gerar_novo_cupom_amigo_cliente(5)

    assert repo.created is not None
    assert novo["status_efetivo"] == "active"
    assert novo["codigo"] != "AMIGO5AB12"
