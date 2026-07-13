import json
from typing import Any, Dict, Optional

from fastapi import HTTPException

from app.repositories.indicacao_repo import (
    STATUS_CREDITADO,
    STATUS_ENVIADO,
    STATUS_HOSPEDADO,
    STATUS_RESERVADO,
    IndicacaoRepository,
    normalizar_documento,
)
from app.services.programa_pontos_service import ProgramaPontosService
from app.utils.datetime_utils import now_utc


PONTOS_CONVITE_REAL = 5
ORIGEM_FRIEND_REFERRAL = "FRIEND_REFERRAL"
ORIGEM_CONVITE_REAL_LEGADA = "CONVITE_REAL"
ORIGENS_REFERRAL = [ORIGEM_FRIEND_REFERRAL, ORIGEM_CONVITE_REAL_LEGADA]


class IndicacaoService:
    def __init__(self, db):
        self.db = db
        self.repo = IndicacaoRepository(db)

    async def criar_indicacao(self, cliente_indicador_id: int, cpf_indicado: str) -> Dict[str, Any]:
        cpf_indicado_norm = normalizar_documento(cpf_indicado)
        if len(cpf_indicado_norm) != 11:
            raise HTTPException(status_code=400, detail="CPF indicado invÃ¡lido")

        indicador = await self.db.cliente.find_unique(where={"id": cliente_indicador_id})
        if not indicador:
            raise HTTPException(status_code=404, detail="Cliente indicador nÃ£o encontrado")

        cpf_indicador_norm = normalizar_documento(getattr(indicador, "documento", None))
        if not cpf_indicador_norm:
            raise HTTPException(status_code=400, detail="Cliente indicador sem CPF/documento cadastrado")

        if cpf_indicador_norm == cpf_indicado_norm:
            raise HTTPException(status_code=400, detail="AutoindicaÃ§Ã£o nÃ£o permitida")

        existente = await self.repo.get_by_cpf_indicado(cpf_indicado_norm)
        if existente:
            raise HTTPException(status_code=409, detail="CPF indicado jÃ¡ possui indicaÃ§Ã£o")

        cliente_indicado = await self._buscar_cliente_por_documento(cpf_indicado_norm)

        try:
            return await self.repo.create({
                "clienteIndicadorId": cliente_indicador_id,
                "clienteIndicadoId": cliente_indicado.id if cliente_indicado else None,
                "cpfIndicador": cpf_indicador_norm,
                "cpfIndicado": cpf_indicado_norm,
                "status": STATUS_ENVIADO,
                "dataEnvio": now_utc(),
                "pontosCreditados": False,
            })
        except Exception as exc:
            if "unique" in str(exc).lower() or "indicacoes_cpf_indicado_unique" in str(exc).lower():
                raise HTTPException(status_code=409, detail="CPF indicado jÃ¡ possui indicaÃ§Ã£o")
            raise

    async def registrar_reserva_realizada(self, reserva_id: int) -> Dict[str, Any]:
        reserva = await self.db.reserva.find_unique(where={"id": reserva_id}, include={"cliente": True})
        if not reserva or not getattr(reserva, "cliente", None):
            return {"success": False, "motivo": "reserva_ou_cliente_nao_encontrado"}

        cpf_indicado = normalizar_documento(getattr(reserva.cliente, "documento", None))
        if not cpf_indicado:
            return {"success": False, "motivo": "cliente_sem_documento"}

        indicacao = await self.repo.get_by_cpf_indicado(cpf_indicado)
        if not indicacao:
            return {"success": True, "atualizada": False, "motivo": "sem_indicacao"}

        if indicacao["status"] == STATUS_CREDITADO:
            return {"success": True, "atualizada": False, "motivo": "indicacao_ja_creditada"}

        if indicacao.get("reserva_id") and indicacao["reserva_id"] != reserva_id:
            return {"success": True, "atualizada": False, "motivo": "indicacao_ja_vinculada_a_outra_reserva"}

        atualizada = await self.repo.vincular_reserva(
            indicacao_id=indicacao["id"],
            cliente_indicado_id=reserva.clienteId,
            reserva_id=reserva_id,
            data_reserva=getattr(reserva, "createdAt", None) or now_utc(),
        )
        return {"success": True, "atualizada": True, "indicacao": atualizada}

    async def registrar_cupom_amigo_reserva(
        self,
        reserva_id: int,
        cliente_indicador_id: int,
    ) -> Dict[str, Any]:
        reserva = await self.db.reserva.find_unique(where={"id": reserva_id}, include={"cliente": True})
        if not reserva or not getattr(reserva, "cliente", None):
            return {"success": False, "motivo": "reserva_ou_cliente_nao_encontrado"}

        indicador = await self.db.cliente.find_unique(where={"id": cliente_indicador_id})
        if not indicador:
            return {"success": False, "motivo": "cliente_indicador_nao_encontrado"}

        cpf_indicador = normalizar_documento(getattr(indicador, "documento", None))
        cpf_indicado = normalizar_documento(getattr(reserva.cliente, "documento", None))
        if not cpf_indicador or not cpf_indicado:
            return {"success": False, "motivo": "cpf_indicador_ou_indicado_ausente"}

        if cpf_indicador == cpf_indicado or int(cliente_indicador_id) == int(reserva.clienteId):
            return {"success": False, "motivo": "autoindicacao_bloqueada"}

        existente = await self.repo.get_by_cpf_indicado(cpf_indicado)
        if existente:
            if int(existente["cliente_indicador_id"]) != int(cliente_indicador_id):
                return {"success": False, "motivo": "cpf_indicado_ja_usado_em_outra_indicacao"}
            if not existente.get("reserva_id"):
                atualizada = await self.repo.vincular_reserva(
                    indicacao_id=existente["id"],
                    cliente_indicado_id=reserva.clienteId,
                    reserva_id=reserva_id,
                    data_reserva=getattr(reserva, "createdAt", None) or now_utc(),
                )
                return {"success": True, "atualizada": True, "indicacao": atualizada}
            return {"success": True, "atualizada": False, "motivo": "indicacao_ja_vinculada"}

        indicacao = await self.repo.create({
            "clienteIndicadorId": cliente_indicador_id,
            "clienteIndicadoId": reserva.clienteId,
            "reservaId": reserva_id,
            "cpfIndicador": cpf_indicador,
            "cpfIndicado": cpf_indicado,
            "status": STATUS_RESERVADO,
            "dataEnvio": now_utc(),
            "dataReserva": getattr(reserva, "createdAt", None) or now_utc(),
            "pontosCreditados": False,
        })
        return {"success": True, "atualizada": True, "indicacao": indicacao}

    async def registrar_checkin_realizado(self, reserva_id: int, checkin_datetime=None) -> Dict[str, Any]:
        indicacao = await self._buscar_indicacao_por_reserva_ou_cliente(reserva_id)
        if not indicacao:
            return {"success": True, "atualizada": False, "motivo": "sem_indicacao"}

        if indicacao["status"] == STATUS_CREDITADO:
            return {"success": True, "atualizada": False, "motivo": "indicacao_ja_creditada"}

        atualizada = await self.repo.marcar_checkin(
            indicacao_id=indicacao["id"],
            data_checkin=checkin_datetime or now_utc(),
        )
        return {"success": True, "atualizada": True, "indicacao": atualizada}

    async def processar_credito_indicacao_apos_checkout(
        self,
        reserva_id: int,
        funcionario_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        reserva = await self.db.reserva.find_unique(where={"id": reserva_id}, include={"cliente": True, "hospedagem": True})
        if not reserva or not getattr(reserva, "cliente", None):
            return {"success": False, "creditado": False, "motivo": "reserva_ou_cliente_nao_encontrado"}

        status_reserva = str(getattr(reserva, "statusReserva", "") or "").upper()
        checkout_real = (
            getattr(reserva, "checkoutReal", None)
            or getattr(getattr(reserva, "hospedagem", None), "checkoutRealizadoEm", None)
        )
        if not checkout_real and status_reserva not in {"CHECKED_OUT", "CHECKOUT_REALIZADO", "FINALIZADA"}:
            return {"success": True, "creditado": False, "motivo": "checkout_nao_concluido"}

        pagamentos_confirmados = await self.db.query_raw(
            """
            SELECT 1
            FROM pagamentos
            WHERE reserva_id = $1
              AND UPPER(status_pagamento) IN ('PAGO', 'CONFIRMADO', 'APROVADO')
            LIMIT 1
            """,
            reserva_id,
        )
        if not pagamentos_confirmados:
            return {"success": True, "creditado": False, "motivo": "pagamento_nao_confirmado"}

        cpf_indicado = normalizar_documento(getattr(reserva.cliente, "documento", None))
        checkout_datetime = (
            checkout_real
            or now_utc()
        )

        async with self.db.tx() as transaction:
            rows = await transaction.query_raw(
                """
                SELECT *
                FROM indicacoes
                WHERE reserva_id = $1 OR cpf_indicado = $2
                ORDER BY id ASC
                LIMIT 1
                FOR UPDATE
                """,
                reserva_id,
                cpf_indicado,
            )

            if not rows:
                # Autocura: se o vinculo nao foi criado quando o cupom amigo
                # foi aplicado (ex.: falha silenciosa historica do INSERT),
                # deriva a indicacao diretamente do cupom da reserva e segue
                # para o credito na mesma transacao.
                cupom_rows = await transaction.query_raw(
                    """
                    SELECT c.cliente_indicador_id
                    FROM cupons_usos cu
                    JOIN cupons c ON c.id = cu.cupom_id
                    WHERE cu.reserva_id = $1
                      AND UPPER(COALESCE(c.tipo_campanha, '')) = 'CUPOM_AMIGO'
                      AND c.cliente_indicador_id IS NOT NULL
                    LIMIT 1
                    """,
                    reserva_id,
                )
                indicador_id_cupom = int(cupom_rows[0]["cliente_indicador_id"]) if cupom_rows else 0
                if not indicador_id_cupom or indicador_id_cupom == int(getattr(reserva, "clienteId", 0) or 0):
                    return {"success": True, "creditado": False, "motivo": "sem_indicacao"}

                indicador_rows = await transaction.query_raw(
                    "SELECT documento FROM clientes WHERE id = $1 LIMIT 1",
                    indicador_id_cupom,
                )
                cpf_indicador = normalizar_documento(indicador_rows[0]["documento"]) if indicador_rows else ""
                if not cpf_indicador or not cpf_indicado or cpf_indicador == cpf_indicado:
                    return {"success": True, "creditado": False, "motivo": "sem_indicacao"}

                rows = await transaction.query_raw(
                    """
                    INSERT INTO indicacoes (
                        cliente_indicador_id, cliente_indicado_id, reserva_id,
                        cpf_indicador, cpf_indicado, status, data_envio,
                        data_reserva, pontos_creditados, updated_at
                    )
                    VALUES ($1, $2, $3, $4, $5, 'reservado', now(), $6::timestamp, false, now())
                    ON CONFLICT (cpf_indicado) DO NOTHING
                    RETURNING *
                    """,
                    indicador_id_cupom,
                    getattr(reserva, "clienteId", None),
                    reserva_id,
                    cpf_indicador,
                    cpf_indicado,
                    getattr(reserva, "createdAt", None) or now_utc(),
                )
                if not rows:
                    # CPF indicado ja tinha indicacao registrada: recarrega com lock.
                    rows = await transaction.query_raw(
                        "SELECT * FROM indicacoes WHERE cpf_indicado = $1 LIMIT 1 FOR UPDATE",
                        cpf_indicado,
                    )
                if not rows:
                    return {"success": True, "creditado": False, "motivo": "sem_indicacao"}
                print(
                    f"[INDICACAO] Autocura: vinculo criado a partir do cupom amigo "
                    f"(reserva {reserva_id}, indicador {indicador_id_cupom})"
                )

            indicacao = rows[0]
            indicacao_id = int(indicacao["id"])
            if bool(indicacao.get("pontos_creditados")):
                return {"success": True, "creditado": False, "idempotente": True, "motivo": "indicacao_ja_creditada"}

            transacao_existente = await transaction.transacaopontos.find_first(
                where={
                    "reservaId": reserva_id,
                    "tipo": "CREDITO",
                    "origem": {"in": ORIGENS_REFERRAL},
                }
            )
            if transacao_existente:
                await transaction.execute_raw(
                    """
                    UPDATE indicacoes
                    SET cliente_indicado_id = $1,
                        reserva_id = $2,
                        status = $3,
                        data_checkout = $4::timestamp,
                        pontos_creditados = true,
                        transacao_pontos_id = $5,
                        updated_at = now()
                    WHERE id = $6
                    """,
                    getattr(reserva, "clienteId", None),
                    reserva_id,
                    STATUS_CREDITADO,
                    checkout_datetime,
                    transacao_existente.id,
                    indicacao_id,
                )
                return {"success": True, "creditado": False, "idempotente": True, "motivo": "transacao_ja_existente"}

            cliente_indicador_id = int(indicacao["cliente_indicador_id"])
            usuario_pontos_rows = await transaction.query_raw(
                """
                SELECT *
                FROM usuarios_pontos
                WHERE cliente_id = $1
                FOR UPDATE
                """,
                cliente_indicador_id,
            )

            if usuario_pontos_rows:
                usuario_pontos = usuario_pontos_rows[0]
                usuario_pontos_id = int(usuario_pontos["id"])
                saldo_anterior = int(usuario_pontos["saldo"])
                pontos_nivel_anterior = int(usuario_pontos.get("pontos_nivel") or 0)
            else:
                novo_usuario_pontos = await transaction.usuariopontos.create(
                    data={"clienteId": cliente_indicador_id, "saldo": 0}
                )
                usuario_pontos_id = novo_usuario_pontos.id
                saldo_anterior = 0
                pontos_nivel_anterior = 0

            saldo_posterior = saldo_anterior + PONTOS_CONVITE_REAL
            pontos_nivel_posterior = pontos_nivel_anterior + PONTOS_CONVITE_REAL
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

            codigo_reserva = getattr(reserva, "codigoReserva", None) or str(reserva_id)
            transacao = await transaction.transacaopontos.create(
                data={
                    "clienteId": cliente_indicador_id,
                    "usuarioPontosId": usuario_pontos_id,
                    "funcionarioId": funcionario_id,
                    "reservaId": reserva_id,
                    "tipo": "CREDITO",
                    "origem": ORIGEM_FRIEND_REFERRAL,
                    "pontos": PONTOS_CONVITE_REAL,
                    "saldoAnterior": saldo_anterior,
                    "saldoPosterior": saldo_posterior,
                    "motivo": f"Friend Referral - reserva {codigo_reserva}",
                    "metadata": json.dumps({
                        "source": ORIGEM_FRIEND_REFERRAL,
                        "reward_type": ORIGEM_FRIEND_REFERRAL,
                        "operation_key": f"friend_referral:{indicacao_id}:{reserva_id}",
                        "indicacao_id": indicacao_id,
                        "reserva_id": reserva_id,
                        "cliente_indicador_id": cliente_indicador_id,
                        "cliente_indicado_id": getattr(reserva, "clienteId", None),
                        "pontos_r": PONTOS_CONVITE_REAL,
                        "pontos_n": PONTOS_CONVITE_REAL,
                        "idempotency_scope": "reservation_referral_reward",
                    }),
                }
            )

            await transaction.execute_raw(
                """
                UPDATE indicacoes
                SET cliente_indicado_id = $1,
                    reserva_id = $2,
                    status = $3,
                    data_checkout = $4::timestamp,
                    pontos_creditados = true,
                    transacao_pontos_id = $5,
                    updated_at = now()
                WHERE id = $6
                """,
                getattr(reserva, "clienteId", None),
                reserva_id,
                STATUS_CREDITADO,
                checkout_datetime,
                transacao.id,
                indicacao_id,
            )

            return {
                "success": True,
                "creditado": True,
                "indicacao_id": indicacao_id,
                "transacao_id": transacao.id,
                "pontos": PONTOS_CONVITE_REAL,
                "saldo_anterior": saldo_anterior,
                "saldo_posterior": saldo_posterior,
            }

    async def obter_status_cliente(self, cliente_id: int) -> Dict[str, Any]:
        cliente = await self.db.cliente.find_unique(where={"id": cliente_id})
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente nÃ£o encontrado")

        indicacoes = await self.repo.list_by_indicador(cliente_id)
        programa = await ProgramaPontosService(self.db).obter_programa_cliente(cliente_id)
        saldo_atual = programa.get("saldo_atual", 0)
        proximo_premio = programa.get("proximo_premio")
        faltam = programa.get("faltam_pontos_para_proximo_premio")

        ultima = indicacoes[0] if indicacoes else None
        status = ultima["status"] if ultima else "sem_indicacao"
        ja_ganhou = any(i["pontos_creditados"] for i in indicacoes)
        ainda_pode_indicar = not any(i["status"] != STATUS_CREDITADO for i in indicacoes)

        return {
            "status": status,
            "progresso": "1/1" if ja_ganhou else "0/1",
            "ja_ganhou_pontos": ja_ganhou,
            "ainda_pode_indicar": ainda_pode_indicar,
            "saldo_atual": saldo_atual,
            "faltam_pontos_para_proximo_premio": faltam,
            "proximo_premio": proximo_premio,
            "programa_pontos": programa,
            "indicacoes": indicacoes,
        }

    async def listar_indicacoes_cliente(self, cliente_id: int) -> Dict[str, Any]:
        return {"success": True, "indicacoes": await self.repo.list_by_indicador(cliente_id)}

    async def reprocessar_creditos_pendentes(self, limit: int = 100, funcionario_id: Optional[int] = None) -> Dict[str, Any]:
        pendentes = await self.repo.listar_pendentes_com_checkout(limit=limit)
        resultados = []
        creditadas = 0
        for item in pendentes:
            resultado = await self.processar_credito_indicacao_apos_checkout(
                item["reserva_id"],
                funcionario_id=funcionario_id,
            )
            resultados.append({"indicacao_id": item["id"], "reserva_id": item["reserva_id"], **resultado})
            if resultado.get("creditado"):
                creditadas += 1
        return {
            "success": True,
            "processadas": len(pendentes),
            "creditadas": creditadas,
            "resultados": resultados,
        }

    async def _buscar_indicacao_por_reserva_ou_cliente(self, reserva_id: int) -> Optional[Dict[str, Any]]:
        indicacao = await self.repo.get_by_reserva_id(reserva_id)
        if indicacao:
            return indicacao

        reserva = await self.db.reserva.find_unique(where={"id": reserva_id}, include={"cliente": True})
        if not reserva or not getattr(reserva, "cliente", None):
            return None

        cpf_indicado = normalizar_documento(getattr(reserva.cliente, "documento", None))
        if not cpf_indicado:
            return None
        return await self.repo.get_by_cpf_indicado(cpf_indicado)

    async def _buscar_cliente_por_documento(self, documento: str):
        rows = await self.db.query_raw(
            """
            SELECT id
            FROM clientes
            WHERE regexp_replace(documento, '\\D', '', 'g') = $1
            LIMIT 1
            """,
            normalizar_documento(documento),
        )
        if not rows:
            return None
        return await self.db.cliente.find_unique(where={"id": int(rows[0]["id"])})

    async def _obter_saldo(self, cliente_id: int) -> int:
        usuario_pontos = await self.db.usuariopontos.find_unique(where={"clienteId": cliente_id})
        if not usuario_pontos:
            return 0
        return int(getattr(usuario_pontos, "saldo", 0) or 0)

    async def _obter_proximo_premio(self, saldo_atual: int) -> Optional[Dict[str, Any]]:
        premio = await self.db.premio.find_first(
            where={"ativo": True, "precoEmPontos": {"gt": saldo_atual}},
            order={"precoEmPontos": "asc"},
        )
        if not premio:
            return None
        return {
            "id": premio.id,
            "nome": premio.nome,
            "preco_em_pontos": premio.precoEmPontos,
        }


async def processarCreditoIndicacaoAposCheckout(db, reserva_id: int, funcionario_id: Optional[int] = None) -> Dict[str, Any]:
    return await IndicacaoService(db).processar_credito_indicacao_apos_checkout(
        reserva_id=reserva_id,
        funcionario_id=funcionario_id,
    )
