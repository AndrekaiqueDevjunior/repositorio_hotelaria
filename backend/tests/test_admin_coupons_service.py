from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.repositories.cupom_repo import CupomRepository
from app.schemas.cupom_schema import AdminCouponGenerateRequest
from app.services.cupom_service import CupomService


class FakeAdminCupomRepo:
    def __init__(self):
        self.created = None
        self.updated = None
        self.deleted_id = None
        self.list_args = None
        self.coupons = {}

    async def get_by_codigo(self, codigo):
        return self.coupons.get(codigo.upper())

    async def create(self, data, criado_por=None):
        self.created = {"data": data, "criado_por": criado_por}
        cupom = {
            "id": 10,
            "codigo": data["codigo"],
            "descricao": data.get("descricao"),
            "tipo_desconto": data["tipo_desconto"],
            "valor_desconto": float(data["valor_desconto"]),
            "pontos_bonus": data.get("pontos_bonus") or 0,
            "min_diarias": data.get("min_diarias"),
            "suites_permitidas": data.get("suites_permitidas"),
            "data_inicio": data["data_inicio"],
            "data_fim": data["data_fim"],
            "limite_total_usos": data.get("limite_total_usos"),
            "limite_por_cliente": data.get("limite_por_cliente"),
            "total_usos": 0,
            "ativo": data.get("ativo", True),
            "status": data.get("status", "active"),
            "tracking_slug": data.get("tracking_slug"),
            "criado_por": criado_por,
            "tipo_campanha": data.get("tipo_campanha"),
            "influencer_nome": data.get("influencer_nome"),
            "commission_percentual": float(data["commission_percentual"])
            if data.get("commission_percentual") is not None
            else None,
            "cliente_indicador_id": None,
            "created_at": None,
            "updated_at": None,
            "stats": {
                "usage_count": 0,
                "unique_customers": 0,
                "gross_amount": 0.0,
                "discount_amount": 0.0,
                "net_amount": 0.0,
                "commission_base": 0.0,
                "estimated_commission": 0.0,
            },
        }
        self.coupons[cupom["codigo"]] = cupom
        return cupom

    async def get_admin_by_codigo(self, codigo, include_usages=True, usage_limit=25):
        return self.coupons.get(codigo.upper())

    async def list_admin(self, **kwargs):
        self.list_args = kwargs
        return list(self.coupons.values())

    async def update(self, cupom_id, data):
        self.updated = {"cupom_id": cupom_id, "data": data}
        cupom = next(item for item in self.coupons.values() if item["id"] == cupom_id)
        cupom.update({
            "descricao": data.get("descricao", cupom["descricao"]),
            "status": data.get("status", cupom["status"]),
            "ativo": data.get("ativo", cupom["ativo"]),
            "commission_percentual": data.get("commission_percentual", cupom["commission_percentual"]),
        })
        return cupom

    async def delete(self, cupom_id):
        self.deleted_id = cupom_id
        return True


@pytest.mark.asyncio
async def test_admin_generate_coupon_cria_influencer_com_link_e_comissao():
    repo = FakeAdminCupomRepo()
    service = CupomService(repo)
    valid_until = datetime.now(timezone.utc) + timedelta(days=30)
    payload = AdminCouponGenerateRequest(
        code="ingrid_influencer",
        discountType="PERCENTAGE",
        discountValue=20,
        validUntil=valid_until,
        maxUses=100,
        campaignType="INFLUENCER",
        influencerName="Ingrid",
        commissionPercentage=10,
    )

    result = await service.admin_generate_coupon(payload.model_dump(exclude_unset=True), criado_por=7)

    assert result["success"] is True
    assert result["code"] == "INGRID_INFLUENCER"
    assert result["discountType"] == "PERCENTAGE"
    assert result["status"] == "ACTIVE"
    assert result["campaignType"] == "INFLUENCER"
    assert result["influencerName"] == "Ingrid"
    assert result["commissionPercentage"] == 10.0
    assert result["trackingLink"].startswith(
        "http://localhost:3000/reservar?cupom=INGRID_INFLUENCER&origem=INFLUENCER&ref=ingrid-"
    )
    assert repo.created["criado_por"] == 7
    assert repo.created["data"]["tipo_desconto"] == "PERCENTUAL"
    assert repo.created["data"]["limite_total_usos"] == 100
    assert repo.created["data"]["commission_percentual"] == Decimal("10")


@pytest.mark.asyncio
async def test_admin_list_coupons_mapeia_filtros_para_repo():
    repo = FakeAdminCupomRepo()
    service = CupomService(repo)
    repo.coupons["INGRID"] = {
        "id": 11,
        "codigo": "INGRID",
        "descricao": "Influencer",
        "tipo_desconto": "PERCENTUAL",
        "valor_desconto": 20.0,
        "pontos_bonus": 0,
        "min_diarias": None,
        "suites_permitidas": None,
        "data_inicio": "2026-06-01T00:00:00+00:00",
        "data_fim": "2026-06-30T00:00:00+00:00",
        "limite_total_usos": 100,
        "limite_por_cliente": 1,
        "total_usos": 5,
        "ativo": True,
        "status": "active",
        "tracking_slug": "ingrid-abcd",
        "criado_por": 7,
        "tipo_campanha": "INFLUENCER",
        "influencer_nome": "Ingrid",
        "commission_percentual": 10.0,
        "stats": {
            "usage_count": 5,
            "unique_customers": 4,
            "gross_amount": 1000.0,
            "discount_amount": 200.0,
            "net_amount": 800.0,
            "commission_base": 800.0,
            "estimated_commission": 80.0,
        },
        "created_at": None,
        "updated_at": None,
    }

    result = await service.admin_list_coupons(
        status="ACTIVE",
        campaign_type="INFLUENCER",
        influencer_only=True,
        limit=25,
        offset=10,
    )

    assert repo.list_args == {
        "status": "active",
        "tipo_campanha": "INFLUENCER",
        "apenas_influencer": True,
        "limit": 25,
        "offset": 10,
    }
    assert result["total"] == 1
    assert result["coupons"][0]["stats"]["estimatedCommission"] == 80.0


def test_repo_admin_row_calcula_comissao_estimativa():
    repo = CupomRepository(db=None)
    row = {
        "id": 1,
        "codigo": "INGRID",
        "descricao": "Influencer",
        "tipo_desconto": "PERCENTUAL",
        "valor_desconto": Decimal("20"),
        "pontos_bonus": 0,
        "min_diarias": None,
        "suites_permitidas": None,
        "data_inicio": datetime(2026, 6, 1, tzinfo=timezone.utc),
        "data_fim": datetime(2026, 6, 30, tzinfo=timezone.utc),
        "limite_total_usos": 100,
        "limite_por_cliente": 1,
        "total_usos": 3,
        "ativo": True,
        "status": "active",
        "tracking_slug": "ingrid-abcd",
        "criado_por": 7,
        "tipo_campanha": "INFLUENCER",
        "influencer_nome": "Ingrid",
        "commission_percentual": Decimal("10"),
        "cliente_indicador_id": None,
        "created_at": None,
        "updated_at": None,
        "usos_registrados": 3,
        "clientes_unicos": 2,
        "valor_original_total": Decimal("1500"),
        "valor_desconto_total": Decimal("300"),
        "valor_final_total": Decimal("1200"),
    }

    result = repo._serialize_cupom_admin_row(row)

    assert result["stats"]["usage_count"] == 3
    assert result["stats"]["commission_base"] == 1200.0
    assert result["stats"]["estimated_commission"] == 120.0
