from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import User
from app.middleware.auth_middleware import get_current_active_user, require_admin_or_manager
from app.middleware.rate_limit import rate_limit_moderate, rate_limit_strict
from app.repositories.cliente_repo import ClienteRepository
from app.repositories.premio_repo_atomic import PremioRepositoryAtomic
from app.repositories.pontos_repo import PontosRepository
from app.services.disponibilidade_service import DisponibilidadeService
from app.services.jornada_service import JornadaService
from app.services.programa_pontos_service import ProgramaPontosService
from app.utils.datetime_utils import LOCAL_TIMEZONE, to_utc

router = APIRouter(tags=["jornada-real"])


class RewardRedeemRequest(BaseModel):
    reward_id: int
    customer_id: Optional[int] = None
    customer_document: Optional[str] = None
    cpf: Optional[str] = None


class PromoPrimeirosConfigRequest(BaseModel):
    ativo: bool = True
    pontos: int
    vagas: int
    data_limite: Optional[str] = None  # ISO 8601, ex: "2026-07-31T23:59:59Z"


def get_jornada_service() -> JornadaService:
    return JornadaService(get_db())


def _int_or_none(value) -> Optional[int]:
    try:
        if value is None:
            return None
        return int(value)
    except Exception:
        return None


def _status_from_redeem_error(message: str) -> int:
    normalized = (message or "").lower()

    if "saldo insuficiente" in normalized:
        return 402
    if "estoque" in normalized or "sem estoque" in normalized:
        return 409
    if "nao encontrado" in normalized or "não encontrado" in normalized:
        return 404

    return 400


def _parse_availability_datetime(value: str, *, default_hour: int) -> datetime:
    raw = (value or "").strip()
    if not raw:
        raise HTTPException(status_code=400, detail="Data obrigatória.")

    try:
        if len(raw) == 10:
            parsed = datetime.fromisoformat(raw)
            local_dt = parsed.replace(
                hour=default_hour,
                minute=0,
                second=0,
                microsecond=0,
                tzinfo=LOCAL_TIMEZONE,
            )
            return to_utc(local_dt)

        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return to_utc(parsed)
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de data inválido. Use YYYY-MM-DD ou ISO 8601.")


async def _get_customer_by_document(documento: str):
    documento_limpo = "".join(filter(str.isdigit, documento or ""))
    if not documento_limpo:
        return None

    repo = ClienteRepository(get_db())
    try:
        return await repo.get_by_documento(documento_limpo)
    except ValueError:
        return None


async def _get_customer_by_id(customer_id: int):
    repo = ClienteRepository(get_db())
    try:
        return await repo.get_by_id(customer_id)
    except ValueError:
        return None


async def _resolve_customer(customer_id: Optional[int], customer_document: Optional[str]):
    if customer_id is not None:
        customer = await _get_customer_by_id(customer_id)
        if customer:
            return customer

    return await _get_customer_by_document(customer_document or "")


@router.get("/availability", response_model=list)
async def listar_availability(
    checkin: str = Query(..., description="Data de check-in: YYYY-MM-DD ou ISO 8601"),
    checkout: str = Query(..., description="Data de check-out: YYYY-MM-DD ou ISO 8601"),
    suite_type: Optional[str] = Query(None, description="Filtro opcional por tipo de suíte"),
    _rate_limit: None = Depends(rate_limit_moderate),
):
    checkin_dt = _parse_availability_datetime(checkin, default_hour=12)
    checkout_dt = _parse_availability_datetime(checkout, default_hour=11)
    if checkout_dt <= checkin_dt:
        raise HTTPException(status_code=400, detail="Data de check-out deve ser posterior ao check-in.")

    tipo_suite = (suite_type or "").strip().upper() or None
    quartos = await DisponibilidadeService(get_db()).listar_quartos_disponiveis(
        checkin_dt,
        checkout_dt,
        tipo_suite,
    )

    return [
        {
            "room_id": quarto.get("numero"),
            "room": quarto.get("numero"),
            "numero": quarto.get("numero"),
            "suite_type": quarto.get("tipo_suite"),
            "tipo_suite": quarto.get("tipo_suite"),
            "status": quarto.get("status"),
            "available": True,
            "disponivel": True,
        }
        for quarto in quartos
    ]


@router.get("/customers/{customer_ref}/loyalty", response_model=dict)
async def obter_loyalty_customer(
    customer_ref: str,
    _rate_limit: None = Depends(rate_limit_moderate),
):
    """Alias publico da Jornada Real para consulta de pontos por CPF."""
    customer = await _get_customer_by_document(customer_ref)

    if not customer:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")

    db = get_db()
    customer_id = int(customer["id"])
    saldo_data = await PontosRepository(db).get_saldo(customer_id)
    programa_data = await ProgramaPontosService(db).obter_programa_cliente(customer_id)

    saldo_atual = int(saldo_data.get("saldo") or 0)
    barra_nivel = programa_data.get("barra_nivel") or {}
    barra_premios = programa_data.get("barra_premios") or {}
    nivel_atual = programa_data.get("nivel") or {}
    proximo_nivel = barra_nivel.get("proximo_nivel") or {}
    proximo_premio = programa_data.get("proximo_premio")
    lifetime_points = int(programa_data.get("total_pontos_nivel") or saldo_atual)
    total_resgatado = int(programa_data.get("total_resgatado") or 0)
    rewards_unlocked = int(programa_data.get("rewards_unlocked") or barra_premios.get("rewards_unlocked") or 0)
    rewards_total = int(programa_data.get("rewards_total") or barra_premios.get("rewards_total") or 0)

    return {
        "customer_id": customer_id,
        "customer_name": customer.get("nome_completo") or "Cliente",
        "document": customer.get("documento"),
        "lifetime_points": lifetime_points,
        "redeemable_points": saldo_atual,
        "total_redeemed_points": total_resgatado,
        "current_level": nivel_atual,
        "current_level_name": nivel_atual.get("nome"),
        "next_level": proximo_nivel or None,
        "next_level_points": _int_or_none(barra_nivel.get("meta")) or 90,
        "missing_to_next_level": _int_or_none(barra_nivel.get("faltam_pontos")) or 0,
        "level_progress": _int_or_none(barra_nivel.get("percentual")) or 0,
        "next_reward": proximo_premio,
        "rewards_unlocked": rewards_unlocked,
        "rewards_total": rewards_total,
        "reward_goal_points": _int_or_none(barra_premios.get("meta")) or 0,
        "missing_to_next_reward": _int_or_none(barra_premios.get("faltam_pontos")) or 0,
        "reward_progress": _int_or_none(barra_premios.get("percentual")) or 0,
        "barra_nivel": barra_nivel,
        "barra_premios": barra_premios,
        "programa_pontos": programa_data,
    }


@router.post("/rewards/redeem", response_model=dict)
async def redeem_reward(
    payload: RewardRedeemRequest,
    _rate_limit: None = Depends(rate_limit_strict),
):
    """Alias da Jornada Real para resgate de premio com resposta em ingles."""
    customer = await _resolve_customer(
        payload.customer_id,
        payload.customer_document or payload.cpf,
    )

    if not customer:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")

    result = await PremioRepositoryAtomic(get_db()).resgatar_atomic(
        premio_id=payload.reward_id,
        cliente_id=int(customer["id"]),
        funcionario_id=None,
    )

    if not result.get("success"):
        detail = result.get("error") or "Erro ao resgatar prêmio."
        raise HTTPException(status_code=_status_from_redeem_error(detail), detail=detail)

    code = result.get("codigo_resgate") or result.get("codigo")
    expires_at = result.get("expira_em") or result.get("valido_ate")

    return {
        "success": True,
        "id": result.get("resgate_id"),
        "reward_id": payload.reward_id,
        "customer_id": int(customer["id"]),
        "redemption_code": code,
        "expires_at": expires_at,
        "status": "active",
        "redemption_status": result.get("status"),
        "points_used": result.get("pontos_usados"),
        "remaining_redeemable_points": result.get("novo_saldo"),
        "message": result.get("mensagem") or "Prêmio resgatado com sucesso.",
    }


@router.get("/jornada/config", response_model=dict)
async def obter_config_jornada(
    service: JornadaService = Depends(get_jornada_service),
):
    return await service.get_config()


@router.get("/admin/promocoes/primeiros-clientes", response_model=dict)
async def obter_promo_primeiros_clientes(
    current_user: User = Depends(require_admin_or_manager),
):
    from app.services.pontos_checkout_service import obter_status_promo_primeiros

    return await obter_status_promo_primeiros(get_db())


@router.put("/admin/promocoes/primeiros-clientes", response_model=dict)
async def salvar_promo_primeiros_clientes(
    payload: PromoPrimeirosConfigRequest,
    current_user: User = Depends(require_admin_or_manager),
):
    from app.services.pontos_checkout_service import salvar_config_promo_primeiros

    if payload.pontos <= 0:
        raise HTTPException(status_code=400, detail="pontos deve ser maior que zero")
    if payload.vagas <= 0:
        raise HTTPException(status_code=400, detail="vagas deve ser maior que zero")

    return await salvar_config_promo_primeiros(
        get_db(),
        ativo=payload.ativo,
        pontos=payload.pontos,
        vagas=payload.vagas,
        data_limite=payload.data_limite,
    )


@router.get("/jornada/regras", response_model=dict)
async def obter_regras_jornada(
    service: JornadaService = Depends(get_jornada_service),
):
    return await service.get_regras()


@router.get("/jornada/consulta", response_model=dict)
async def consultar_jornada_por_cpf(
    request: Request,
    cpf: str = Query(..., min_length=11),
    service: JornadaService = Depends(get_jornada_service),
    _rate_limit: None = Depends(rate_limit_moderate),
):
    try:
        dashboard = await service.consultar_jornada_por_cpf(cpf)
        return dashboard
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar Jornada Real: {exc}")


@router.get("/clientes/{cliente_id}/jornada", response_model=dict)
async def obter_dashboard_jornada_cliente(
    cliente_id: int,
    service: JornadaService = Depends(get_jornada_service),
    current_user: User = Depends(get_current_active_user),
):
    return await service.montar_dashboard_jornada(cliente_id)


@router.get("/clientes/{cliente_id}/nivel", response_model=dict)
async def obter_nivel_jornada_cliente(
    cliente_id: int,
    service: JornadaService = Depends(get_jornada_service),
    current_user: User = Depends(get_current_active_user),
):
    return await service.obter_nivel_cliente(cliente_id)


@router.get("/clientes/{cliente_id}/beneficios", response_model=dict)
async def obter_beneficios_jornada_cliente(
    cliente_id: int,
    service: JornadaService = Depends(get_jornada_service),
    current_user: User = Depends(get_current_active_user),
):
    return await service.listar_beneficios(cliente_id)
