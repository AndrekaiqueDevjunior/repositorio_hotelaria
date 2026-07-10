from types import SimpleNamespace
import os

import pytest

os.environ.setdefault("CIELO_MERCHANT_ID", "test-merchant")
os.environ.setdefault("CIELO_MERCHANT_KEY", "test-key")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")

from app.api.v1.referral_routes import aplicar_referral_na_reserva, gerar_referral
from app.schemas.cupom_schema import ReferralApplyRequest, ReferralGenerateRequest


class FakeCupomService:
    def __init__(self):
        self.criar_args = None
        self.aplicar_args = None

    async def criar_cupom_amigo(self, **kwargs):
        self.criar_args = kwargs
        return {
            "codigo": "AMIGO10ABCD",
            "status": "active",
            "valor_desconto": 10.0,
            "pontos_bonus": 0,
            "total_usos": 0,
            "limite_total_usos": 5,
            "data_fim": "2026-07-04T12:00:00+00:00",
            "link_rastreado": "https://hotel-real.com/reservar?cupom=AMIGO10ABCD",
            "whatsapp_message": "Convite Real",
            "whatsapp_share_url": "https://wa.me/?text=Convite%20Real",
            "whatsapp_send_result": {"success": True, "message_sid": "SM123"},
            "cliente_indicador": {"id": 10, "nome": "Joao"},
        }

    async def aplicar_em_reserva(self, reserva_id, codigo):
        self.aplicar_args = {"reserva_id": reserva_id, "codigo": codigo}
        return {
            "codigo": codigo,
            "valor_original": 500.0,
            "valor_desconto": 50.0,
            "valor_final": 450.0,
            "pontos_bonus": 0,
            "status": "active",
            "indicacao": {"success": True},
        }


@pytest.mark.asyncio
async def test_generate_referral_usa_core_cupom_e_twilio():
    service = FakeCupomService()
    payload = ReferralGenerateRequest(
        customer_id=10,
        discount_percentage=10,
        bonus_points=0,
        valid_days=30,
        max_uses=5,
        recipient_phone="+5522999999999",
        send_whatsapp=True,
    )

    result = await gerar_referral(
        payload=payload,
        service=service,
        current_user=SimpleNamespace(id=7),
    )

    assert result["success"] is True
    assert result["code"] == "AMIGO10ABCD"
    assert result["discount_percentage"] == 10.0
    assert result["bonus_points"] == 0
    assert result["twilio"]["message_sid"] == "SM123"
    assert service.criar_args == {
        "cliente_id": 10,
        "percentual_desconto": 10,
        "pontos_bonus": 0,
        "dias_validade": 30,
        "limite_total_usos": 5,
        "telefone_destino": "+5522999999999",
        "enviar_whatsapp": True,
        "criado_por": 7,
    }


@pytest.mark.asyncio
async def test_apply_referral_to_reservation_mapeia_desconto():
    service = FakeCupomService()
    payload = ReferralApplyRequest(reservation_id=99, code="amigo10abcd")

    result = await aplicar_referral_na_reserva(payload=payload, service=service)

    assert result["success"] is True
    assert result["reservation_id"] == 99
    assert result["code"] == "AMIGO10ABCD"
    assert result["discount"]["amount"] == 50.0
    assert result["bonus_points_future"] == 0
    assert service.aplicar_args == {"reserva_id": 99, "codigo": "AMIGO10ABCD"}
