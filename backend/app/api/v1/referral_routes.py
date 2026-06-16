from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends

from app.core.database import get_db
from app.core.security import User
from app.middleware.auth_middleware import require_admin_or_manager
from app.middleware.rate_limit import rate_limit_moderate
from app.repositories.cupom_repo import CupomRepository
from app.schemas.cupom_schema import ReferralApplyRequest, ReferralGenerateRequest
from app.services.cupom_service import CupomService


router = APIRouter(prefix="/referrals", tags=["referrals"])


async def get_cupom_service() -> CupomService:
    return CupomService(CupomRepository(get_db()))


def _referral_response(
    cupom: Optional[Dict[str, Any]],
    validation: Optional[Dict[str, Any]] = None,
    generated_by: Optional[str] = None,
) -> Dict[str, Any]:
    if not cupom:
        return {
            "valid": False,
            "message": (validation or {}).get("mensagem") or "Cupom não encontrado",
            "code": None,
            "codigo": None,
        }

    valid = bool((validation or {}).get("valido", cupom.get("ativo") and cupom.get("status") == "active"))
    message = (validation or {}).get("mensagem") or ("Cupom válido" if valid else "Cupom inválido")
    cliente_indicador = cupom.get("cliente_indicador") or {}

    return {
        "valid": valid,
        "message": message,
        "code": cupom.get("codigo"),
        "codigo": cupom.get("codigo"),
        "status": cupom.get("status"),
        "generated_by": generated_by or cliente_indicador.get("nome"),
        "generated_by_customer_id": cupom.get("cliente_indicador_id") or cliente_indicador.get("id"),
        "discount_percentage": cupom.get("valor_desconto"),
        "bonus_points": cupom.get("pontos_bonus") or 0,
        "current_uses": cupom.get("total_usos") or 0,
        "max_uses": cupom.get("limite_total_usos"),
        "expires_at": cupom.get("data_fim"),
        "link": cupom.get("link_rastreado"),
        "whatsapp_message": cupom.get("whatsapp_message"),
        "whatsapp_share_url": cupom.get("whatsapp_share_url"),
    }


async def _nome_cliente_indicador(service: CupomService, cupom: Dict[str, Any]) -> Optional[str]:
    cliente_id = cupom.get("cliente_indicador_id")
    if not cliente_id:
        return None

    cliente = await service.cupom_repo.db.cliente.find_unique(where={"id": int(cliente_id)})
    if not cliente:
        return None
    return getattr(cliente, "nomeCompleto", None)


@router.post("/generate", response_model=dict, status_code=201)
async def gerar_referral(
    payload: ReferralGenerateRequest,
    service: CupomService = Depends(get_cupom_service),
    current_user: User = Depends(require_admin_or_manager),
):
    cupom = await service.criar_cupom_amigo(
        cliente_id=payload.customer_id,
        percentual_desconto=payload.discount_percentage,
        pontos_bonus=payload.bonus_points,
        dias_validade=payload.valid_days,
        limite_total_usos=payload.max_uses,
        telefone_destino=payload.recipient_phone,
        enviar_whatsapp=payload.send_whatsapp,
        criado_por=current_user.id,
    )
    response = _referral_response(cupom, {"valido": True, "mensagem": "Cupom gerado"})
    response["success"] = True
    response["twilio"] = cupom.get("whatsapp_send_result")
    return response


@router.get("/{code}", response_model=dict)
async def validar_referral(
    code: str,
    service: CupomService = Depends(get_cupom_service),
    _rate_limit: None = Depends(rate_limit_moderate),
):
    validation = await service.validar(codigo=code)
    cupom = await service.get_by_codigo(code)
    generated_by = await _nome_cliente_indicador(service, cupom) if cupom else None
    return _referral_response(cupom, validation, generated_by=generated_by)


@router.post("/apply-to-reservation", response_model=dict)
async def aplicar_referral_na_reserva(
    payload: ReferralApplyRequest,
    service: CupomService = Depends(get_cupom_service),
    _rate_limit: None = Depends(rate_limit_moderate),
):
    uso = await service.aplicar_em_reserva(payload.reservation_id, payload.code)
    return {
        "success": True,
        "reservation_id": payload.reservation_id,
        "reserva_id": payload.reservation_id,
        "code": uso.get("codigo"),
        "codigo": uso.get("codigo"),
        "discount": {
            "original": uso.get("valor_original"),
            "amount": uso.get("valor_desconto"),
            "final": uso.get("valor_final"),
        },
        "bonus_points_future": uso.get("pontos_bonus") or 0,
        "status": uso.get("status"),
        "usage": uso,
        "indicacao": uso.get("indicacao"),
    }
