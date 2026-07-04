"""
Repositorio de premios com transacoes atomicas.

O resgate usa lock pessimista para proteger saldo, estoque e uso unico do
codigo de resgate.
"""

import json
import logging
import secrets
from datetime import timedelta
from typing import Any, Dict, List, Optional

from prisma import Client
from prisma.errors import UniqueViolationError

from app.utils.datetime_utils import now_utc, to_utc

security_logger = logging.getLogger("security")

CODIGO_STATUS_ACTIVE = "ativo"
CODIGO_STATUS_USED = "utilizado"
CODIGO_STATUS_EXPIRED = "expirado"
CODIGO_STATUS_CANCELLED = "cancelado"
RESGATE_STATUS_AGUARDANDO_USO = "aguardando_uso"
RESGATE_STATUS_UTILIZADO = "utilizado"


def _row_get(row: Any, key: str, default: Any = None) -> Any:
    if isinstance(row, dict):
        return row.get(key, default)
    return getattr(row, key, default)


class PremioRepositoryAtomic:
    """Repositorio de premios com consistencia transacional."""

    def __init__(self, db: Client):
        self.db = db

    async def list_all(self, apenas_ativos: bool = True) -> List[Dict[str, Any]]:
        where = {"ativo": True} if apenas_ativos else {}
        premios = await self.db.premio.find_many(
            where=where,
            order={"precoEmPontos": "asc"},
        )
        return [self._serialize(p) for p in premios]

    async def get_by_id(self, premio_id: int) -> Optional[Dict[str, Any]]:
        premio = await self.db.premio.find_unique(where={"id": premio_id})
        if not premio:
            return None
        return self._serialize(premio)

    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        preco_rp = data.get("preco_em_rp")
        if preco_rp is None:
            preco_rp = data.get("preco_em_pontos", 0)

        premio = await self.db.premio.create(
            data={
                "nome": data["nome"],
                "descricao": data.get("descricao"),
                "precoEmPontos": data["preco_em_pontos"],
                "precoEmRp": preco_rp,
                "ativo": data.get("ativo", True),
                "categoria": data.get("categoria", "GERAL"),
                "categoriaId": data.get("categoria_id"),
                "estoque": data.get("estoque"),
                "imagemUrl": data.get("imagem_url"),
            }
        )
        return self._serialize(premio)

    async def update(self, premio_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        premio = await self.db.premio.find_unique(where={"id": premio_id})
        if not premio:
            return None

        update_data: Dict[str, Any] = {}
        if "nome" in data:
            update_data["nome"] = data["nome"]
        if "descricao" in data:
            update_data["descricao"] = data["descricao"]
        if "preco_em_pontos" in data:
            update_data["precoEmPontos"] = data["preco_em_pontos"]
        if "preco_em_rp" in data:
            update_data["precoEmRp"] = data["preco_em_rp"]
        if "ativo" in data:
            update_data["ativo"] = data["ativo"]
        if "categoria" in data:
            update_data["categoria"] = data["categoria"]
        if "categoria_id" in data:
            update_data["categoriaId"] = data["categoria_id"]
        if "estoque" in data:
            update_data["estoque"] = data["estoque"]
        if "imagem_url" in data:
            update_data["imagemUrl"] = data["imagem_url"]

        if not update_data:
            return self._serialize(premio)

        premio_atualizado = await self.db.premio.update(
            where={"id": premio_id},
            data=update_data,
        )
        return self._serialize(premio_atualizado)

    async def delete(self, premio_id: int) -> bool:
        premio = await self.db.premio.find_unique(where={"id": premio_id})
        if not premio:
            return False
        await self.db.premio.update(where={"id": premio_id}, data={"ativo": False})
        return True

    async def resgatar_atomic(
        self,
        premio_id: int,
        cliente_id: int,
        funcionario_id: int = None,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        cliente_nome = "Cliente"
        cliente_telefone = None
        cliente_endereco = None
        codigo_resgate = None
        premio_nome = None
        custo = 0

        # Sem isso, um duplo-clique ou retry de rede no endpoint de resgate
        # debitava pontos duas vezes (mesmo com os locks de saldo/estoque
        # abaixo, que so garantem consistencia, nao deduplicacao). Fast-path
        # fora da transacao; a unique constraint em idempotency_key e quem
        # fecha a corrida de verdade (ver except UniqueViolationError abaixo).
        if idempotency_key:
            existente = await self._buscar_resgate_por_idempotency_key(self.db, idempotency_key)
            if existente:
                return existente

        try:
            return await self._resgatar_atomic_tx(
                premio_id=premio_id,
                cliente_id=cliente_id,
                funcionario_id=funcionario_id,
                idempotency_key=idempotency_key,
            )
        except UniqueViolationError:
            # Duas requisicoes com a mesma idempotency_key correram e uma
            # ganhou a corrida na constraint unica -- devolve o resgate dela
            # em vez de propagar o erro (a transacao perdedora ja fez
            # rollback completo do debito de saldo/estoque desta tentativa).
            if idempotency_key:
                existente = await self._buscar_resgate_por_idempotency_key(self.db, idempotency_key)
                if existente:
                    return existente
            raise

    async def _resgatar_atomic_tx(
        self,
        premio_id: int,
        cliente_id: int,
        funcionario_id: Optional[int],
        idempotency_key: Optional[str],
    ) -> Dict[str, Any]:
        cliente_nome = "Cliente"
        cliente_telefone = None
        cliente_endereco = None
        codigo_resgate = None
        premio_nome = None
        custo = 0

        async with self.db.tx() as transaction:
            cliente_raw = await transaction.query_raw(
                'SELECT id, "nomeCompleto", telefone, "enderecoCompleto" FROM clientes WHERE id = $1',
                cliente_id,
            )
            if not cliente_raw:
                return {"success": False, "error": "Cliente nao encontrado"}

            cliente_dados = cliente_raw[0]
            cliente_nome = cliente_dados.get("nomeCompleto") or "Cliente"
            cliente_telefone = cliente_dados.get("telefone")
            cliente_endereco = cliente_dados.get("enderecoCompleto")

            premio_raw = await transaction.query_raw(
                """
                SELECT *
                FROM premios
                WHERE id = $1
                FOR UPDATE
                """,
                premio_id,
            )
            if not premio_raw:
                return {"success": False, "error": "Premio nao encontrado"}

            premio_data = premio_raw[0]
            if not premio_data["ativo"]:
                return {"success": False, "error": "Premio nao esta ativo"}

            estoque_atual = premio_data.get("estoque")
            if estoque_atual is not None and int(estoque_atual) <= 0:
                security_logger.warning(
                    "Tentativa de resgate com estoque esgotado - "
                    f"Premio: {premio_id}, Cliente: {cliente_id}"
                )
                return {"success": False, "error": "Premio sem estoque disponivel"}

            custo = int(premio_data["preco_em_pontos"])
            premio_nome = premio_data["nome"]
            categoria_nome = premio_data.get("categoria")
            categoria_id = premio_data.get("categoria_id")
            if categoria_id:
                categoria_raw = await transaction.query_raw(
                    "SELECT nome FROM categorias_premios WHERE id = $1",
                    int(categoria_id),
                )
                if categoria_raw:
                    categoria_nome = categoria_raw[0].get("nome") or categoria_nome

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
                saldo_atual = int(usuario_pontos_data["saldo"] or 0)
                usuario_pontos_id = int(usuario_pontos_data["id"])
            else:
                usuario_pontos = await transaction.usuariopontos.create(
                    data={"clienteId": cliente_id, "saldo": 0}
                )
                saldo_atual = 0
                usuario_pontos_id = usuario_pontos.id

            if saldo_atual < custo:
                security_logger.warning(
                    "Tentativa de resgate com saldo insuficiente - "
                    f"Cliente: {cliente_id}, Saldo: {saldo_atual}, Custo: {custo}"
                )
                return {
                    "success": False,
                    "error": f"Saldo insuficiente. Necessario: {custo} pontos. Disponivel: {saldo_atual} pontos",
                }

            novo_saldo = saldo_atual - custo
            await transaction.execute_raw(
                """
                UPDATE usuarios_pontos
                SET saldo = $1, updated_at = NOW()
                WHERE id = $2
                """,
                novo_saldo,
                usuario_pontos_id,
            )

            transacao_pontos = await transaction.transacaopontos.create(
                data={
                    "clienteId": cliente_id,
                    "usuarioPontosId": usuario_pontos_id,
                    "funcionarioId": funcionario_id,
                    "tipo": "debito_resgate",
                    "origem": "PREMIO",
                    "pontos": -custo,
                    "saldoAnterior": saldo_atual,
                    "saldoPosterior": novo_saldo,
                    "status": "debitado",
                    "motivo": f"Resgate de premio: {premio_nome}",
                }
            )

            if estoque_atual is not None:
                await transaction.execute_raw(
                    """
                    UPDATE premios
                    SET estoque = estoque - 1, updated_at = NOW()
                    WHERE id = $1 AND estoque > 0
                    """,
                    premio_id,
                )
                estoque_verificacao = await transaction.query_raw(
                    "SELECT estoque FROM premios WHERE id = $1",
                    premio_id,
                )
                if estoque_verificacao and int(estoque_verificacao[0]["estoque"]) < 0:
                    raise Exception("Estoque ficou negativo durante o processamento")

            codigo_resgate = await self._gerar_codigo_resgate(transaction)
            expira_em = now_utc() + timedelta(days=30)

            resgate = await transaction.resgatepremio.create(
                data={
                    "clienteId": cliente_id,
                    "premioId": premio_id,
                    "pontosUsados": custo,
                    "status": RESGATE_STATUS_AGUARDANDO_USO,
                    "codigoResgate": codigo_resgate,
                    "codigoStatus": CODIGO_STATUS_ACTIVE,
                    "expiraEm": expira_em,
                    "funcionarioId": funcionario_id,
                    "idempotencyKey": idempotency_key,
                }
            )

            codigo_row = await transaction.codigoresgate.create(
                data={
                    "resgateId": resgate.id,
                    "codigo": codigo_resgate,
                    "status": CODIGO_STATUS_ACTIVE,
                    "validoAte": expira_em,
                    "funcionarioId": funcionario_id,
                }
            )

            await transaction.execute_raw(
                """
                INSERT INTO logs_jornada (cliente_id, acao, payload, created_at)
                VALUES ($1, $2, CAST($3 AS JSONB), NOW())
                """,
                cliente_id,
                "resgate_premio",
                json.dumps({
                    "premio_id": premio_id,
                    "premio_nome": premio_nome,
                    "resgate_id": resgate.id,
                    "codigo": codigo_resgate,
                    "pontos_usados": custo,
                }),
            )

            security_logger.info(
                "Resgate atomico realizado com sucesso - "
                f"Cliente: {cliente_id}, Premio: {premio_id} ({premio_nome}), "
                f"Pontos: {custo}, Saldo: {saldo_atual} -> {novo_saldo}, Codigo: {codigo_resgate}"
            )

            result = {
                "success": True,
                "resgate_id": resgate.id,
                "status": RESGATE_STATUS_AGUARDANDO_USO,
                "premio": {
                    "id": premio_data["id"],
                    "nome": premio_nome,
                    "categoria": categoria_nome,
                    "preco_em_pontos": custo,
                },
                "pontos_usados": custo,
                "novo_saldo": novo_saldo,
                "transacao_id": transacao_pontos.id,
                "cliente_nome": cliente_nome,
                "codigo": codigo_row.codigo,
                "codigo_resgate": codigo_row.codigo,
                "codigo_status": CODIGO_STATUS_ACTIVE,
                "valido_ate": expira_em.isoformat(),
                "expira_em": expira_em.isoformat(),
                "mensagem": "Experiencia confirmada com sucesso.",
            }

        try:
            from app.services.whatsapp_service import get_whatsapp_service

            whatsapp_service = get_whatsapp_service()

            # Notificacao operacional para o hotel (quem vai entregar o premio)
            notificacao_result = await whatsapp_service.enviar_notificacao_resgate_premio(
                cliente_nome=cliente_nome,
                cliente_telefone=cliente_telefone,
                cliente_endereco=cliente_endereco,
                premio_nome=premio_nome,
                pontos_usados=custo,
                codigo_resgate=codigo_resgate,
            )
            if notificacao_result.get("success"):
                security_logger.info(
                    "Notificacao WhatsApp (hotel) enviada - "
                    f"Resgate: {result.get('resgate_id')}, SID: {notificacao_result.get('message_sid')}"
                )

            # Confirmacao ao cliente com o codigo de resgate
            confirmacao_result = await whatsapp_service.enviar_confirmacao_resgate_cliente(
                cliente_telefone=cliente_telefone,
                premio_nome=premio_nome,
                codigo_resgate=codigo_resgate,
                pontos_usados=custo,
                valido_ate=result.get("valido_ate"),
            )
            if confirmacao_result.get("success"):
                security_logger.info(
                    "Confirmacao WhatsApp (cliente) enviada - "
                    f"Resgate: {result.get('resgate_id')}, SID: {confirmacao_result.get('message_sid')}"
                )
        except Exception as exc:
            security_logger.error(f"Erro ao enviar notificacao WhatsApp: {exc}")

        return result

    async def obter_codigo_resgate(self, codigo_resgate: str) -> Dict[str, Any]:
        codigo = self._normalizar_codigo(codigo_resgate)
        if not codigo:
            return {"success": False, "error": "Codigo de resgate obrigatorio"}

        rows = await self.db.query_raw(
            """
            SELECT cr.id,
                   cr.codigo,
                   cr.status,
                   cr.valido_ate,
                   cr.utilizado_em,
                   rp.id AS resgate_id,
                   rp.pontos_usados,
                   p.id AS premio_id,
                   p.nome AS premio_nome,
                   p.categoria AS premio_categoria
            FROM codigos_resgate cr
            JOIN resgates_premios rp ON rp.id = cr.resgate_id
            JOIN premios p ON p.id = rp.premio_id
            WHERE cr.codigo = $1
            LIMIT 1
            """,
            codigo,
        )
        if not rows:
            return {"success": False, "error": "Codigo de resgate nao encontrado"}

        row = rows[0]
        valido_ate = to_utc(row.get("valido_ate"))
        status = (row.get("status") or CODIGO_STATUS_ACTIVE).lower()
        if valido_ate and valido_ate < now_utc() and status == CODIGO_STATUS_ACTIVE:
            status = CODIGO_STATUS_EXPIRED

        return {
            "success": True,
            "codigo": row.get("codigo"),
            "status": status,
            "valido_ate": valido_ate.isoformat() if valido_ate else None,
            "utilizado_em": row.get("utilizado_em").isoformat() if row.get("utilizado_em") else None,
            "resgate_id": int(row["resgate_id"]),
            "premio": {
                "id": int(row["premio_id"]),
                "nome": row.get("premio_nome"),
                "categoria": row.get("premio_categoria"),
            },
            "pontos_usados": int(row.get("pontos_usados") or 0),
            "regras": {
                "pessoal_e_intransferivel": True,
                "uso_unico": True,
                "resgate_no_hotel": True,
            },
        }

    async def validar_codigo_resgate(self, codigo_resgate: str) -> Dict[str, Any]:
        codigo = self._normalizar_codigo(codigo_resgate)
        if not codigo:
            return {"success": False, "valido": False, "error": "Codigo de resgate obrigatorio"}

        async with self.db.tx() as transaction:
            rows = await transaction.query_raw(
                """
                SELECT cr.*, rp.cliente_id, rp.premio_id, p.nome AS premio_nome, p.categoria AS premio_categoria
                FROM codigos_resgate cr
                JOIN resgates_premios rp ON rp.id = cr.resgate_id
                JOIN premios p ON p.id = rp.premio_id
                WHERE cr.codigo = $1
                FOR UPDATE OF cr
                """,
                codigo,
            )
            if not rows:
                return {"success": False, "valido": False, "error": "Codigo de resgate nao encontrado"}

            row = rows[0]
            status_codigo = (row.get("status") or CODIGO_STATUS_ACTIVE).lower()
            valido_ate = to_utc(row.get("valido_ate"))

            if status_codigo != CODIGO_STATUS_ACTIVE:
                return {"success": True, "valido": False, "error": f"Codigo indisponivel: {status_codigo}"}

            if valido_ate and valido_ate < now_utc():
                await self._marcar_codigo_expirado(transaction, int(row["id"]), int(row["resgate_id"]))
                return {"success": True, "valido": False, "error": "Codigo expirado"}

            return {
                "success": True,
                "valido": True,
                "codigo": codigo,
                "resgate_id": int(row["resgate_id"]),
                "cliente_id": int(row["cliente_id"]),
                "premio": {
                    "id": int(row["premio_id"]),
                    "nome": row.get("premio_nome"),
                    "categoria": row.get("premio_categoria"),
                },
                "valido_ate": valido_ate.isoformat() if valido_ate else None,
            }

    async def usar_codigo_resgate(
        self,
        codigo_resgate: str,
        funcionario_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        codigo = self._normalizar_codigo(codigo_resgate)
        if not codigo:
            return {"success": False, "error": "Codigo de resgate obrigatorio"}

        async with self.db.tx() as transaction:
            rows = await transaction.query_raw(
                """
                SELECT cr.*, rp.cliente_id, rp.premio_id, p.nome AS premio_nome
                FROM codigos_resgate cr
                JOIN resgates_premios rp ON rp.id = cr.resgate_id
                JOIN premios p ON p.id = rp.premio_id
                WHERE cr.codigo = $1
                FOR UPDATE OF cr
                """,
                codigo,
            )
            if not rows:
                return {"success": False, "error": "Codigo de resgate nao encontrado"}

            codigo_data = rows[0]
            status_codigo = (codigo_data.get("status") or CODIGO_STATUS_ACTIVE).lower()
            if status_codigo != CODIGO_STATUS_ACTIVE:
                return {"success": False, "error": f"Codigo ja inutilizado: {status_codigo}"}

            expira_em = to_utc(codigo_data.get("valido_ate"))
            if expira_em and expira_em < now_utc():
                await self._marcar_codigo_expirado(
                    transaction,
                    int(codigo_data["id"]),
                    int(codigo_data["resgate_id"]),
                )
                return {"success": False, "error": "Codigo expirado"}

            usado_em = now_utc()
            await transaction.execute_raw(
                """
                UPDATE codigos_resgate
                SET status = $1,
                    utilizado_em = $2::timestamptz,
                    funcionario_id = $3,
                    updated_at = NOW()
                WHERE id = $4
                """,
                CODIGO_STATUS_USED,
                usado_em,
                funcionario_id,
                int(codigo_data["id"]),
            )
            await transaction.execute_raw(
                """
                UPDATE resgates_premios
                SET codigo_status = $1,
                    usado_em = $2::timestamp,
                    status = $3,
                    funcionario_entrega_id = $4,
                    updated_at = NOW()
                WHERE id = $5
                """,
                CODIGO_STATUS_USED,
                usado_em,
                RESGATE_STATUS_UTILIZADO,
                funcionario_id,
                int(codigo_data["resgate_id"]),
            )
            await transaction.execute_raw(
                """
                INSERT INTO logs_jornada (cliente_id, acao, payload, created_at)
                VALUES ($1, $2, CAST($3 AS JSONB), NOW())
                """,
                int(codigo_data["cliente_id"]),
                "codigo_resgate_utilizado",
                json.dumps({
                    "codigo": codigo,
                    "resgate_id": int(codigo_data["resgate_id"]),
                    "funcionario_id": funcionario_id,
                }),
            )

            return {
                "success": True,
                "resgate_id": int(codigo_data["resgate_id"]),
                "codigo": codigo,
                "codigo_resgate": codigo,
                "codigo_status": CODIGO_STATUS_USED,
                "status": RESGATE_STATUS_UTILIZADO,
                "usado_em": usado_em.isoformat(),
            }

    async def listar_resgates_cliente(self, cliente_id: int) -> List[Dict[str, Any]]:
        rows = await self.db.query_raw(
            """
            SELECT rp.id,
                   rp.premio_id,
                   p.nome AS premio_nome,
                   rp.pontos_usados,
                   rp.status,
                   COALESCE(cr.codigo, rp.codigo_resgate) AS codigo_resgate,
                   COALESCE(cr.status, rp.codigo_status) AS codigo_status,
                   COALESCE(cr.valido_ate, rp.expira_em) AS expira_em,
                   COALESCE(cr.utilizado_em, rp.usado_em) AS usado_em,
                   rp.created_at
            FROM resgates_premios rp
            JOIN premios p ON p.id = rp.premio_id
            LEFT JOIN LATERAL (
                SELECT *
                FROM codigos_resgate cr
                WHERE cr.resgate_id = rp.id
                ORDER BY
                    CASE WHEN cr.status = $2 THEN 0 ELSE 1 END,
                    cr.created_at DESC,
                    cr.id DESC
                LIMIT 1
            ) cr ON TRUE
            WHERE rp.cliente_id = $1
            ORDER BY rp.created_at DESC
            """,
            cliente_id,
            CODIGO_STATUS_ACTIVE,
        )

        return [
            {
                "id": int(row["id"]),
                "premio_id": int(row["premio_id"]),
                "premio_nome": row.get("premio_nome"),
                "pontos_usados": int(row.get("pontos_usados") or 0),
                "status": row.get("status"),
                "codigo_resgate": row.get("codigo_resgate"),
                "codigo_status": row.get("codigo_status"),
                "expira_em": row.get("expira_em").isoformat() if row.get("expira_em") else None,
                "usado_em": row.get("usado_em").isoformat() if row.get("usado_em") else None,
                "data_resgate": row.get("created_at").isoformat() if row.get("created_at") else None,
            }
            for row in rows
        ]

    async def confirmar_entrega(self, resgate_id: int, funcionario_id: int) -> Dict[str, Any]:
        rows = await self.db.query_raw(
            """
            SELECT COALESCE(cr.codigo, rp.codigo_resgate) AS codigo
            FROM resgates_premios rp
            LEFT JOIN LATERAL (
                SELECT *
                FROM codigos_resgate cr
                WHERE cr.resgate_id = rp.id
                ORDER BY
                    CASE WHEN cr.status = $2 THEN 0 ELSE 1 END,
                    cr.created_at DESC,
                    cr.id DESC
                LIMIT 1
            ) cr ON TRUE
            WHERE rp.id = $1
            LIMIT 1
            """,
            resgate_id,
            CODIGO_STATUS_ACTIVE,
        )
        if not rows:
            return {"success": False, "error": "Resgate nao encontrado"}

        codigo = rows[0].get("codigo")
        if codigo:
            return await self.usar_codigo_resgate(codigo, funcionario_id=funcionario_id)

        await self.db.resgatepremio.update(
            where={"id": resgate_id},
            data={
                "status": RESGATE_STATUS_UTILIZADO,
                "funcionarioEntregaId": funcionario_id,
                "codigoStatus": CODIGO_STATUS_USED,
                "usadoEm": now_utc(),
            },
        )
        return {"success": True, "message": "Entrega confirmada"}

    async def expirar_codigos_vencidos(self) -> Dict[str, Any]:
        agora = now_utc()
        async with self.db.tx() as transaction:
            expirados = await transaction.query_raw(
                """
                UPDATE codigos_resgate
                SET status = $1,
                    updated_at = NOW()
                WHERE status = $2
                  AND valido_ate < $3::timestamptz
                RETURNING id, resgate_id, codigo
                """,
                CODIGO_STATUS_EXPIRED,
                CODIGO_STATUS_ACTIVE,
                agora,
            )

            for row in expirados:
                resgate_id = int(row["resgate_id"])
                await transaction.execute_raw(
                    """
                    UPDATE resgates_premios
                    SET codigo_status = $1,
                        status = $1,
                        updated_at = NOW()
                    WHERE id = $2
                      AND codigo_resgate = $3
                    """,
                    CODIGO_STATUS_EXPIRED,
                    resgate_id,
                    row["codigo"],
                )

        return {
            "success": True,
            "codigos_expirados": len(expirados),
            "expirados": [
                {
                    "id": int(row["id"]),
                    "resgate_id": int(row["resgate_id"]),
                    "codigo": row["codigo"],
                }
                for row in expirados
            ],
        }

    async def renovar_codigo_resgate(
        self,
        resgate_id: int,
        funcionario_id: Optional[int] = None,
        dias_validade: int = 30,
    ) -> Dict[str, Any]:
        async with self.db.tx() as transaction:
            rows = await transaction.query_raw(
                """
                SELECT id, cliente_id, premio_id, status
                FROM resgates_premios
                WHERE id = $1
                FOR UPDATE
                """,
                resgate_id,
            )
            if not rows:
                return {"success": False, "error": "Resgate nao encontrado"}

            resgate = rows[0]
            status_resgate = (resgate.get("status") or "").lower()
            if status_resgate == RESGATE_STATUS_UTILIZADO:
                return {"success": False, "error": "Resgate ja utilizado nao pode ter codigo renovado"}

            cancelados = await transaction.query_raw(
                """
                UPDATE codigos_resgate
                SET status = $1,
                    updated_at = NOW()
                WHERE resgate_id = $2
                  AND status = $3
                RETURNING codigo
                """,
                CODIGO_STATUS_CANCELLED,
                resgate_id,
                CODIGO_STATUS_ACTIVE,
            )

            novo_codigo = await self._gerar_codigo_resgate(transaction)
            expira_em = now_utc() + timedelta(days=int(dias_validade or 30))
            codigo_row = await transaction.codigoresgate.create(
                data={
                    "resgateId": resgate_id,
                    "codigo": novo_codigo,
                    "status": CODIGO_STATUS_ACTIVE,
                    "validoAte": expira_em,
                    "funcionarioId": funcionario_id,
                }
            )
            await transaction.execute_raw(
                """
                UPDATE resgates_premios
                SET codigo_resgate = $1,
                    codigo_status = $2,
                    expira_em = $3::timestamptz,
                    status = $4,
                    updated_at = NOW()
                WHERE id = $5
                """,
                novo_codigo,
                CODIGO_STATUS_ACTIVE,
                expira_em,
                RESGATE_STATUS_AGUARDANDO_USO,
                resgate_id,
            )
            await transaction.execute_raw(
                """
                INSERT INTO logs_jornada (cliente_id, acao, payload, created_at)
                VALUES ($1, $2, CAST($3 AS JSONB), NOW())
                """,
                int(resgate["cliente_id"]),
                "codigo_resgate_renovado",
                json.dumps({
                    "resgate_id": resgate_id,
                    "codigo_novo": novo_codigo,
                    "codigos_cancelados": [row["codigo"] for row in cancelados],
                    "funcionario_id": funcionario_id,
                }),
            )

        return {
            "success": True,
            "resgate_id": resgate_id,
            "codigo": codigo_row.codigo,
            "codigo_resgate": codigo_row.codigo,
            "codigo_status": CODIGO_STATUS_ACTIVE,
            "valido_ate": expira_em.isoformat(),
            "expira_em": expira_em.isoformat(),
            "codigos_cancelados": [row["codigo"] for row in cancelados],
        }

    def _serialize(self, premio) -> Dict[str, Any]:
        return {
            "id": _row_get(premio, "id"),
            "nome": _row_get(premio, "nome"),
            "descricao": _row_get(premio, "descricao"),
            "preco_em_pontos": _row_get(premio, "precoEmPontos", _row_get(premio, "preco_em_pontos")),
            "preco_em_rp": _row_get(premio, "precoEmRp", _row_get(premio, "preco_em_rp")),
            "ativo": _row_get(premio, "ativo"),
            "categoria": _row_get(premio, "categoria", "GERAL"),
            "categoria_id": _row_get(premio, "categoriaId", _row_get(premio, "categoria_id")),
            "estoque": _row_get(premio, "estoque"),
            "imagem_url": _row_get(premio, "imagemUrl", _row_get(premio, "imagem_url")),
            "created_at": _row_get(premio, "createdAt").isoformat() if _row_get(premio, "createdAt") else None,
        }

    async def _buscar_resgate_por_idempotency_key(self, conn, idempotency_key: str) -> Optional[Dict[str, Any]]:
        """Busca um resgate ja criado com esta chave, para devolver como
        replay seguro (mesma logica de pagamento_repo.get_by_idempotency_key).
        """
        rows = await conn.query_raw(
            """
            SELECT rp.id AS resgate_id,
                   rp.status,
                   rp.pontos_usados,
                   p.id AS premio_id,
                   p.nome AS premio_nome,
                   p.categoria AS premio_categoria,
                   p.preco_em_pontos,
                   COALESCE(cr.codigo, rp.codigo_resgate) AS codigo,
                   COALESCE(cr.valido_ate, rp.expira_em) AS valido_ate
            FROM resgates_premios rp
            JOIN premios p ON p.id = rp.premio_id
            LEFT JOIN LATERAL (
                SELECT * FROM codigos_resgate cr
                WHERE cr.resgate_id = rp.id
                ORDER BY cr.created_at DESC, cr.id DESC
                LIMIT 1
            ) cr ON TRUE
            WHERE rp.idempotency_key = $1
            LIMIT 1
            """,
            idempotency_key,
        )
        if not rows:
            return None

        row = rows[0]
        valido_ate = to_utc(row.get("valido_ate"))
        return {
            "success": True,
            "idempotente": True,
            "resgate_id": int(row["resgate_id"]),
            "status": row.get("status"),
            "premio": {
                "id": int(row["premio_id"]),
                "nome": row.get("premio_nome"),
                "categoria": row.get("premio_categoria"),
                "preco_em_pontos": int(row.get("preco_em_pontos") or 0),
            },
            "pontos_usados": int(row.get("pontos_usados") or 0),
            "codigo": row.get("codigo"),
            "codigo_resgate": row.get("codigo"),
            "codigo_status": CODIGO_STATUS_ACTIVE,
            "valido_ate": valido_ate.isoformat() if valido_ate else None,
            "expira_em": valido_ate.isoformat() if valido_ate else None,
            "mensagem": "Resgate ja processado anteriormente (idempotencia).",
        }

    async def _gerar_codigo_resgate(self, transaction) -> str:
        for _tentativa in range(30):
            codigo = f"REAL-{secrets.randbelow(1_000_000):06d}"
            rows = await transaction.query_raw(
                """
                SELECT codigo FROM codigos_resgate WHERE codigo = $1
                UNION ALL
                SELECT codigo_resgate AS codigo FROM resgates_premios WHERE codigo_resgate = $1
                LIMIT 1
                """,
                codigo,
            )
            if not rows:
                return codigo
        raise ValueError("Nao foi possivel gerar codigo unico de resgate")

    def _normalizar_codigo(self, codigo_resgate: str) -> str:
        return (codigo_resgate or "").strip().upper()

    async def _marcar_codigo_expirado(self, transaction, codigo_id: int, resgate_id: int) -> None:
        await transaction.execute_raw(
            """
            UPDATE codigos_resgate
            SET status = $1, updated_at = NOW()
            WHERE id = $2
            """,
            CODIGO_STATUS_EXPIRED,
            codigo_id,
        )
        await transaction.execute_raw(
            """
            UPDATE resgates_premios
            SET codigo_status = $1,
                status = $1,
                updated_at = NOW()
            WHERE id = $2
              AND codigo_resgate = (
                  SELECT codigo
                  FROM codigos_resgate
                  WHERE id = $3
              )
            """,
            CODIGO_STATUS_EXPIRED,
            resgate_id,
            codigo_id,
        )
