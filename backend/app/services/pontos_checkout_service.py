from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, Optional

from app.repositories.pontos_repo import PontosRepository
from app.services.programa_pontos_service import ProgramaPontosService
from app.services.real_points_service import RealPointsService
from app.utils.datetime_utils import now_utc


def _date_to_db_datetime(d: date) -> datetime:
    return datetime(d.year, d.month, d.day, tzinfo=timezone.utc)


async def buscar_regra_ativa(db, suite_tipo: str, checkout_date: date):
    suite_tipo_norm = (suite_tipo or "").upper().strip()
    data_ref = _date_to_db_datetime(checkout_date)

    return await db.pontosregra.find_first(
        where={
            "suiteTipo": suite_tipo_norm,
            "ativo": True,
            "dataInicio": {"lte": data_ref},
            "dataFim": {"gte": data_ref},
        },
        order={"dataInicio": "desc"},
    )


async def creditar_rp_no_checkout(
    db,
    reserva_id: int,
    funcionario_id: Optional[int] = None,
    checkout_datetime: Optional[datetime] = None,
) -> Dict[str, Any]:
    reserva = await db.reserva.find_unique(where={"id": reserva_id})
    if not reserva:
        return {"success": False, "error": "Reserva nao encontrada"}

    cliente_id = getattr(reserva, "clienteId", None)
    if not cliente_id:
        return {"success": False, "error": "Reserva sem clienteId"}

    status_reserva = (getattr(reserva, "statusReserva", None) or "").upper().strip()
    if status_reserva in {"CANCELADA", "CANCELADO", "NO_SHOW", "NO-SHOW"}:
        return {
            "success": True,
            "creditado": False,
            "pontos": 0,
            "motivo": "Reserva cancelada ou no-show nao gera pontos",
            "status": "bloqueado",
        }

    tipo_suite = (getattr(reserva, "tipoSuite", None) or "").upper().strip()
    num_diarias = int(getattr(reserva, "numDiarias", 0) or 0)
    if num_diarias <= 0:
        return {
            "success": True,
            "creditado": False,
            "pontos": 0,
            "motivo": "Reserva sem diarias validas",
        }

    checkout_dt = checkout_datetime or getattr(reserva, "checkoutReal", None) or now_utc()
    regra = await buscar_regra_ativa(db, tipo_suite, checkout_dt.date())

    pontos, detalhe = RealPointsService.calcular_rp_oficial(tipo_suite, num_diarias, 0)
    motivo_calculo = f"Tabela oficial Jornada Real: {detalhe}"

    # A migration 013 formaliza as regras do banco com diarias_base = 1.
    # Se o banco ja estiver atualizado, usamos a regra configurada; se ainda
    # estiver com regra antiga de blocos, mantemos a tabela oficial como fonte.
    if regra:
        diarias_base = int(getattr(regra, "diariasBase", 1) or 1)
        rp_por_base = int(getattr(regra, "rpPorBase", 0) or 0)
        if diarias_base == 1 and rp_por_base > 0:
            pontos = num_diarias * rp_por_base
            motivo_calculo = (
                f"Regra ativa pontos_regras: {num_diarias} diaria(s) "
                f"x {rp_por_base} RP = {pontos} RP"
            )

    if pontos <= 0:
        return {"success": True, "creditado": False, "pontos": 0, "motivo": "Sem pontos a creditar"}

    programa_service = ProgramaPontosService(db)
    nivel = await programa_service.obter_nivel_efetivo_cliente(cliente_id)
    calculo_nivel = programa_service.aplicar_bonus_nivel(pontos, nivel)
    pontos_base = calculo_nivel["pontos_base"]
    pontos_bonus_nivel = calculo_nivel["pontos_bonus_nivel"]
    pontos = calculo_nivel["pontos_total"]

    transacao_existente = await db.transacaopontos.find_first(
        where={
            "reservaId": reserva_id,
            "tipo": "CREDITO",
            "origem": {"in": ["CHECKOUT", "RESERVA"]},
        }
    )
    if transacao_existente:
        liberar_em_existente = getattr(transacao_existente, "liberarEm", None)
        return {
            "success": True,
            "creditado": False,
            "pontos": 0,
            "motivo": "Pontos ja registrados para esta reserva",
            "transacao": {
                "transacao_id": transacao_existente.id,
                "saldo_anterior": getattr(transacao_existente, "saldoAnterior", None),
                "saldo_posterior": getattr(transacao_existente, "saldoPosterior", None),
                "pontos": getattr(transacao_existente, "pontos", None),
                "status": getattr(transacao_existente, "status", "liberado"),
                "liberar_em": liberar_em_existente.isoformat() if liberar_em_existente else None,
            },
        }

    codigo = getattr(reserva, "codigoReserva", None) or str(reserva_id)
    temporada = getattr(regra, "temporada", None) if regra else None
    motivo = f"Checkout reserva {codigo} - Suite {tipo_suite} - {num_diarias} diarias - {pontos} RP"
    if temporada:
        motivo = f"{motivo} - Temporada {temporada}"
    if pontos_bonus_nivel > 0:
        bonus_percentual = nivel.get("bonus_percentual") or 0
        motivo = f"{motivo} - Bonus nivel {nivel.get('nome')} +{bonus_percentual}% ({pontos_base}+{pontos_bonus_nivel})"
    motivo = f"{motivo} ({motivo_calculo})"

    liberar_em = checkout_dt + timedelta(hours=48)
    bonus_percentual = float(nivel.get("bonus_percentual") or 0)
    metadata = {
        "programa": "JORNADA_REAL",
        "origem": "CHECKOUT",
        "pontos_base": pontos_base,
        "bonus_percentual": bonus_percentual,
        "pontos_bonus_nivel": pontos_bonus_nivel,
        "pontos_total": pontos,
        "nivel": {
            "codigo": nivel.get("codigo"),
            "nome": nivel.get("nome"),
            "pontos_minimos": nivel.get("pontos_minimos"),
        },
        "calculo": {
            "suite_tipo": tipo_suite,
            "num_diarias": num_diarias,
            "fonte": motivo_calculo,
        },
    }
    pontos_repo = PontosRepository(db)
    result = await pontos_repo.criar_transacao_pontos(
        cliente_id=cliente_id,
        pontos=pontos,
        tipo="CREDITO",
        origem="CHECKOUT",
        motivo=motivo,
        reserva_id=reserva_id,
        funcionario_id=funcionario_id,
        status="pendente",
        liberar_em=liberar_em,
        metadata=metadata,
    )

    if result.get("idempotente"):
        return {
            "success": True,
            "creditado": False,
            "pontos": 0,
            "motivo": "Pontos ja registrados para esta reserva",
            "transacao": result,
        }

    return {
        "success": bool(result.get("success")),
        "creditado": bool(result.get("success")),
        "pontos": pontos if result.get("success") else 0,
        "pontos_base": pontos_base,
        "pontos_bonus_nivel": pontos_bonus_nivel,
        "nivel": nivel,
        "status": "pendente",
        "liberar_em": liberar_em.isoformat(),
        "transacao": result,
        "metadata": metadata,
    }


async def liberar_pontos_pendentes(
    db,
    limit: int = 100,
    agora: Optional[datetime] = None,
) -> Dict[str, Any]:
    return await PontosRepository(db).liberar_pontos_pendentes(limit=limit, agora=agora)


async def creditar_bonus_cupom_no_checkout(
    db,
    reserva_id: int,
    funcionario_id: Optional[int] = None,
) -> Dict[str, Any]:
    reserva = await db.reserva.find_unique(where={"id": reserva_id})
    if not reserva:
        return {"success": False, "error": "Reserva nao encontrada"}

    cliente_id = getattr(reserva, "clienteId", None)
    if not cliente_id:
        return {"success": False, "error": "Reserva sem clienteId"}

    cupom_uso = await db.cupomuso.find_first(
        where={"reservaId": reserva_id},
        include={"cupom": True},
    )
    if not cupom_uso or not getattr(cupom_uso, "cupom", None):
        return {"success": True, "creditado": False, "pontos": 0, "motivo": "Reserva sem cupom"}

    pontos_bonus = int(getattr(cupom_uso.cupom, "pontosBonus", 0) or 0)
    if pontos_bonus <= 0:
        return {"success": True, "creditado": False, "pontos": 0, "motivo": "Cupom sem bonus de pontos"}

    transacao_existente = await db.transacaopontos.find_first(
        where={
            "reservaId": reserva_id,
            "tipo": "CREDITO",
            "origem": "BONUS_CUPOM",
        }
    )
    if transacao_existente:
        return {"success": True, "creditado": False, "pontos": 0, "motivo": "Bonus do cupom ja creditado"}

    pontos_repo = PontosRepository(db)
    codigo = getattr(reserva, "codigoReserva", None) or str(reserva_id)
    motivo = f"Bonus do cupom {cupom_uso.cupom.codigo} no checkout da reserva {codigo}"

    result = await pontos_repo.criar_transacao_pontos(
        cliente_id=cliente_id,
        pontos=pontos_bonus,
        tipo="CREDITO",
        origem="BONUS_CUPOM",
        motivo=motivo,
        reserva_id=reserva_id,
        funcionario_id=funcionario_id,
    )

    if result.get("idempotente"):
        return {
            "success": True,
            "creditado": False,
            "pontos": 0,
            "motivo": "Bonus do cupom ja creditado",
            "transacao": result,
        }

    return {
        "success": bool(result.get("success")),
        "creditado": bool(result.get("success")),
        "pontos": pontos_bonus if result.get("success") else 0,
        "transacao": result,
    }
