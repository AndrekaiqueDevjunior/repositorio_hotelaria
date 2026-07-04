from datetime import date, datetime, timezone
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

    pontos_base, detalhe = RealPointsService.calcular_rp_oficial(tipo_suite, num_diarias, 0)
    motivo_calculo = f"Tabela oficial Jornada Real: {detalhe}"

    # A migration 013 formaliza as regras do banco com diarias_base = 1.
    # Se o banco ja estiver atualizado, usamos a regra configurada; se ainda
    # estiver com regra antiga de blocos, mantemos a tabela oficial como fonte.
    if regra:
        diarias_base = int(getattr(regra, "diariasBase", 1) or 1)
        rp_por_base = int(getattr(regra, "rpPorBase", 0) or 0)
        if diarias_base == 1 and rp_por_base > 0:
            pontos_base = num_diarias * rp_por_base
            motivo_calculo = (
                f"Regra ativa pontos_regras: {num_diarias} diaria(s) "
                f"x {rp_por_base} RP = {pontos_base} RP"
            )

    if pontos_base <= 0:
        return {"success": True, "creditado": False, "pontos": 0, "motivo": "Sem pontos a creditar"}

    programa_service = ProgramaPontosService(db)
    nivel = await programa_service.obter_nivel_efetivo_cliente(cliente_id)
    pontos_n_antes = await programa_service.obter_total_pontos_nivel(cliente_id)

    # Pontos N = sempre a pontuacao-base da suite, sem multiplicador. Pontos R
    # recebem o multiplicador do nivel atual do cliente (1x/2x/4x).
    calculo_nivel = programa_service.aplicar_bonus_nivel(pontos_base, nivel)
    pontos_n = calculo_nivel["pontos_n"]
    multiplicador_r = calculo_nivel["multiplicador_r"]
    pontos_r = calculo_nivel["pontos_r"]

    pontos_n_depois = pontos_n_antes + pontos_n
    nivel_depois = await programa_service.nivel_por_total_pontos_nivel(pontos_n_depois)
    progrediu_nivel = int(nivel_depois.get("codigo") or 0) > int(nivel.get("codigo") or 0)

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
    motivo = f"Checkout reserva {codigo} - Suite {tipo_suite} - {num_diarias} diarias - {pontos_n}N + {pontos_r}R"
    if temporada:
        motivo = f"{motivo} - Temporada {temporada}"
    if multiplicador_r > 1:
        motivo = f"{motivo} - Multiplicador nivel {nivel.get('nome')} {multiplicador_r:g}x sobre Pontos R"
    motivo = f"{motivo} ({motivo_calculo})"

    metadata = {
        "programa": "JORNADA_REAL",
        "origem": "CHECKOUT",
        "pontos_base": pontos_base,
        "pontos_n": pontos_n,
        "multiplicador_r": multiplicador_r,
        "pontos_r": pontos_r,
        "pontos_n_antes": pontos_n_antes,
        "pontos_n_depois": pontos_n_depois,
        "nivel_antes": {
            "codigo": nivel.get("codigo"),
            "nome": nivel.get("nome"),
            "pontos_minimos": nivel.get("pontos_minimos"),
        },
        "nivel_depois": {
            "codigo": nivel_depois.get("codigo"),
            "nome": nivel_depois.get("nome"),
            "pontos_minimos": nivel_depois.get("pontos_minimos"),
        },
        "progrediu_nivel": progrediu_nivel,
        "calculo": {
            "suite_tipo": tipo_suite,
            "num_diarias": num_diarias,
            "fonte": motivo_calculo,
        },
    }
    pontos_repo = PontosRepository(db)

    # Caminho normal: credita na hora (status "liberado"). 48h so entra em
    # cena como teto de seguranca se o credito imediato falhar por algum
    # motivo excepcional (falha de integracao, inconsistencia de dados) --
    # nesse caso cai como "pendente" com liberar_em=agora, para o job
    # liberar_pontos_pendentes (a cada 15min) reprocessar o quanto antes.
    status_final = "liberado"
    liberar_em_final: Optional[datetime] = None
    try:
        result = await pontos_repo.criar_transacao_pontos(
            cliente_id=cliente_id,
            pontos=pontos_r,
            pontos_nivel=pontos_n,
            tipo="CREDITO",
            origem="CHECKOUT",
            motivo=motivo,
            reserva_id=reserva_id,
            funcionario_id=funcionario_id,
            status="liberado",
            metadata=metadata,
        )
    except Exception as exc_imediato:
        print(f"[PONTOS CHECKOUT] Falha ao creditar pontos imediatamente da reserva {reserva_id}: {exc_imediato}")
        try:
            status_final = "pendente"
            liberar_em_final = now_utc()
            metadata_fallback = dict(metadata)
            metadata_fallback["erro_credito_imediato"] = str(exc_imediato)
            result = await pontos_repo.criar_transacao_pontos(
                cliente_id=cliente_id,
                pontos=pontos_r,
                pontos_nivel=pontos_n,
                tipo="CREDITO",
                origem="CHECKOUT",
                motivo=motivo,
                reserva_id=reserva_id,
                funcionario_id=funcionario_id,
                status="pendente",
                liberar_em=liberar_em_final,
                metadata=metadata_fallback,
            )
        except Exception as exc_fallback:
            print(f"[PONTOS CHECKOUT] Falha tambem ao registrar pontos pendentes da reserva {reserva_id}: {exc_fallback}")
            return {"success": False, "error": f"Falha ao processar pontos da reserva: {exc_fallback}"}

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
        "pontos": pontos_r if result.get("success") else 0,
        "pontos_n": pontos_n if result.get("success") else 0,
        "pontos_r": pontos_r if result.get("success") else 0,
        "pontos_base": pontos_base,
        "multiplicador_r": multiplicador_r,
        "nivel": nivel,
        "nivel_depois": nivel_depois,
        "progrediu_nivel": progrediu_nivel,
        "status": status_final,
        "liberar_em": liberar_em_final.isoformat() if liberar_em_final else None,
        "transacao": result,
        "metadata": metadata,
    }


async def estornar_pontos_cancelamento(db, reserva_id: int) -> Dict[str, Any]:
    """Estorna pontos ja liberados de uma reserva cancelada.

    Com o credito de pontos agora acontecendo na hora do checkout (em vez de
    so depois de 48h), fica mais provavel que uma reserva seja cancelada
    depois que os pontos dela ja viraram saldo disponivel -- entao o
    cancelamento precisa desfazer esse credito explicitamente. Nunca levanta
    excecao: se o debito falhar (ex: cliente ja resgatou os pontos e o saldo
    ficaria negativo), o cancelamento da reserva nao deve travar por isso.
    """
    transacoes = await db.transacaopontos.find_many(
        where={
            "reservaId": reserva_id,
            "tipo": {"in": ["CREDITO", "AJUSTE"]},
            "status": "liberado",
            "pontos": {"gt": 0},
        }
    )
    if not transacoes:
        return {"success": True, "estornado": False, "motivo": "Sem pontos liberados para estornar"}

    pontos_repo = PontosRepository(db)
    estornados = []
    pendentes = []
    for transacao in transacoes:
        origem_estorno = f"ESTORNO_{transacao.origem}"
        ja_estornado = await db.transacaopontos.find_first(
            where={
                "reservaId": reserva_id,
                "tipo": "ESTORNO",
                "origem": origem_estorno,
                "motivo": {"contains": f"#{transacao.id}"},
            }
        )
        if ja_estornado:
            continue
        motivo_estorno = f"Estorno da transacao #{transacao.id} - reserva {reserva_id} cancelada"
        try:
            result = await pontos_repo.criar_transacao_pontos(
                cliente_id=transacao.clienteId,
                pontos=-int(transacao.pontos),
                tipo="ESTORNO",
                origem=origem_estorno,
                motivo=motivo_estorno,
                reserva_id=reserva_id,
                status="estornado",
            )
            estornados.append({"transacao_original_id": transacao.id, **result})
        except Exception as exc:
            print(f"[PONTOS ESTORNO] Falha ao estornar transacao {transacao.id} da reserva {reserva_id}: {exc}")
            # Saldo insuficiente (cliente ja resgatou os pontos) ou outra falha
            # pontual: registra um estorno "pendente" (nao mexe no saldo agora)
            # para o job retentar_estornos_pendentes reprocessar quando o
            # cliente acumular saldo suficiente de novo.
            try:
                result_pendente = await pontos_repo.criar_transacao_pontos(
                    cliente_id=transacao.clienteId,
                    pontos=-int(transacao.pontos),
                    tipo="ESTORNO",
                    origem=origem_estorno,
                    motivo=motivo_estorno,
                    reserva_id=reserva_id,
                    status="pendente",
                )
                pendentes.append({"transacao_original_id": transacao.id, "erro": str(exc), **result_pendente})
            except Exception as exc_fallback:
                print(f"[PONTOS ESTORNO] Falha tambem ao registrar estorno pendente da transacao {transacao.id}: {exc_fallback}")
                pendentes.append({"transacao_original_id": transacao.id, "erro": str(exc_fallback)})

    return {
        "success": True,
        "estornado": bool(estornados),
        "transacoes_estornadas": estornados,
        "transacoes_pendentes": pendentes,
    }


async def liberar_pontos_pendentes(
    db,
    limit: int = 100,
    agora: Optional[datetime] = None,
) -> Dict[str, Any]:
    return await PontosRepository(db).liberar_pontos_pendentes(limit=limit, agora=agora)


async def retentar_estornos_pendentes(
    db,
    limit: int = 100,
    agora: Optional[datetime] = None,
) -> Dict[str, Any]:
    return await PontosRepository(db).retentar_estornos_pendentes(limit=limit, agora=agora)


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


# ---------------------------------------------------------------------------
# Promo de lancamento: primeiros N clientes (CPFs distintos) que fizerem
# check-out dentro da validade ganham X pontos, uma unica vez por cliente.
# Configuravel em ConfiguracaoJornada (chave PROMO_PRIMEIROS_CLIENTES).
# ---------------------------------------------------------------------------
PROMO_PRIMEIROS_CHAVE = "PROMO_PRIMEIROS_CLIENTES"
PROMO_PRIMEIROS_ORIGEM = "BONUS_PROMO_PRIMEIROS"


def _parse_data_limite(valor: Any) -> Optional[datetime]:
    if not valor:
        return None
    if isinstance(valor, datetime):
        dt = valor
    else:
        try:
            dt = datetime.fromisoformat(str(valor).replace("Z", "+00:00"))
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


async def obter_config_promo_primeiros(db) -> Optional[Dict[str, Any]]:
    """Le a configuracao da promo 'primeiros N clientes' em ConfiguracaoJornada.

    valor_json esperado:
        {"pontos": 100, "vagas": 10, "data_limite": "2026-07-31T23:59:59Z"}
    Retorna None se nao existir ou estiver inativa.
    """
    try:
        config = await db.configuracaojornada.find_unique(
            where={"chave": PROMO_PRIMEIROS_CHAVE}
        )
    except Exception:
        return None
    if not config or not getattr(config, "ativo", False):
        return None
    valor = getattr(config, "valorJson", None) or {}
    if not isinstance(valor, dict):
        return None
    return {
        "pontos": int(valor.get("pontos", 0) or 0),
        "vagas": int(valor.get("vagas", 0) or 0),
        "data_limite": _parse_data_limite(valor.get("data_limite")),
    }


async def creditar_bonus_promo_primeiros_no_checkout(
    db,
    reserva_id: int,
    funcionario_id: Optional[int] = None,
) -> Dict[str, Any]:
    config = await obter_config_promo_primeiros(db)
    if not config:
        return {"success": True, "creditado": False, "pontos": 0, "motivo": "Promo inativa ou nao configurada"}

    pontos_promo = config["pontos"]
    vagas = config["vagas"]
    data_limite = config["data_limite"]
    if pontos_promo <= 0 or vagas <= 0:
        return {"success": True, "creditado": False, "pontos": 0, "motivo": "Promo sem pontos/vagas configurados"}

    if data_limite and now_utc() > data_limite:
        return {"success": True, "creditado": False, "pontos": 0, "motivo": "Promo encerrada (data limite)"}

    reserva = await db.reserva.find_unique(where={"id": reserva_id})
    if not reserva:
        return {"success": False, "error": "Reserva nao encontrada"}

    cliente_id = getattr(reserva, "clienteId", None)
    if not cliente_id:
        return {"success": False, "error": "Reserva sem clienteId"}

    status_reserva = (getattr(reserva, "statusReserva", None) or "").upper().strip()
    if status_reserva in {"CANCELADA", "CANCELADO", "NO_SHOW", "NO-SHOW"}:
        return {"success": True, "creditado": False, "pontos": 0, "motivo": "Reserva cancelada nao gera promo"}

    codigo = getattr(reserva, "codigoReserva", None) or str(reserva_id)
    pontos_repo = PontosRepository(db)

    # Vagas sao um recurso compartilhado e limitado (ex.: 10 primeiros
    # clientes) -- contar "CPFs distintos ja contemplados" e decidir se ha
    # vaga livre precisa ser atomico com o credito, senao dois checkouts
    # concorrentes na ultima vaga passam ambos no check-then-act. Um
    # pg_advisory_xact_lock serializa todos os creditos desta promo mesmo
    # com pool de conexoes (o lock e preso a transacao, nao a sessao, e e
    # liberado automaticamente no commit/rollback).
    async with db.tx() as transaction:
        await transaction.execute_raw(
            "SELECT pg_advisory_xact_lock(hashtext($1))", PROMO_PRIMEIROS_CHAVE
        )

        # Idempotencia por CPF: 1 bonus por cliente, independente de quantas reservas
        ja_contemplado = await transaction.transacaopontos.find_first(
            where={
                "clienteId": cliente_id,
                "tipo": "CREDITO",
                "origem": PROMO_PRIMEIROS_ORIGEM,
            }
        )
        if ja_contemplado:
            return {"success": True, "creditado": False, "pontos": 0, "motivo": "Cliente ja contemplado na promo"}

        # Vagas: conta CPFs distintos ja contemplados
        contemplados = await transaction.transacaopontos.find_many(
            where={"tipo": "CREDITO", "origem": PROMO_PRIMEIROS_ORIGEM},
            distinct=["clienteId"],
        )
        vagas_usadas = len(contemplados)
        if vagas_usadas >= vagas:
            return {"success": True, "creditado": False, "pontos": 0, "motivo": "Vagas da promo esgotadas"}

        posicao = vagas_usadas + 1
        motivo = f"Promo primeiros {vagas} clientes - posicao {posicao}/{vagas} - reserva {codigo}"
        metadata = {
            "programa": "JORNADA_REAL",
            "origem": PROMO_PRIMEIROS_ORIGEM,
            "promo": PROMO_PRIMEIROS_CHAVE,
            "posicao": posicao,
            "vagas": vagas,
            "pontos": pontos_promo,
            "data_limite": data_limite.isoformat() if data_limite else None,
        }

        result = await pontos_repo.criar_transacao_pontos(
            cliente_id=cliente_id,
            pontos=pontos_promo,
            tipo="CREDITO",
            origem=PROMO_PRIMEIROS_ORIGEM,
            motivo=motivo,
            reserva_id=reserva_id,
            funcionario_id=funcionario_id,
            metadata=metadata,
            _tx=transaction,
        )

    if result.get("idempotente"):
        return {"success": True, "creditado": False, "pontos": 0, "motivo": "Bonus da promo ja creditado", "transacao": result}

    return {
        "success": bool(result.get("success")),
        "creditado": bool(result.get("success")),
        "pontos": pontos_promo if result.get("success") else 0,
        "posicao": posicao,
        "vagas": vagas,
        "transacao": result,
        "metadata": metadata,
    }


async def contar_vagas_promo_usadas(db) -> int:
    """Conta CPFs distintos ja contemplados pela promo de primeiros clientes."""
    contemplados = await db.transacaopontos.find_many(
        where={"tipo": "CREDITO", "origem": PROMO_PRIMEIROS_ORIGEM},
        distinct=["clienteId"],
    )
    return len(contemplados)


async def obter_status_promo_primeiros(db) -> Dict[str, Any]:
    """Status completo da promo para o admin (inclui config inativa)."""
    try:
        config = await db.configuracaojornada.find_unique(
            where={"chave": PROMO_PRIMEIROS_CHAVE}
        )
    except Exception:
        config = None

    valor: Dict[str, Any] = {}
    ativo = False
    if config:
        ativo = bool(getattr(config, "ativo", False))
        raw = getattr(config, "valorJson", None)
        if isinstance(raw, dict):
            valor = raw

    pontos = int(valor.get("pontos", 0) or 0)
    vagas = int(valor.get("vagas", 0) or 0)
    data_limite = _parse_data_limite(valor.get("data_limite"))
    vagas_usadas = await contar_vagas_promo_usadas(db)
    return {
        "configurada": config is not None,
        "ativo": ativo,
        "pontos": pontos,
        "vagas": vagas,
        "data_limite": data_limite.isoformat() if data_limite else None,
        "vagas_usadas": vagas_usadas,
        "vagas_restantes": max(vagas - vagas_usadas, 0),
        "esgotada": vagas > 0 and vagas_usadas >= vagas,
        "encerrada_por_data": bool(data_limite and now_utc() > data_limite),
    }


async def salvar_config_promo_primeiros(
    db,
    *,
    ativo: bool,
    pontos: int,
    vagas: int,
    data_limite: Optional[str],
) -> Dict[str, Any]:
    """Cria/atualiza a configuracao da promo de primeiros clientes."""
    from prisma import Json as PrismaJson

    valor = {
        "pontos": int(pontos or 0),
        "vagas": int(vagas or 0),
        "data_limite": data_limite or None,
    }
    await db.configuracaojornada.upsert(
        where={"chave": PROMO_PRIMEIROS_CHAVE},
        data={
            "create": {
                "chave": PROMO_PRIMEIROS_CHAVE,
                "valorJson": PrismaJson(valor),
                "ativo": bool(ativo),
            },
            "update": {
                "valorJson": PrismaJson(valor),
                "ativo": bool(ativo),
            },
        },
    )
    return await obter_status_promo_primeiros(db)
