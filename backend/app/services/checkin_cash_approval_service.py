import base64
import json
import os
import secrets
from datetime import timedelta
from decimal import Decimal
from typing import Any, Dict, Optional

from fastapi import HTTPException
from prisma import Json as PrismaJson

from app.services.whatsapp_service import get_whatsapp_service
from app.utils.datetime_utils import format_local, now_utc, to_utc


APPROVAL_STATUS_PENDING = "pending"
APPROVAL_STATUS_APPROVED = "approved"
APPROVAL_STATUS_EXPIRED = "expired"
APPROVAL_STATUS_CANCELLED = "cancelled"
APPROVAL_STATUS_REJECTED = "rejected"


def _row_get(row: Any, key: str, default: Any = None) -> Any:
    if isinstance(row, dict):
        return row.get(key, default)
    return getattr(row, key, default)


class CheckinCashApprovalService:
    def __init__(self, db):
        self.db = db

    IMAGENS_EMBUTIVEIS = {".jpg", ".jpeg", ".png"}

    async def solicitar(
        self,
        reservation_id: int,
        amount: Decimal,
        funcionario_id: Optional[int] = None,
        payment_method: str = "cash",
        foto_url: Optional[str] = None,
        foto_base64: Optional[str] = None,
        foto_nome: Optional[str] = None,
    ) -> Dict[str, Any]:
        metodo = (payment_method or "cash").strip().lower()
        if metodo not in {"cash", "dinheiro", "na_chegada"}:
            raise HTTPException(status_code=400, detail="Fluxo CHK aceita apenas pagamento em dinheiro")

        reserva = await self.db.reserva.find_unique(
            where={"id": int(reservation_id)},
            include={"cliente": True},
        )
        if not reserva:
            raise HTTPException(status_code=404, detail="Reserva nao encontrada")

        valor = Decimal(str(amount))
        if valor <= 0:
            raise HTTPException(status_code=400, detail="Valor deve ser maior que zero")

        await self._cancelar_pendentes_expirados(int(reservation_id))
        codigo = await self._gerar_codigo_unico()
        expira_em = now_utc() + timedelta(minutes=30)
        recepcionista_nome = None
        if funcionario_id:
            funcionario = await self.db.funcionario.find_unique(where={"id": int(funcionario_id)})
            recepcionista_nome = getattr(funcionario, "nome", None)

        payload = {
            "reservation_id": int(reservation_id),
            "amount": str(valor),
            "payment_method": metodo,
            "requested_by": funcionario_id,
            "requested_by_name": recepcionista_nome,
            "foto_url": foto_url,
        }

        # Integracao com a tela /comprovantes: o CHK ja nasce com o pagamento
        # em dinheiro PENDENTE vinculado (idempotencyKey chk-<codigo>) e, se a
        # recepcao anexar foto, com o comprovante no fluxo padrao de validacao.
        # A decisao do gerente (WhatsApp ou painel) confirma/nega esse mesmo
        # pagamento e valida/recusa esse mesmo comprovante — nada fica orfao.
        pagamento = await self.db.pagamento.create(
            data={
                "reservaId": int(reservation_id),
                "clienteId": int(getattr(reserva, "clienteId", 0) or 0),
                "valor": valor,
                "metodo": "na_chegada",
                "statusPagamento": "PENDENTE",
                "idempotencyKey": f"chk-{codigo}",
            }
        )

        comprovante_id = None
        if foto_base64 and foto_nome:
            from app.repositories.comprovante_repo import ComprovanteRepository
            from app.schemas.comprovante_schema import ComprovanteUpload, TipoComprovante

            try:
                upload = await ComprovanteRepository(self.db).upload_comprovante(
                    ComprovanteUpload(
                        pagamento_id=pagamento.id,
                        tipo_comprovante=TipoComprovante.DINHEIRO,
                        arquivo_base64=foto_base64,
                        nome_arquivo=foto_nome,
                        observacoes=f"Check-in em dinheiro {codigo}",
                        valor_confirmado=float(valor),
                    )
                )
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc))
            comprovante = upload.get("comprovante")
            comprovante_id = getattr(comprovante, "id", None)

        payload["pagamento_id"] = pagamento.id
        payload["comprovante_id"] = comprovante_id

        approval = await self.db.checkincashapproval.create(
            data={
                "reservaId": int(reservation_id),
                "codigo": codigo,
                "valor": valor,
                "status": APPROVAL_STATUS_PENDING,
                "expiraEm": expira_em,
                "pagamentoId": pagamento.id,
                "payload": PrismaJson(payload),
            }
        )

        cliente = getattr(reserva, "cliente", None)
        cliente_nome = getattr(cliente, "nomeCompleto", None) or getattr(reserva, "clienteNome", "Cliente")
        whatsapp = await get_whatsapp_service().enviar_confirmacao_checkin_dinheiro(
            codigo_reserva=getattr(reserva, "codigoReserva", None) or f"RES-{reservation_id}",
            cliente_nome=cliente_nome,
            valor=float(valor),
            reserva_id=int(reservation_id),
            approval_code=codigo,
        )
        # Pedido de aprovacao com botoes Aprovar/Recusar direto ao gerente;
        # a resposta volta pelo webhook Twilio e resolve o codigo CHK.
        # Foto anexada (jpg/png) vai embutida no card via rota publica
        # /checkins/foto/<codigo>; PDF ou link externo caem no quick-reply.
        servico_whatsapp = get_whatsapp_service()
        foto_link = foto_url
        extensao_foto = os.path.splitext(foto_nome or "")[1].lower()
        if comprovante_id and extensao_foto in self.IMAGENS_EMBUTIVEIS and servico_whatsapp.frontend_base_url:
            foto_link = f"{servico_whatsapp.frontend_base_url}/api/v1/checkins/foto/{codigo}"
        whatsapp_gerente = await servico_whatsapp.enviar_aprovacao_checkin_gerente(
            cliente_nome=cliente_nome,
            cliente_cpf=getattr(cliente, "documento", None),
            recepcionista_nome=recepcionista_nome,
            valor=float(valor),
            horario_checkin=format_local(now_utc(), "%d/%m/%Y %H:%M"),
            approval_code=codigo,
            foto_link=foto_link,
        )
        gerente_sids = [
            r.get("message_sid")
            for r in whatsapp_gerente.get("resultados", [whatsapp_gerente])
            if r.get("message_sid")
        ]
        if gerente_sids:
            payload["gerente_message_sids"] = gerente_sids
            try:
                await self.db.checkincashapproval.update(
                    where={"id": approval.id},
                    data={"payload": PrismaJson(payload)},
                )
            except Exception:
                pass
        await self._registrar_log(
            int(getattr(reserva, "clienteId", 0) or 0) or None,
            "checkin_cash_approval_requested",
            {
                "approval_id": approval.id,
                "codigo": codigo,
                "reservation_id": int(reservation_id),
                "whatsapp_success": bool(whatsapp.get("success")),
                "whatsapp_gerente_success": bool(whatsapp_gerente.get("success")),
            },
        )

        return {
            "success": True,
            "approval_id": approval.id,
            "approval_code": codigo,
            "expires_at": expira_em.isoformat(),
            "qr_code": self._qr_placeholder(codigo),
            "payment_id": pagamento.id,
            "comprovante_id": comprovante_id,
            "whatsapp": whatsapp,
            "whatsapp_gerente": whatsapp_gerente,
        }

    async def aprovar(self, code: str, funcionario_id: Optional[int] = None) -> Dict[str, Any]:
        codigo = (code or "").strip().upper()
        if not codigo.startswith("CHK-"):
            raise HTTPException(status_code=400, detail="Codigo CHK invalido")

        async with self.db.tx() as transaction:
            rows = await transaction.query_raw(
                """
                SELECT *
                FROM checkin_cash_approvals
                WHERE codigo = $1
                FOR UPDATE
                """,
                codigo,
            )
            if not rows:
                raise HTTPException(status_code=404, detail="Codigo CHK nao encontrado")

            approval = rows[0]
            status = (_row_get(approval, "status") or "").lower()
            if status == APPROVAL_STATUS_APPROVED:
                raise HTTPException(status_code=400, detail="Codigo ja foi utilizado")
            if status != APPROVAL_STATUS_PENDING:
                raise HTTPException(status_code=400, detail=f"Codigo indisponivel: {status}")

            expira_em = to_utc(_row_get(approval, "expira_em"))
            if expira_em and expira_em < now_utc():
                await transaction.execute_raw(
                    """
                    UPDATE checkin_cash_approvals
                    SET status = $1, updated_at = NOW()
                    WHERE codigo = $2
                    """,
                    APPROVAL_STATUS_EXPIRED,
                    codigo,
                )
                raise HTTPException(status_code=400, detail="Codigo expirado")

            reserva_id = int(_row_get(approval, "reserva_id"))
            reserva_rows = await transaction.query_raw(
                """
                SELECT id, cliente_id, codigo_reserva, cliente_nome, status_reserva
                FROM reservas
                WHERE id = $1
                FOR UPDATE
                """,
                reserva_id,
            )
            if not reserva_rows:
                raise HTTPException(status_code=404, detail="Reserva nao encontrada")

            reserva = reserva_rows[0]
            # O pagamento PENDENTE criado junto com o CHK (idempotency chk-*)
            # e confirmado aqui; approvals antigos sem pagamento vinculado
            # seguem o caminho legado (reaproveita confirmado ou cria).
            pagamento_chk_rows = await transaction.query_raw(
                """
                SELECT id
                FROM pagamentos
                WHERE idempotency_key = $1
                FOR UPDATE
                """,
                f"chk-{codigo}",
            )
            if pagamento_chk_rows:
                pagamento_id = int(pagamento_chk_rows[0]["id"])
                await transaction.execute_raw(
                    """
                    UPDATE pagamentos
                    SET status_pagamento = 'CONFIRMADO', updated_at = NOW()
                    WHERE id = $1
                    """,
                    pagamento_id,
                )
            else:
                pagamento_rows = await transaction.query_raw(
                    """
                    SELECT id
                    FROM pagamentos
                    WHERE reserva_id = $1
                      AND metodo IN ('na_chegada', 'dinheiro', 'cash')
                      AND status_pagamento IN ('PAGO', 'CONFIRMADO', 'APROVADO')
                    ORDER BY id DESC
                    LIMIT 1
                    """,
                    reserva_id,
                )
                if pagamento_rows:
                    pagamento_id = int(pagamento_rows[0]["id"])
                else:
                    pagamento = await transaction.pagamento.create(
                        data={
                            "reservaId": reserva_id,
                            "clienteId": int(reserva["cliente_id"]),
                            "valor": Decimal(str(_row_get(approval, "valor"))),
                            "metodo": "na_chegada",
                            "statusPagamento": "CONFIRMADO",
                            "idempotencyKey": f"chk-{codigo}",
                        }
                    )
                    pagamento_id = pagamento.id

            # Comprovante anexado no CHK e validado pela mesma decisao
            # (validador_id null = gerente via WhatsApp), mantendo a tela
            # /comprovantes consistente com o painel de aprovacoes.
            await transaction.execute_raw(
                """
                UPDATE comprovantes_pagamento
                SET status_validacao = 'APROVADO',
                    data_validacao = NOW(),
                    validador_id = $1,
                    updated_at = NOW()
                WHERE pagamento_id = $2
                  AND status_validacao NOT IN ('APROVADO', 'RECUSADO', 'CANCELADO')
                """,
                funcionario_id,
                pagamento_id,
            )

            aprovado_em = now_utc()
            await transaction.execute_raw(
                """
                UPDATE reservas
                SET status_reserva = 'CONFIRMADA',
                    forma_pagamento = COALESCE(forma_pagamento, 'na_chegada'),
                    updated_at = NOW()
                WHERE id = $1
                  AND status_reserva NOT IN ('CHECKIN_REALIZADO', 'HOSPEDADO', 'CHECKOUT_REALIZADO', 'CANCELADA', 'CANCELADO', 'NO_SHOW')
                """,
                reserva_id,
            )
            await transaction.execute_raw(
                """
                UPDATE checkin_cash_approvals
                SET status = $1,
                    aprovado_em = $2::timestamptz,
                    aprovado_por = $3,
                    pagamento_id = $4,
                    updated_at = NOW()
                WHERE codigo = $5
                """,
                APPROVAL_STATUS_APPROVED,
                aprovado_em,
                funcionario_id,
                pagamento_id,
                codigo,
            )
            await transaction.execute_raw(
                """
                INSERT INTO logs_jornada (cliente_id, acao, payload, created_at)
                VALUES ($1, $2, CAST($3 AS JSONB), NOW())
                """,
                int(reserva["cliente_id"]),
                "checkin_cash_approval_approved",
                json.dumps({
                    "codigo": codigo,
                    "reservation_id": reserva_id,
                    "pagamento_id": pagamento_id,
                    "funcionario_id": funcionario_id,
                }),
            )

        return {
            "success": True,
            "approved": True,
            "approval_code": codigo,
            "reservation_id": reserva_id,
            "payment_id": pagamento_id,
            "checkin_at": aprovado_em.isoformat(),
        }

    async def recusar(
        self,
        code: str,
        funcionario_id: Optional[int] = None,
        motivo: Optional[str] = None,
    ) -> Dict[str, Any]:
        codigo = (code or "").strip().upper()
        if not codigo.startswith("CHK-"):
            raise HTTPException(status_code=400, detail="Codigo CHK invalido")

        async with self.db.tx() as transaction:
            rows = await transaction.query_raw(
                """
                SELECT *
                FROM checkin_cash_approvals
                WHERE codigo = $1
                FOR UPDATE
                """,
                codigo,
            )
            if not rows:
                raise HTTPException(status_code=404, detail="Codigo CHK nao encontrado")

            approval = rows[0]
            status = (_row_get(approval, "status") or "").lower()
            if status != APPROVAL_STATUS_PENDING:
                raise HTTPException(status_code=400, detail=f"Codigo indisponivel: {status}")

            reserva_id = int(_row_get(approval, "reserva_id"))
            await transaction.execute_raw(
                """
                UPDATE checkin_cash_approvals
                SET status = $1, aprovado_por = $2, updated_at = NOW()
                WHERE codigo = $3
                """,
                APPROVAL_STATUS_REJECTED,
                funcionario_id,
                codigo,
            )
            # Reflete a recusa no pagamento e no comprovante vinculados ao
            # CHK, mantendo a tela /comprovantes sincronizada com a decisao.
            pagamento_id = _row_get(approval, "pagamento_id")
            if pagamento_id:
                await transaction.execute_raw(
                    """
                    UPDATE pagamentos
                    SET status_pagamento = 'NEGADO', updated_at = NOW()
                    WHERE id = $1
                      AND status_pagamento = 'PENDENTE'
                    """,
                    int(pagamento_id),
                )
                await transaction.execute_raw(
                    """
                    UPDATE comprovantes_pagamento
                    SET status_validacao = 'RECUSADO',
                        motivo_recusa = $1,
                        data_validacao = NOW(),
                        validador_id = $2,
                        updated_at = NOW()
                    WHERE pagamento_id = $3
                      AND status_validacao NOT IN ('APROVADO', 'RECUSADO', 'CANCELADO')
                    """,
                    motivo or "Check-in em dinheiro recusado",
                    funcionario_id,
                    int(pagamento_id),
                )
            reserva_rows = await transaction.query_raw(
                "SELECT cliente_id FROM reservas WHERE id = $1",
                reserva_id,
            )
            cliente_id = int(reserva_rows[0]["cliente_id"]) if reserva_rows else None
            await transaction.execute_raw(
                """
                INSERT INTO logs_jornada (cliente_id, acao, payload, created_at)
                VALUES ($1, $2, CAST($3 AS JSONB), NOW())
                """,
                cliente_id,
                "checkin_cash_approval_rejected",
                json.dumps({
                    "codigo": codigo,
                    "reservation_id": reserva_id,
                    "funcionario_id": funcionario_id,
                    "motivo": motivo,
                }),
            )

        return {
            "success": True,
            "approved": False,
            "rejected": True,
            "approval_code": codigo,
            "reservation_id": reserva_id,
        }

    async def obter_foto(self, code: str) -> Dict[str, str]:
        """Localiza o arquivo do comprovante vinculado ao CHK.

        Usado pela rota publica que o WhatsApp consome para embutir a foto
        no card do gerente. Protegido pelo codigo CHK nao-adivinhavel e por
        janela de 24h a partir da criacao da aprovacao.
        """
        codigo = (code or "").strip().upper()
        if not codigo.startswith("CHK-"):
            raise HTTPException(status_code=404, detail="Foto nao encontrada")

        approval = await self.db.checkincashapproval.find_unique(where={"codigo": codigo})
        pagamento_id = getattr(approval, "pagamentoId", None) if approval else None
        if not approval or not pagamento_id:
            raise HTTPException(status_code=404, detail="Foto nao encontrada")

        criado_em = to_utc(getattr(approval, "createdAt", None))
        if not criado_em or now_utc() - criado_em > timedelta(hours=24):
            raise HTTPException(status_code=404, detail="Foto nao encontrada")

        comprovante = await self.db.comprovantepagamento.find_first(
            where={"pagamentoId": int(pagamento_id)},
            order={"id": "desc"},
        )
        caminho = getattr(comprovante, "caminhoArquivo", None) if comprovante else None
        if not caminho:
            raise HTTPException(status_code=404, detail="Foto nao encontrada")

        return {
            "caminho": caminho,
            "nome": getattr(comprovante, "nomeArquivo", None) or "comprovante",
        }

    async def encontrar_codigo_por_message_sid(self, message_sid: str) -> Optional[str]:
        """Resolve o codigo CHK a partir do SID da mensagem enviada ao gerente
        (OriginalRepliedMessageSid do webhook quando ele toca no botao)."""
        sid = (message_sid or "").strip()
        if not sid:
            return None
        rows = await self.db.query_raw(
            """
            SELECT codigo
            FROM checkin_cash_approvals
            WHERE payload->'gerente_message_sids' @> to_jsonb($1::text)
            ORDER BY created_at DESC
            LIMIT 1
            """,
            sid,
        )
        return rows[0]["codigo"] if rows else None

    async def codigo_pendente_unico(self) -> Optional[str]:
        """Fallback quando o webhook nao traz o SID da mensagem original: se
        existe exatamente UMA aprovacao pendente valida, e inequivoco qual o
        gerente esta respondendo."""
        rows = await self.db.query_raw(
            """
            SELECT codigo
            FROM checkin_cash_approvals
            WHERE status = $1
              AND expira_em > NOW()
            ORDER BY created_at DESC
            LIMIT 2
            """,
            APPROVAL_STATUS_PENDING,
        )
        return rows[0]["codigo"] if len(rows) == 1 else None

    async def listar(self, status: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        await self._expirar_pendentes_vencidos()

        status_norm = (status or "all").strip().lower()
        allowed_statuses = {
            "all",
            APPROVAL_STATUS_PENDING,
            APPROVAL_STATUS_APPROVED,
            APPROVAL_STATUS_EXPIRED,
            APPROVAL_STATUS_CANCELLED,
            APPROVAL_STATUS_REJECTED,
        }
        if status_norm not in allowed_statuses:
            raise HTTPException(status_code=400, detail="Status de aprovacao CHK invalido")

        limite = max(1, min(int(limit or 50), 200))
        rows = await self.db.query_raw(
            """
            SELECT
                a.id,
                a.reserva_id,
                a.codigo,
                a.valor,
                a.status,
                a.expira_em,
                a.aprovado_em,
                a.aprovado_por,
                a.pagamento_id,
                a.payload,
                a.created_at,
                a.updated_at,
                r.codigo_reserva,
                r.cliente_nome,
                r.quarto_numero,
                r.status_reserva,
                c.telefone AS cliente_telefone,
                f.nome AS aprovado_por_nome
            FROM checkin_cash_approvals a
            JOIN reservas r ON r.id = a.reserva_id
            LEFT JOIN clientes c ON c.id = r.cliente_id
            LEFT JOIN funcionarios f ON f.id = a.aprovado_por
            WHERE ($1 = 'all' OR a.status = $1)
            ORDER BY
                CASE WHEN a.status = 'pending' THEN 0 ELSE 1 END,
                a.created_at DESC
            LIMIT $2
            """,
            status_norm,
            limite,
        )
        approvals = [self._serialize_approval_row(row) for row in rows]
        return {"success": True, "approvals": approvals, "total": len(approvals)}

    async def _cancelar_pendentes_expirados(self, reservation_id: int) -> None:
        # Cancela tambem o pagamento PENDENTE e o comprovante do CHK antigo
        # antes de marcar a approval como cancelada (senao ficam orfaos na
        # tela /comprovantes aguardando uma validacao que nunca vem).
        await self.db.execute_raw(
            """
            UPDATE comprovantes_pagamento
            SET status_validacao = 'CANCELADO', updated_at = NOW()
            WHERE pagamento_id IN (
                SELECT pagamento_id FROM checkin_cash_approvals
                WHERE reserva_id = $1 AND status = $2 AND pagamento_id IS NOT NULL
            )
              AND status_validacao NOT IN ('APROVADO', 'RECUSADO', 'CANCELADO')
            """,
            int(reservation_id),
            APPROVAL_STATUS_PENDING,
        )
        await self.db.execute_raw(
            """
            UPDATE pagamentos
            SET status_pagamento = 'CANCELADO', updated_at = NOW()
            WHERE id IN (
                SELECT pagamento_id FROM checkin_cash_approvals
                WHERE reserva_id = $1 AND status = $2 AND pagamento_id IS NOT NULL
            )
              AND status_pagamento = 'PENDENTE'
            """,
            int(reservation_id),
            APPROVAL_STATUS_PENDING,
        )
        await self.db.execute_raw(
            """
            UPDATE checkin_cash_approvals
            SET status = $1, updated_at = NOW()
            WHERE reserva_id = $2
              AND status = $3
            """,
            APPROVAL_STATUS_CANCELLED,
            int(reservation_id),
            APPROVAL_STATUS_PENDING,
        )

    async def _expirar_pendentes_vencidos(self) -> None:
        try:
            await self.db.execute_raw(
                """
                UPDATE checkin_cash_approvals
                SET status = $1, updated_at = NOW()
                WHERE status = $2
                  AND expira_em < NOW()
                """,
                APPROVAL_STATUS_EXPIRED,
                APPROVAL_STATUS_PENDING,
            )
        except Exception:
            pass

    async def _gerar_codigo_unico(self) -> str:
        for _ in range(20):
            codigo = f"CHK-{secrets.token_hex(4).upper()}"
            existente = await self.db.checkincashapproval.find_unique(where={"codigo": codigo})
            if not existente:
                return codigo
        raise HTTPException(status_code=409, detail="Nao foi possivel gerar codigo CHK unico")

    async def _registrar_log(self, cliente_id: Optional[int], acao: str, payload: Dict[str, Any]) -> None:
        try:
            await self.db.execute_raw(
                """
                INSERT INTO logs_jornada (cliente_id, acao, payload, created_at)
                VALUES ($1, $2, CAST($3 AS JSONB), NOW())
                """,
                cliente_id,
                acao,
                json.dumps(payload),
            )
        except Exception:
            pass

    def _qr_placeholder(self, codigo: str) -> str:
        payload = base64.b64encode(codigo.encode("utf-8")).decode("ascii")
        return f"data:text/plain;base64,{payload}"

    def _serialize_approval_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        expira_em = to_utc(_row_get(row, "expira_em"))
        aprovado_em = to_utc(_row_get(row, "aprovado_em"))
        created_at = to_utc(_row_get(row, "created_at"))
        updated_at = to_utc(_row_get(row, "updated_at"))
        status = (_row_get(row, "status") or APPROVAL_STATUS_PENDING).lower()
        is_expired = bool(expira_em and expira_em < now_utc())
        can_approve = status == APPROVAL_STATUS_PENDING and not is_expired
        payload = _row_get(row, "payload")
        return {
            "id": int(_row_get(row, "id")),
            "approval_id": int(_row_get(row, "id")),
            "approval_code": _row_get(row, "codigo"),
            "code": _row_get(row, "codigo"),
            "reservation_id": int(_row_get(row, "reserva_id")),
            "codigo_reserva": _row_get(row, "codigo_reserva"),
            "guest_name": _row_get(row, "cliente_nome"),
            "cliente_nome": _row_get(row, "cliente_nome"),
            "cliente_telefone": _row_get(row, "cliente_telefone"),
            "room": _row_get(row, "quarto_numero"),
            "room_number": _row_get(row, "quarto_numero"),
            "amount": float(Decimal(str(_row_get(row, "valor") or 0))),
            "valor": float(Decimal(str(_row_get(row, "valor") or 0))),
            "status": APPROVAL_STATUS_EXPIRED if is_expired and status == APPROVAL_STATUS_PENDING else status,
            "reservation_status": _row_get(row, "status_reserva"),
            "expires_at": expira_em.isoformat() if expira_em else None,
            "approved_at": aprovado_em.isoformat() if aprovado_em else None,
            "approved_by": _row_get(row, "aprovado_por"),
            "approved_by_name": _row_get(row, "aprovado_por_nome"),
            "payment_id": _row_get(row, "pagamento_id"),
            "requested_at": created_at.isoformat() if created_at else None,
            "created_at": created_at.isoformat() if created_at else None,
            "updated_at": updated_at.isoformat() if updated_at else None,
            "is_expired": is_expired,
            "can_approve": can_approve,
            "payload": payload if isinstance(payload, dict) else None,
        }
