from datetime import date, datetime, timezone
from typing import Any, Dict, Optional

from app.repositories.pontos_repo import PontosRepository
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
        return {"success": False, "error": "Reserva não encontrada"}

    cliente_id = getattr(reserva, "clienteId", None)
    if not cliente_id:
        return {"success": False, "error": "Reserva sem clienteId"}

    tipo_suite = (getattr(reserva, "tipoSuite", None) or "").upper().strip()
    num_diarias = int(getattr(reserva, "numDiarias", 0) or 0)

    if num_diarias <= 0:
        return {"success": True, "creditado": False, "pontos": 0, "motivo": "Reserva sem diárias válidas"}

    checkout_dt = checkout_datetime or getattr(reserva, "checkoutReal", None)
    if not checkout_dt:
        checkout_dt = now_utc()

    regra = await buscar_regra_ativa(db, tipo_suite, checkout_dt.date())
    if not regra:
        return {
            "success": True,
            "creditado": False,
            "pontos": 0,
            "motivo": "Nenhuma regra ativa encontrada para a data do checkout",
        }

    diarias_base = int(getattr(regra, "diariasBase", 2) or 2)
    rp_por_base = int(getattr(regra, "rpPorBase", 0) or 0)

    if diarias_base <= 0 or rp_por_base <= 0:
        return {"success": True, "creditado": False, "pontos": 0, "motivo": "Regra inválida"}

    blocos = num_diarias // diarias_base
    pontos = blocos * rp_por_base

    if pontos <= 0:
        return {"success": True, "creditado": False, "pontos": 0, "motivo": "Sem pontos a creditar"}

    transacao_existente = await db.transacaopontos.find_first(
        where={
            "reservaId": reserva_id,
            "tipo": "CREDITO",
        }
    )

    if transacao_existente:
        return {
            "success": True,
            "creditado": False,
            "pontos": 0,
            "motivo": "Pontos já creditados",
            "transacao": {
                "transacao_id": transacao_existente.id,
                "saldo_anterior": getattr(transacao_existente, "saldoAnterior", None),
                "saldo_posterior": getattr(transacao_existente, "saldoPosterior", None),
                "pontos": getattr(transacao_existente, "pontos", None),
            },
        }

    pontos_repo = PontosRepository(db)

    codigo = getattr(reserva, "codigoReserva", None) or str(reserva_id)
    temporada = getattr(regra, "temporada", None)
    motivo = f"Checkout reserva {codigo} - Suíte {tipo_suite} - {num_diarias} diárias - {pontos} RP"
    if temporada:
        motivo = f"{motivo} - Temporada {temporada}"

    result = await pontos_repo.criar_transacao_pontos(
        cliente_id=cliente_id,
        pontos=pontos,
        tipo="CREDITO",
        origem="CHECKOUT",
        motivo=motivo,
        reserva_id=reserva_id,
        funcionario_id=funcionario_id,
    )

    return {
        "success": bool(result.get("success")),
        "creditado": bool(result.get("success")),
        "pontos": pontos if result.get("success") else 0,
        "transacao": result,
    }
