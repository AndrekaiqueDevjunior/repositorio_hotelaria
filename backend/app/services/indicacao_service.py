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
from app.utils.datetime_utils import now_utc


PONTOS_CONVITE_REAL = 3
ORIGEM_CONVITE_REAL = "CONVITE_REAL"


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

        cpf_indicado = normalizar_documento(getattr(reserva.cliente, "documento", None))
        checkout_datetime = (
            getattr(reserva, "checkoutReal", None)
            or getattr(getattr(reserva, "hospedagem", None), "checkoutRealizadoEm", None)
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
                return {"success": True, "creditado": False, "motivo": "sem_indicacao"}

            indicacao = rows[0]
            indicacao_id = int(indicacao["id"])
            if bool(indicacao.get("pontos_creditados")):
                return {"success": True, "creditado": False, "idempotente": True, "motivo": "indicacao_ja_creditada"}

            transacao_existente = await transaction.transacaopontos.find_first(
                where={
                    "reservaId": reserva_id,
                    "tipo": "CREDITO",
                    "origem": ORIGEM_CONVITE_REAL,
                }
            )
            if transacao_existente:
                await transaction.execute_raw(
                    """
                    UPDATE indicacoes
                    SET cliente_indicado_id = $1,
                        reserva_id = $2,
                        status = $3,
                        data_checkout = $4,
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
            else:
                novo_usuario_pontos = await transaction.usuariopontos.create(
                    data={"clienteId": cliente_indicador_id, "saldo": 0}
                )
                usuario_pontos_id = novo_usuario_pontos.id
                saldo_anterior = 0

            saldo_posterior = saldo_anterior + PONTOS_CONVITE_REAL
            await transaction.execute_raw(
                """
                UPDATE usuarios_pontos
                SET saldo = $1, updated_at = NOW()
                WHERE id = $2
                """,
                saldo_posterior,
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
                    "origem": ORIGEM_CONVITE_REAL,
                    "pontos": PONTOS_CONVITE_REAL,
                    "saldoAnterior": saldo_anterior,
                    "saldoPosterior": saldo_posterior,
                    "motivo": f"Convite Real - reserva {codigo_reserva}",
                }
            )

            await transaction.execute_raw(
                """
                UPDATE indicacoes
                SET cliente_indicado_id = $1,
                    reserva_id = $2,
                    status = $3,
                    data_checkout = $4,
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
        saldo_atual = await self._obter_saldo(cliente_id)
        proximo_premio = await self._obter_proximo_premio(saldo_atual)
        faltam = None
        if proximo_premio:
            faltam = max(0, int(proximo_premio["preco_em_pontos"]) - saldo_atual)

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
