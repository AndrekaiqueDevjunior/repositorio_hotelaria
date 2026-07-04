import json
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone
from prisma import Client
from fastapi import HTTPException
from app.utils.datetime_utils import to_utc
from app.schemas.pontos_schema import (
    AjustarPontosRequest, SaldoResponse, TransacaoResponse,
    HistoricoTransacao, HistoricoResponse
)

# Constantes de segurança
MAX_PONTOS_POR_TRANSACAO = 1000
MIN_PONTOS_POR_TRANSACAO = -1000
ORIGENS_IDEMPOTENTES_POR_RESERVA = {"CHECKOUT", "BONUS_CUPOM", "CONVITE_REAL", "RESERVA"}


class PontosRepository:
    def __init__(self, db: Client):
        self.db = db
    
    async def get_saldo(self, cliente_id: int) -> Dict[str, Any]:
        """Obter saldo de pontos do cliente"""
        # Primeiro verificar se o cliente existe
        cliente = await self.db.cliente.find_first(
            where={"id": cliente_id}
        )
        
        if not cliente:
            return {
                "success": False,
                "error": f"Cliente com ID {cliente_id} não encontrado",
                "saldo": 0
            }
        
        usuario_pontos = await self.db.usuariopontos.find_first(
            where={"clienteId": cliente_id}
        )
        
        if not usuario_pontos:
            # Criar registro se não existir (cliente já validado)
            usuario_pontos = await self.db.usuariopontos.create(
                data={
                    "clienteId": cliente_id,
                    "saldo": 0
                }
            )
        
        return {
            "success": True,
            "saldo": usuario_pontos.saldo,
            "usuario_pontos_id": usuario_pontos.id,
            "cliente_nome": cliente.nomeCompleto
        }
    
    async def ajustar_pontos(
        self, 
        request: AjustarPontosRequest,
        funcionario_id: int = None
    ) -> Dict[str, Any]:
        """Ajustar pontos (creditar/debitar) com rastreabilidade"""
        # VALIDAÇÃO DE SEGURANÇA: Limites de pontos
        if request.pontos == 0:
            raise ValueError("Transação de 0 pontos não permitida")
        
        if abs(request.pontos) > MAX_PONTOS_POR_TRANSACAO:
            raise ValueError(
                f"Transação limitada a ±{MAX_PONTOS_POR_TRANSACAO} pontos. "
                f"Valor solicitado: {request.pontos}"
            )
        
        resultado = await self.criar_transacao_pontos(
            cliente_id=request.cliente_id,
            pontos=request.pontos,
            tipo="AJUSTE" if request.pontos > 0 else "DEBITO",
            origem="AJUSTE_MANUAL",
            motivo=request.motivo,
            funcionario_id=funcionario_id,
        )

        return {
            "success": True,
            "transacao_id": resultado["transacao_id"],
            "novo_saldo": resultado["saldo_posterior"],
            "saldo_anterior": resultado["saldo_anterior"]
        }
    
    async def get_historico(self, cliente_id: int, limit: int = 20) -> Dict[str, Any]:
        """Obter histórico de transações com relacionamentos"""
        transacoes = await self.db.transacaopontos.find_many(
            where={"clienteId": cliente_id},
            order={"createdAt": "desc"},
            take=limit,
            include={
                "reserva": True,
                "funcionario": True
            }
        )
        
        return {
            "success": True,
            "transacoes": [self._serialize_transacao(t) for t in transacoes],
            "total": len(transacoes)
        }
    
    def _serialize_transacao(self, transacao) -> Dict[str, Any]:
        """Serializar transação para response com relacionamentos"""
        return {
            "id": transacao.id,
            "tipo": transacao.tipo,
            "pontos": transacao.pontos,
            "saldo_anterior": transacao.saldoAnterior if hasattr(transacao, 'saldoAnterior') and transacao.saldoAnterior is not None else 0,
            "saldo_posterior": transacao.saldoPosterior if hasattr(transacao, 'saldoPosterior') and transacao.saldoPosterior is not None else 0,
            "status": getattr(transacao, "status", "liberado"),
            "liberar_em": transacao.liberarEm.isoformat() if getattr(transacao, "liberarEm", None) else None,
            "origem": transacao.origem,
            "motivo": transacao.motivo if hasattr(transacao, 'motivo') else None,
            "metadata": (
                getattr(transacao, "metadata_json", None)
                if hasattr(transacao, "metadata_json")
                else getattr(transacao, "metadata", None)
            ),
            "created_at": transacao.createdAt.isoformat() if transacao.createdAt else None,
            "reserva_id": transacao.reservaId if hasattr(transacao, 'reservaId') else None,
            "reserva_codigo": transacao.reserva.codigoReserva if hasattr(transacao, 'reserva') and transacao.reserva else None,
            "funcionario_id": transacao.funcionarioId if hasattr(transacao, 'funcionarioId') else None,
            "funcionario_nome": transacao.funcionario.nome if hasattr(transacao, 'funcionario') and transacao.funcionario else None,
            "cliente_id": transacao.clienteId if hasattr(transacao, 'clienteId') else None,
            "cliente_nome": transacao.cliente.nomeCompleto if hasattr(transacao, 'cliente') and transacao.cliente else None
        }
    
    async def get_estatisticas(self) -> Dict[str, Any]:
        """Obter estatísticas gerais do sistema de pontos"""
        # Total de pontos em circulação
        todos_usuarios = await self.db.usuariopontos.find_many()
        total_pontos = sum(u.saldo for u in todos_usuarios)
        total_usuarios_com_pontos = len([u for u in todos_usuarios if u.saldo > 0])
        
        # Total de transações
        total_transacoes = await self.db.transacaopontos.count()
        
        # Transações recentes
        transacoes_recentes = await self.db.transacaopontos.find_many(
            order={"createdAt": "desc"},
            take=10,
            include={"cliente": True, "funcionario": True, "reserva": True}
        )

        inicio_hoje = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        transacoes_hoje = await self.db.transacaopontos.count(
            where={"createdAt": {"gte": inicio_hoje}}
        )

        return {
            "success": True,
            "total_pontos_circulacao": total_pontos,
            "total_usuarios": len(todos_usuarios),
            "usuarios_com_pontos": total_usuarios_com_pontos,
            "total_transacoes": total_transacoes,
            "transacoes_hoje": transacoes_hoje,
            "transacoes_recentes": [self._serialize_transacao(t) for t in transacoes_recentes]
        }
    
    async def criar_transacao_pontos(
        self,
        cliente_id: int,
        pontos: int,
        tipo: str,
        origem: str,
        motivo: str = None,
        reserva_id: int = None,
        funcionario_id: int = None,
        status: str = "liberado",
        liberar_em: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
        pontos_nivel: Optional[int] = None,
        _tx: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Criar transação de pontos completa com todos os relacionamentos

        Args:
            cliente_id: ID do cliente
            pontos: Quantidade de Pontos R (saldo resgatavel); pode ser negativo para debito
            tipo: CREDITO, DEBITO, AJUSTE, ESTORNO
            origem: RESERVA, AJUSTE_MANUAL, CONVITE, etc
            motivo: Descrição da transação
            reserva_id: ID da reserva relacionada (se aplicável)
            funcionario_id: ID do funcionário que fez ajuste (se aplicável)
            metadata: Dados estruturados para auditoria da transação
            pontos_nivel: Quantidade de Pontos N (nivel) a creditar, quando
                difere de `pontos` (ex.: reserva com multiplicador de nivel
                aplicado so aos Pontos R). Se None, usa `pontos` quando
                positivo (comportamento legado para origens sem multiplicador).
                Nunca reduz Pontos N, mesmo se um valor negativo for passado.
            _tx: transação Prisma já aberta pelo chamador (ex.: para manter um
                lock/consulta anterior atômico junto com esta escrita). Se
                None, abre e comita sua própria transação como de costume.
        """
        # VALIDAÇÃO DE SEGURANÇA: Limites de pontos
        if pontos == 0:
            raise ValueError("Transação de 0 pontos não permitida")

        if abs(pontos) > MAX_PONTOS_POR_TRANSACAO:
            raise ValueError(
                f"Transação limitada a ±{MAX_PONTOS_POR_TRANSACAO} pontos. "
                f"Valor solicitado: {pontos}"
            )

        origem_norm = (origem or "").strip().upper()
        status_norm = (status or "liberado").strip().lower()
        if pontos < 0 and status_norm == "liberado":
            status_norm = "debitado"
        aplicar_saldo = status_norm not in {"pendente", "bloqueado", "expirado"}
        origens_idempotencia = (
            ["CHECKOUT", "RESERVA"]
            if origem_norm in {"CHECKOUT", "RESERVA"}
            else [origem_norm]
        )

        async def _executar(transaction) -> Dict[str, Any]:
            if reserva_id and origem_norm in ORIGENS_IDEMPOTENTES_POR_RESERVA:
                transacao_existente = await transaction.transacaopontos.find_first(
                    where={"reservaId": reserva_id, "origem": {"in": origens_idempotencia}}
                )
                if transacao_existente:
                    return {
                        "success": True,
                        "idempotente": True,
                        "transacao_id": transacao_existente.id,
                        "saldo_anterior": getattr(transacao_existente, "saldoAnterior", 0),
                        "saldo_posterior": getattr(transacao_existente, "saldoPosterior", 0),
                        "pontos": getattr(transacao_existente, "pontos", 0),
                        "status": getattr(transacao_existente, "status", "liberado"),
                        "liberar_em": (
                            transacao_existente.liberarEm.isoformat()
                            if getattr(transacao_existente, "liberarEm", None)
                            else None
                        ),
                        "metadata": getattr(transacao_existente, "metadata", None),
                    }

            usuario_pontos_raw = await transaction.query_raw(
                """
                SELECT *
                FROM usuarios_pontos
                WHERE cliente_id = $1
                FOR UPDATE
                """,
                cliente_id,
            )

            if usuario_pontos_raw:
                usuario_pontos_data = usuario_pontos_raw[0]
                usuario_pontos_id = int(usuario_pontos_data["id"])
                saldo_anterior = int(usuario_pontos_data["saldo"])
                pontos_nivel_anterior = int(usuario_pontos_data.get("pontos_nivel") or 0)
            else:
                usuario_pontos = await transaction.usuariopontos.create(
                    data={"clienteId": cliente_id, "saldo": 0}
                )
                usuario_pontos_id = usuario_pontos.id
                saldo_anterior = 0
                pontos_nivel_anterior = 0

            if reserva_id and origem_norm in ORIGENS_IDEMPOTENTES_POR_RESERVA:
                transacao_existente = await transaction.transacaopontos.find_first(
                    where={"reservaId": reserva_id, "origem": {"in": origens_idempotencia}}
                )
                if transacao_existente:
                    return {
                        "success": True,
                        "idempotente": True,
                        "transacao_id": transacao_existente.id,
                        "saldo_anterior": getattr(transacao_existente, "saldoAnterior", 0),
                        "saldo_posterior": getattr(transacao_existente, "saldoPosterior", 0),
                        "pontos": getattr(transacao_existente, "pontos", 0),
                        "status": getattr(transacao_existente, "status", "liberado"),
                        "liberar_em": (
                            transacao_existente.liberarEm.isoformat()
                            if getattr(transacao_existente, "liberarEm", None)
                            else None
                        ),
                        "metadata": getattr(transacao_existente, "metadata", None),
                    }

            saldo_posterior = saldo_anterior + pontos if aplicar_saldo else saldo_anterior

            if saldo_posterior < 0:
                raise ValueError("Saldo insuficiente para esta transação")

            # Pontos N (nivel) so crescem em creditos aplicados; resgate/debito
            # nunca reduz este valor, pois representa progressao permanente.
            pontos_nivel_delta = pontos if pontos_nivel is None else pontos_nivel
            pontos_nivel_posterior = (
                pontos_nivel_anterior + pontos_nivel_delta
                if aplicar_saldo and pontos_nivel_delta > 0
                else pontos_nivel_anterior
            )

            if aplicar_saldo:
                await transaction.execute_raw(
                    """
                    UPDATE usuarios_pontos
                    SET saldo = $1, pontos_nivel = $2, updated_at = NOW()
                    WHERE id = $3
                    """,
                    saldo_posterior,
                    pontos_nivel_posterior,
                    usuario_pontos_id,
                )

            transacao_data = {
                "clienteId": cliente_id,
                "usuarioPontosId": usuario_pontos_id,
                "funcionarioId": funcionario_id,
                "reservaId": reserva_id,
                "tipo": tipo,
                "origem": origem_norm,
                "pontos": pontos,
                "saldoAnterior": saldo_anterior,
                "saldoPosterior": saldo_posterior,
                "status": status_norm,
                "liberarEm": liberar_em,
                "motivo": motivo,
            }
            if metadata is not None:
                transacao_data["metadata"] = json.dumps(metadata) if isinstance(metadata, dict) else metadata

            transacao = await transaction.transacaopontos.create(data=transacao_data)

            return {
                "success": True,
                "transacao_id": transacao.id,
                "saldo_anterior": saldo_anterior,
                "saldo_posterior": saldo_posterior,
                "pontos": pontos,
                "status": status_norm,
                "liberar_em": liberar_em.isoformat() if liberar_em else None,
                "metadata": metadata,
            }

        if _tx is not None:
            return await _executar(_tx)

        async with self.db.tx() as transaction:
            return await _executar(transaction)

    @staticmethod
    def _extrair_pontos_n_metadata(metadata_raw: Any, default: int) -> int:
        """Le pontos_n gravado na metadata da transacao (reserva com nivel/multiplicador).

        Origens sem multiplicador (cupom, promo, indicacao, ajuste manual) nao
        gravam pontos_n na metadata; nesses casos Pontos N == Pontos R, entao
        cai no `default` (o proprio valor de pontos da transacao).
        """
        metadata = metadata_raw
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except (TypeError, ValueError):
                metadata = None
        if isinstance(metadata, dict) and metadata.get("pontos_n") is not None:
            try:
                return int(metadata["pontos_n"])
            except (TypeError, ValueError):
                return default
        return default

    async def liberar_pontos_pendentes(
        self,
        limit: int = 100,
        agora: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Liberar transacoes pendentes cujo liberar_em ja venceu."""
        agora_ref = agora or datetime.now(timezone.utc)
        limite = max(1, min(int(limit or 100), 500))

        pendentes = await self.db.query_raw(
            """
            SELECT id
            FROM transacoes_pontos
            WHERE status = 'pendente'
              AND liberar_em IS NOT NULL
              AND liberar_em <= $1::timestamptz
            ORDER BY liberar_em ASC, id ASC
            LIMIT $2
            """,
            agora_ref,
            limite,
        )

        liberadas: List[Dict[str, Any]] = []
        for row in pendentes:
            transacao_id = int(row["id"])
            async with self.db.tx() as transaction:
                locked_rows = await transaction.query_raw(
                    """
                    SELECT *
                    FROM transacoes_pontos
                    WHERE id = $1
                    FOR UPDATE
                    """,
                    transacao_id,
                )
                if not locked_rows:
                    continue

                transacao = locked_rows[0]
                if (transacao.get("status") or "").lower() != "pendente":
                    continue

                liberar_em = to_utc(transacao.get("liberar_em"))
                if liberar_em and liberar_em > agora_ref:
                    continue

                pontos = int(transacao.get("pontos") or 0)
                if pontos <= 0:
                    await transaction.execute_raw(
                        """
                        UPDATE transacoes_pontos
                        SET status = 'bloqueado'
                        WHERE id = $1
                        """,
                        transacao_id,
                    )
                    continue

                usuario_pontos_id = int(transacao["usuario_pontos_id"])
                usuario_rows = await transaction.query_raw(
                    """
                    SELECT *
                    FROM usuarios_pontos
                    WHERE id = $1
                    FOR UPDATE
                    """,
                    usuario_pontos_id,
                )
                if not usuario_rows:
                    # 48h e o teto maximo de tentativas (RF01/RF02): se passou
                    # desse prazo e ainda nao da pra resolver (inconsistencia
                    # de dados), escalona para "falha" em vez de ficar preso
                    # em pendente para sempre.
                    criado_em = to_utc(transacao.get("created_at"))
                    if criado_em and (agora_ref - criado_em) > timedelta(hours=48):
                        await transaction.execute_raw(
                            """
                            UPDATE transacoes_pontos
                            SET status = 'falha'
                            WHERE id = $1
                            """,
                            transacao_id,
                        )
                    continue

                saldo_anterior = int(usuario_rows[0]["saldo"] or 0)
                saldo_posterior = saldo_anterior + pontos
                pontos_nivel_anterior = int(usuario_rows[0].get("pontos_nivel") or 0)
                pontos_n_credito = self._extrair_pontos_n_metadata(transacao.get("metadata"), default=pontos)
                pontos_nivel_posterior = pontos_nivel_anterior + max(0, pontos_n_credito)

                await transaction.execute_raw(
                    """
                    UPDATE usuarios_pontos
                    SET saldo = $1, pontos_nivel = $2, updated_at = NOW()
                    WHERE id = $3
                    """,
                    saldo_posterior,
                    pontos_nivel_posterior,
                    usuario_pontos_id,
                )
                await transaction.execute_raw(
                    """
                    UPDATE transacoes_pontos
                    SET status = 'liberado',
                        saldo_anterior = $1,
                        saldo_posterior = $2
                    WHERE id = $3
                    """,
                    saldo_anterior,
                    saldo_posterior,
                    transacao_id,
                )

                liberadas.append({
                    "transacao_id": transacao_id,
                    "cliente_id": int(transacao["cliente_id"]),
                    "reserva_id": transacao.get("reserva_id"),
                    "origem": transacao.get("origem"),
                    "metadata": transacao.get("metadata"),
                    "pontos": pontos,
                    "saldo_anterior": saldo_anterior,
                    "saldo_posterior": saldo_posterior,
                })

        for liberada in liberadas:
            await self._notificar_pontos_liberados(liberada)

        return {"success": True, "total_liberadas": len(liberadas), "transacoes": liberadas}

    async def retentar_estornos_pendentes(
        self,
        limit: int = 100,
        agora: Optional[datetime] = None,
        prazo_falha: timedelta = timedelta(days=30),
    ) -> Dict[str, Any]:
        """Reprocessa ESTORNOs que nao puderam ser aplicados na hora do
        cancelamento (saldo insuficiente porque o cliente ja resgatou os
        pontos creditados no checkout).

        Diferente de liberar_pontos_pendentes, aqui nao ha uma data prevista
        de liberacao -- o estorno so fica aplicavel quando o cliente
        acumular saldo suficiente de novo. Por isso o teto antes de desistir
        e marcar como 'falha' (revisao manual) e bem maior: 30 dias.
        """
        agora_ref = agora or datetime.now(timezone.utc)
        limite = max(1, min(int(limit or 100), 500))

        pendentes = await self.db.query_raw(
            """
            SELECT id
            FROM transacoes_pontos
            WHERE tipo = 'ESTORNO'
              AND status = 'pendente'
            ORDER BY created_at ASC, id ASC
            LIMIT $1
            """,
            limite,
        )

        aplicados: List[Dict[str, Any]] = []
        for row in pendentes:
            transacao_id = int(row["id"])
            async with self.db.tx() as transaction:
                locked_rows = await transaction.query_raw(
                    """
                    SELECT *
                    FROM transacoes_pontos
                    WHERE id = $1
                    FOR UPDATE
                    """,
                    transacao_id,
                )
                if not locked_rows:
                    continue

                transacao = locked_rows[0]
                if (transacao.get("status") or "").lower() != "pendente":
                    continue

                pontos = int(transacao.get("pontos") or 0)
                usuario_pontos_id = int(transacao["usuario_pontos_id"])
                usuario_rows = await transaction.query_raw(
                    """
                    SELECT *
                    FROM usuarios_pontos
                    WHERE id = $1
                    FOR UPDATE
                    """,
                    usuario_pontos_id,
                )
                if not usuario_rows:
                    continue

                saldo_anterior = int(usuario_rows[0]["saldo"] or 0)
                saldo_posterior = saldo_anterior + pontos

                if saldo_posterior < 0:
                    criado_em = to_utc(transacao.get("created_at"))
                    if criado_em and (agora_ref - criado_em) > prazo_falha:
                        await transaction.execute_raw(
                            """
                            UPDATE transacoes_pontos
                            SET status = 'falha'
                            WHERE id = $1
                            """,
                            transacao_id,
                        )
                    continue

                await transaction.execute_raw(
                    """
                    UPDATE usuarios_pontos
                    SET saldo = $1, updated_at = NOW()
                    WHERE id = $2
                    """,
                    saldo_posterior,
                    usuario_pontos_id,
                )
                await transaction.execute_raw(
                    """
                    UPDATE transacoes_pontos
                    SET status = 'estornado',
                        saldo_anterior = $1,
                        saldo_posterior = $2
                    WHERE id = $3
                    """,
                    saldo_anterior,
                    saldo_posterior,
                    transacao_id,
                )

                aplicados.append({
                    "transacao_id": transacao_id,
                    "cliente_id": int(transacao["cliente_id"]),
                    "reserva_id": transacao.get("reserva_id"),
                    "pontos": pontos,
                    "saldo_anterior": saldo_anterior,
                    "saldo_posterior": saldo_posterior,
                })

        return {"success": True, "total_aplicados": len(aplicados), "transacoes": aplicados}

    async def _notificar_pontos_liberados(self, transacao: Dict[str, Any]) -> None:
        origem = (transacao.get("origem") or "").strip().upper()
        if origem != "CHECKOUT":
            return

        transacao_id = int(transacao["transacao_id"])
        cliente_id = int(transacao["cliente_id"])
        reserva_id = transacao.get("reserva_id")
        try:
            existente = await self.db.query_raw(
                """
                SELECT id
                FROM logs_jornada
                WHERE acao = 'pontos_pos_checkout_whatsapp'
                  AND payload->>'transacao_id' = $1
                LIMIT 1
                """,
                str(transacao_id),
            )
            if existente:
                return

            rows = await self.db.query_raw(
                """
                SELECT c."nomeCompleto" AS nome_completo,
                       c.telefone,
                       c.documento,
                       r.codigo_reserva
                FROM clientes c
                LEFT JOIN reservas r ON r.id = $2
                WHERE c.id = $1
                LIMIT 1
                """,
                cliente_id,
                int(reserva_id) if reserva_id else None,
            )
            if not rows:
                return

            row = rows[0]
            metadata = transacao.get("metadata") or {}
            from app.services.programa_pontos_service import ProgramaPontosService
            from app.services.notification_service import NotificationService
            from app.services.whatsapp_service import get_whatsapp_service

            programa = await ProgramaPontosService(self.db).obter_programa_cliente(cliente_id)
            proximo_premio = programa.get("proximo_premio") or {}
            whatsapp_result = await get_whatsapp_service().enviar_pontos_pos_checkout(
                cliente_nome=row.get("nome_completo") or "Cliente",
                cliente_telefone=row.get("telefone"),
                documento=row.get("documento"),
                codigo_reserva=row.get("codigo_reserva") or str(reserva_id or transacao_id),
                saldo_atual=int(transacao.get("saldo_posterior") or programa.get("saldo_atual") or 0),
                pontos_ganhos_checkout=int(transacao.get("pontos") or 0),
                faltam_pontos_para_proximo_premio=programa.get("faltam_pontos_para_proximo_premio"),
                proximo_premio_nome=proximo_premio.get("nome"),
            )
            await self.db.execute_raw(
                """
                INSERT INTO logs_jornada (cliente_id, acao, payload, created_at)
                VALUES ($1, $2, CAST($3 AS JSONB), NOW())
                """,
                cliente_id,
                "pontos_pos_checkout_whatsapp",
                json.dumps({
                    "transacao_id": transacao_id,
                    "reserva_id": reserva_id,
                    "pontos": int(transacao.get("pontos") or 0),
                    "saldo_posterior": int(transacao.get("saldo_posterior") or 0),
                    "whatsapp_success": bool(whatsapp_result.get("success")),
                }),
            )
            await NotificationService.notificar_premio_proximo(self.db, cliente_id, reserva_id=reserva_id)
        except Exception as exc:
            print(f"[POS CHECKOUT] Erro ao notificar pontos liberados: {exc}")

    async def listar_ajustes_manuais(
        self,
        cliente_id: Optional[int] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        where: Dict[str, Any] = {
            "origem": {"in": ["AJUSTE_MANUAL", "ESTORNO_AJUSTE_MANUAL"]}
        }
        if cliente_id is not None:
            where["clienteId"] = cliente_id

        transacoes = await self.db.transacaopontos.find_many(
            where=where,
            order={"createdAt": "desc"},
            take=limit,
            include={"cliente": True, "funcionario": True, "reserva": True}
        )

        return {
            "success": True,
            "transacoes": [self._serialize_transacao(t) for t in transacoes],
            "total": len(transacoes)
        }

    async def estornar_ajuste_manual(
        self,
        transacao_id: int,
        funcionario_id: int,
        motivo: Optional[str] = None
    ) -> Dict[str, Any]:
        transacao = await self.db.transacaopontos.find_unique(
            where={"id": transacao_id},
            include={"cliente": True, "funcionario": True}
        )

        if not transacao:
            raise ValueError("Transação não encontrada")

        if transacao.origem != "AJUSTE_MANUAL":
            raise ValueError("Apenas ajustes manuais podem ser estornados")

        estorno_existente = await self.db.transacaopontos.find_first(
            where={
                "origem": "ESTORNO_AJUSTE_MANUAL",
                "clienteId": transacao.clienteId,
                "motivo": {"contains": f"#{transacao_id}"},
            }
        )
        if estorno_existente:
            raise ValueError("Este ajuste manual já foi estornado")

        motivo_estorno = (
            f"Estorno da transação #{transacao_id}"
            + (f" | {motivo.strip()}" if motivo and motivo.strip() else "")
        )

        resultado = await self.criar_transacao_pontos(
            cliente_id=transacao.clienteId,
            pontos=transacao.pontos * -1,
            tipo="ESTORNO",
            origem="ESTORNO_AJUSTE_MANUAL",
            motivo=motivo_estorno,
            funcionario_id=funcionario_id,
            status="estornado",
        )

        return {
            "success": True,
            "transacao_estornada_id": transacao_id,
            **resultado
        }
