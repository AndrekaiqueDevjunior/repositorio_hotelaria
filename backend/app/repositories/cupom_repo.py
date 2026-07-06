from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional, Tuple

from prisma import Client

from app.utils.datetime_utils import now_utc, to_utc


RESERVA_STATUS_PERMITE_CUPOM = {"PENDENTE"}
STATUS_PAGAMENTO_BLOQUEIA_CUPOM = {
    "PAGO",
    "APROVADO",
    "CONFIRMADO",
    "CAPTURED",
    "AUTHORIZED",
}
TIPOS_DESCONTO_VALIDOS = {"PERCENTUAL", "FIXO"}
CASAS_MONETARIAS = Decimal("0.01")
CUPOM_STATUS_ACTIVE = "active"
CUPOM_STATUS_EXPIRED = "expired"
CUPOM_STATUS_CANCELLED = "cancelled"
CUPOM_STATUS_MAX_USAGE = "max_usage_reached"


class CupomRepository:
    def __init__(self, db: Client):
        self.db = db

    async def list_all(self, apenas_ativos: bool = False) -> List[Dict[str, Any]]:
        where = {"ativo": True, "status": CUPOM_STATUS_ACTIVE} if apenas_ativos else {}
        cupons = await self.db.cupom.find_many(where=where, order={"createdAt": "desc"})
        return [self._serialize_cupom(cupom) for cupom in cupons]

    async def get_by_id(self, cupom_id: int) -> Optional[Dict[str, Any]]:
        cupom = await self.db.cupom.find_unique(where={"id": cupom_id})
        if not cupom:
            return None
        return self._serialize_cupom(cupom)

    async def get_by_codigo(self, codigo: str) -> Optional[Dict[str, Any]]:
        cupom = await self.db.cupom.find_unique(where={"codigo": self._normalizar_codigo(codigo)})
        if not cupom:
            return None
        return self._serialize_cupom(cupom)

    async def get_amigo_by_cliente(self, cliente_id: int) -> Optional[Dict[str, Any]]:
        cupom = await self.db.cupom.find_first(
            where={"clienteIndicadorId": cliente_id, "tipoCampanha": "CUPOM_AMIGO"},
            order={"createdAt": "desc"},
        )
        if not cupom:
            return None
        return self._serialize_cupom(cupom)

    async def create(self, data: Dict[str, Any], criado_por: Optional[int] = None) -> Dict[str, Any]:
        codigo = self._normalizar_codigo(data["codigo"])
        tipo = self._normalizar_tipo_desconto(data["tipo_desconto"])
        suites_permitidas = self._normalizar_suites(data.get("suites_permitidas"))

        cupom = await self.db.cupom.create(
            data={
                "codigo": codigo,
                "descricao": data.get("descricao"),
                "tipoDesconto": tipo,
                "valorDesconto": self._to_decimal(data["valor_desconto"]),
                "pontosBonus": data.get("pontos_bonus") or 0,
                "minDiarias": data.get("min_diarias"),
                "suitesPermitidas": suites_permitidas,
                "dataInicio": data["data_inicio"],
                "dataFim": data["data_fim"],
                "limiteTotalUsos": data.get("limite_total_usos"),
                "limitePorCliente": data.get("limite_por_cliente"),
                "ativo": data.get("ativo", True),
                "status": data.get("status") or (CUPOM_STATUS_ACTIVE if data.get("ativo", True) else CUPOM_STATUS_CANCELLED),
                "trackingSlug": data.get("tracking_slug"),
                "criadoPor": criado_por,
                "tipoCampanha": data.get("tipo_campanha"),
                "influencerNome": data.get("influencer_nome"),
                "commissionPercentual": self._to_decimal(data["commission_percentual"])
                if data.get("commission_percentual") is not None
                else None,
                "clienteIndicadorId": data.get("cliente_indicador_id"),
            }
        )
        return self._serialize_cupom(cupom)

    async def update(self, cupom_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        existente = await self.db.cupom.find_unique(where={"id": cupom_id})
        if not existente:
            return None

        update_data: Dict[str, Any] = {}
        if "descricao" in data:
            update_data["descricao"] = data.get("descricao")
        if "tipo_desconto" in data and data.get("tipo_desconto") is not None:
            update_data["tipoDesconto"] = self._normalizar_tipo_desconto(data["tipo_desconto"])
        if "valor_desconto" in data and data.get("valor_desconto") is not None:
            update_data["valorDesconto"] = self._to_decimal(data["valor_desconto"])
        if "pontos_bonus" in data:
            update_data["pontosBonus"] = data.get("pontos_bonus") or 0
        if "min_diarias" in data:
            update_data["minDiarias"] = data.get("min_diarias")
        if "suites_permitidas" in data:
            update_data["suitesPermitidas"] = self._normalizar_suites(data.get("suites_permitidas"))
        if "data_inicio" in data and data.get("data_inicio") is not None:
            update_data["dataInicio"] = data["data_inicio"]
        if "data_fim" in data and data.get("data_fim") is not None:
            update_data["dataFim"] = data["data_fim"]
        if "limite_total_usos" in data:
            update_data["limiteTotalUsos"] = data.get("limite_total_usos")
        if "limite_por_cliente" in data:
            update_data["limitePorCliente"] = data.get("limite_por_cliente")
        if "ativo" in data and data.get("ativo") is not None:
            update_data["ativo"] = data["ativo"]
            update_data["status"] = CUPOM_STATUS_ACTIVE if data["ativo"] else CUPOM_STATUS_CANCELLED
        if "status" in data and data.get("status") is not None:
            update_data["status"] = data.get("status")
        if "tracking_slug" in data:
            update_data["trackingSlug"] = data.get("tracking_slug")
        if "tipo_campanha" in data:
            update_data["tipoCampanha"] = data.get("tipo_campanha")
        if "influencer_nome" in data:
            update_data["influencerNome"] = data.get("influencer_nome")
        if "commission_percentual" in data:
            update_data["commissionPercentual"] = (
                self._to_decimal(data["commission_percentual"])
                if data.get("commission_percentual") is not None
                else None
            )
        if "cliente_indicador_id" in data:
            update_data["clienteIndicadorId"] = data.get("cliente_indicador_id")

        if not update_data:
            return self._serialize_cupom(existente)

        cupom = await self.db.cupom.update(where={"id": cupom_id}, data=update_data)
        return self._serialize_cupom(cupom)

    async def set_ativo(self, cupom_id: int, ativo: bool) -> Optional[Dict[str, Any]]:
        existente = await self.db.cupom.find_unique(where={"id": cupom_id})
        if not existente:
            return None
        cupom = await self.db.cupom.update(
            where={"id": cupom_id},
            data={"ativo": ativo, "status": CUPOM_STATUS_ACTIVE if ativo else CUPOM_STATUS_CANCELLED},
        )
        return self._serialize_cupom(cupom)

    async def list_admin(
        self,
        status: Optional[str] = None,
        tipo_campanha: Optional[str] = None,
        apenas_influencer: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        conditions: List[str] = []
        params: List[Any] = []

        if status:
            params.append(status.strip().lower())
            conditions.append(f"LOWER(c.status) = ${len(params)}")
        if tipo_campanha:
            params.append(tipo_campanha.strip().upper())
            conditions.append(f"UPPER(COALESCE(c.tipo_campanha, '')) = ${len(params)}")
        if apenas_influencer:
            conditions.append(
                "(UPPER(COALESCE(c.tipo_campanha, '')) = 'INFLUENCER' "
                "OR c.influencer_nome IS NOT NULL "
                "OR c.commission_percentual IS NOT NULL)"
            )

        limit = max(1, min(int(limit or 50), 200))
        offset = max(0, int(offset or 0))
        params.extend([limit, offset])
        limit_param = len(params) - 1
        offset_param = len(params)
        where_sql = " AND ".join(conditions) if conditions else "TRUE"

        rows = await self.db.query_raw(
            f"""
            SELECT
                c.*,
                COUNT(cu.id)::int AS usos_registrados,
                COUNT(DISTINCT cu.cliente_id)::int AS clientes_unicos,
                COALESCE(SUM(cu.valor_original), 0)::numeric AS valor_original_total,
                COALESCE(SUM(cu.valor_desconto), 0)::numeric AS valor_desconto_total,
                COALESCE(SUM(cu.valor_final), 0)::numeric AS valor_final_total
            FROM cupons c
            LEFT JOIN cupons_usos cu ON cu.cupom_id = c.id
            WHERE {where_sql}
            GROUP BY c.id
            ORDER BY c.created_at DESC
            LIMIT ${limit_param} OFFSET ${offset_param}
            """,
            *params,
        )
        return [self._serialize_cupom_admin_row(row) for row in rows]

    async def get_admin_by_codigo(
        self,
        codigo: str,
        include_usages: bool = True,
        usage_limit: int = 25,
    ) -> Optional[Dict[str, Any]]:
        rows = await self.db.query_raw(
            """
            SELECT
                c.*,
                COUNT(cu.id)::int AS usos_registrados,
                COUNT(DISTINCT cu.cliente_id)::int AS clientes_unicos,
                COALESCE(SUM(cu.valor_original), 0)::numeric AS valor_original_total,
                COALESCE(SUM(cu.valor_desconto), 0)::numeric AS valor_desconto_total,
                COALESCE(SUM(cu.valor_final), 0)::numeric AS valor_final_total
            FROM cupons c
            LEFT JOIN cupons_usos cu ON cu.cupom_id = c.id
            WHERE c.codigo = $1
            GROUP BY c.id
            LIMIT 1
            """,
            self._normalizar_codigo(codigo),
        )
        if not rows:
            return None

        cupom = self._serialize_cupom_admin_row(rows[0])
        if not include_usages:
            return cupom

        limite = max(1, min(int(usage_limit or 25), 100))
        usos = await self.db.query_raw(
            """
            SELECT
                cu.id,
                cu.reserva_id,
                cu.cliente_id,
                cu.valor_original,
                cu.valor_desconto,
                cu.valor_final,
                cu.created_at,
                r.codigo_reserva,
                c.nome_completo AS cliente_nome,
                c.documento AS cliente_documento
            FROM cupons_usos cu
            LEFT JOIN reservas r ON r.id = cu.reserva_id
            LEFT JOIN clientes c ON c.id = cu.cliente_id
            WHERE cu.cupom_id = $1
            ORDER BY cu.created_at DESC
            LIMIT $2
            """,
            int(cupom["id"]),
            limite,
        )
        cupom["usages"] = [self._serialize_cupom_uso_admin_row(row) for row in usos]
        return cupom

    async def delete(self, cupom_id: int) -> bool:
        existente = await self.db.cupom.find_unique(where={"id": cupom_id})
        if not existente:
            return False
        await self.db.cupom.update(
            where={"id": cupom_id},
            data={"ativo": False, "status": CUPOM_STATUS_CANCELLED},
        )
        return True

    async def validar_cupom(
        self,
        codigo: str,
        cliente_id: Optional[int] = None,
        suite_tipo: Optional[str] = None,
        num_diarias: Optional[int] = None,
        valor_total_base: Optional[Any] = None,
        reserva_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        reserva_contexto = None
        if reserva_id:
            reserva_contexto = await self._obter_contexto_reserva(reserva_id)
            cliente_id = reserva_contexto["cliente_id"]
            suite_tipo = reserva_contexto["tipo_suite"]
            num_diarias = reserva_contexto["num_diarias"]
            valor_total_base = reserva_contexto["valor_total_base"]

        cupom = await self.db.cupom.find_unique(where={"codigo": self._normalizar_codigo(codigo)})
        if not cupom:
            return {"valido": False, "mensagem": "Cupom não encontrado"}

        contexto = {
            "reserva_id": reserva_id,
            "cliente_id": cliente_id,
            "suite_tipo": (suite_tipo or "").strip().upper() or None,
            "num_diarias": num_diarias,
            "valor_total_base": self._to_decimal(valor_total_base) if valor_total_base is not None else None,
        }
        valido, mensagem = await self._validar_regras_cupom(cupom, contexto)
        if not valido:
            return {
                "valido": False,
                "mensagem": mensagem,
                "codigo": cupom.codigo,
                "status": getattr(cupom, "status", CUPOM_STATUS_ACTIVE),
                "tipo_desconto": cupom.tipoDesconto,
                "valor_desconto": float(cupom.valorDesconto),
                "pontos_bonus": int(cupom.pontosBonus or 0),
            }

        valor_desconto_calculado = None
        valor_final_estimado = None
        if contexto["valor_total_base"] is not None:
            valor_desconto_calculado, valor_final_estimado = self._calcular_desconto(
                cupom.tipoDesconto,
                cupom.valorDesconto,
                contexto["valor_total_base"],
            )

        return {
            "valido": True,
            "mensagem": "Cupom válido",
            "codigo": cupom.codigo,
            "status": getattr(cupom, "status", CUPOM_STATUS_ACTIVE),
            "tipo_desconto": cupom.tipoDesconto,
            "valor_desconto": float(cupom.valorDesconto),
            "valor_desconto_calculado": float(valor_desconto_calculado) if valor_desconto_calculado is not None else None,
            "valor_final_estimado": float(valor_final_estimado) if valor_final_estimado is not None else None,
            "pontos_bonus": int(cupom.pontosBonus or 0),
        }

    async def aplicar_cupom_reserva(self, reserva_id: int, codigo: str) -> Dict[str, Any]:
        codigo_norm = self._normalizar_codigo(codigo)

        async with self.db.tx() as transaction:
            reserva_contexto = await self._obter_contexto_reserva(reserva_id, transaction, lock=True)
            await self._validar_contexto_aplicacao_reserva(transaction, reserva_contexto)

            uso_existente = await transaction.cupomuso.find_first(where={"reservaId": reserva_id})
            if uso_existente:
                raise ValueError("A reserva já possui um cupom aplicado")

            cupom_row = await transaction.query_raw(
                """
                SELECT *
                FROM cupons
                WHERE codigo = $1
                FOR UPDATE
                """,
                codigo_norm,
            )
            if not cupom_row:
                raise ValueError("Cupom não encontrado")

            cupom_data = cupom_row[0]
            contexto = {
                "reserva_id": reserva_contexto["id"],
                "cliente_id": reserva_contexto["cliente_id"],
                "suite_tipo": reserva_contexto["tipo_suite"],
                "num_diarias": reserva_contexto["num_diarias"],
                "valor_total_base": reserva_contexto["valor_total_base"],
            }
            valido, mensagem = await self._validar_regras_cupom_row(cupom_data, contexto, transaction)
            if not valido:
                raise ValueError(mensagem)

            valor_desconto, valor_final = self._calcular_desconto(
                cupom_data["tipo_desconto"],
                cupom_data["valor_desconto"],
                reserva_contexto["valor_total_base"],
            )

            valor_original = self._to_decimal(reserva_contexto["valor_total_base"])

            uso = await transaction.cupomuso.create(
                data={
                    "cupomId": int(cupom_data["id"]),
                    "reservaId": reserva_id,
                    "clienteId": reserva_contexto["cliente_id"],
                    "valorOriginal": valor_original,
                    "valorDesconto": valor_desconto,
                    "valorFinal": valor_final,
                }
            )

            cupom = await transaction.cupom.update(
                where={"id": int(cupom_data["id"])},
                data=self._montar_update_uso_cupom(cupom_data),
            )

        return self._serialize_cupom_uso(
            uso,
            cupom_codigo=cupom.codigo,
            pontos_bonus=int(cupom.pontosBonus or 0),
            tipo_campanha=getattr(cupom, "tipoCampanha", None),
            cliente_indicador_id=getattr(cupom, "clienteIndicadorId", None),
        )

    async def remover_cupom_reserva(self, reserva_id: int) -> Dict[str, Any]:
        async with self.db.tx() as transaction:
            reserva_contexto = await self._obter_contexto_reserva(reserva_id, transaction, lock=True)
            await self._validar_contexto_aplicacao_reserva(transaction, reserva_contexto)

            uso = await transaction.cupomuso.find_first(
                where={"reservaId": reserva_id},
                include={"cupom": True},
            )
            if not uso:
                raise ValueError("A reserva não possui cupom aplicado")

            await transaction.cupomuso.delete(where={"id": uso.id})

            if uso.cupomId:
                cupom_data = await transaction.cupom.find_unique(where={"id": uso.cupomId})
                if cupom_data and int(cupom_data.totalUsos or 0) > 0:
                    novo_total = int(cupom_data.totalUsos or 0) - 1
                    update_data: Dict[str, Any] = {"totalUsos": {"decrement": 1}}
                    limite = getattr(cupom_data, "limiteTotalUsos", None)
                    if (
                        getattr(cupom_data, "status", None) == CUPOM_STATUS_MAX_USAGE
                        and limite is not None
                        and novo_total < int(limite)
                    ):
                        update_data["ativo"] = True
                        update_data["status"] = CUPOM_STATUS_ACTIVE
                    await transaction.cupom.update(
                        where={"id": uso.cupomId},
                        data=update_data,
                    )

        return self._serialize_cupom_uso(
            uso,
            cupom_codigo=getattr(getattr(uso, "cupom", None), "codigo", None),
            pontos_bonus=int(getattr(getattr(uso, "cupom", None), "pontosBonus", 0) or 0),
        )

    async def obter_cupom_reserva(self, reserva_id: int) -> Optional[Dict[str, Any]]:
        uso = await self.db.cupomuso.find_first(
            where={"reservaId": reserva_id},
            include={"cupom": True},
        )
        if not uso:
            return None
        return self._serialize_cupom_uso(
            uso,
            cupom_codigo=getattr(getattr(uso, "cupom", None), "codigo", None),
            pontos_bonus=int(getattr(getattr(uso, "cupom", None), "pontosBonus", 0) or 0),
        )

    async def processar_invalidacoes_automaticas(self) -> Dict[str, Any]:
        agora = now_utc()
        expirados = await self.db.query_raw(
            """
            UPDATE cupons
            SET ativo = FALSE,
                status = $1,
                updated_at = NOW()
            WHERE status = $2
              AND ativo = TRUE
              AND data_fim < $3::timestamptz
            RETURNING id, codigo
            """,
            CUPOM_STATUS_EXPIRED,
            CUPOM_STATUS_ACTIVE,
            agora,
        )
        esgotados = await self.db.query_raw(
            """
            UPDATE cupons
            SET ativo = FALSE,
                status = $1,
                updated_at = NOW()
            WHERE status = $2
              AND ativo = TRUE
              AND limite_total_usos IS NOT NULL
              AND total_usos >= limite_total_usos
            RETURNING id, codigo
            """,
            CUPOM_STATUS_MAX_USAGE,
            CUPOM_STATUS_ACTIVE,
        )
        return {
            "success": True,
            "cupons_expirados": len(expirados),
            "cupons_esgotados": len(esgotados),
            "expirados": [{"id": int(row["id"]), "codigo": row["codigo"]} for row in expirados],
            "esgotados": [{"id": int(row["id"]), "codigo": row["codigo"]} for row in esgotados],
        }

    async def _obter_contexto_reserva(
        self,
        reserva_id: int,
        db: Optional[Client] = None,
        lock: bool = False,
    ) -> Dict[str, Any]:
        executor = db or self.db
        if lock:
            rows = await executor.query_raw(
                """
                SELECT id, cliente_id, status_reserva, tipo_suite, num_diarias, valor_diaria
                FROM reservas
                WHERE id = $1
                FOR UPDATE
                """,
                reserva_id,
            )
            if not rows:
                raise ValueError("Reserva não encontrada")
            reserva = rows[0]
            valor_diaria = self._to_decimal(reserva["valor_diaria"])
            num_diarias = int(reserva["num_diarias"] or 0)
            return {
                "id": int(reserva["id"]),
                "cliente_id": int(reserva["cliente_id"]),
                "status_reserva": reserva["status_reserva"],
                "tipo_suite": (reserva["tipo_suite"] or "").strip().upper(),
                "num_diarias": num_diarias,
                "valor_total_base": (valor_diaria * Decimal(num_diarias)).quantize(CASAS_MONETARIAS, rounding=ROUND_HALF_UP),
            }

        reserva = await executor.reserva.find_unique(where={"id": reserva_id})
        if not reserva:
            raise ValueError("Reserva não encontrada")

        valor_diaria = self._to_decimal(getattr(reserva, "valorDiaria", 0))
        num_diarias = int(getattr(reserva, "numDiarias", 0) or 0)
        return {
            "id": int(reserva.id),
            "cliente_id": int(reserva.clienteId),
            "status_reserva": reserva.statusReserva,
            "tipo_suite": (reserva.tipoSuite or "").strip().upper(),
            "num_diarias": num_diarias,
            "valor_total_base": (valor_diaria * Decimal(num_diarias)).quantize(CASAS_MONETARIAS, rounding=ROUND_HALF_UP),
        }

    async def _validar_contexto_aplicacao_reserva(self, db: Client, reserva_contexto: Dict[str, Any]) -> None:
        status_reserva = (reserva_contexto["status_reserva"] or "").strip().upper()
        if status_reserva not in RESERVA_STATUS_PERMITE_CUPOM:
            raise ValueError("Cupom só pode ser aplicado em reservas pendentes")

        pagamentos = await db.pagamento.find_many(where={"reservaId": reserva_contexto["id"]})
        for pagamento in pagamentos:
            status_pagamento = (getattr(pagamento, "statusPagamento", None) or "").strip().upper()
            if status_pagamento in STATUS_PAGAMENTO_BLOQUEIA_CUPOM:
                raise ValueError("Não é possível alterar cupom após pagamento aprovado")

    async def _validar_regras_cupom(
        self,
        cupom,
        contexto: Dict[str, Any],
        db: Optional[Client] = None,
    ) -> Tuple[bool, str]:
        return await self._validar_regras_cupom_row(
            {
                "id": cupom.id,
                "codigo": cupom.codigo,
                "ativo": cupom.ativo,
                "status": getattr(cupom, "status", CUPOM_STATUS_ACTIVE),
                "tracking_slug": getattr(cupom, "trackingSlug", None),
                "tipo_desconto": cupom.tipoDesconto,
                "valor_desconto": cupom.valorDesconto,
                "pontos_bonus": cupom.pontosBonus,
                "min_diarias": cupom.minDiarias,
                "suites_permitidas": cupom.suitesPermitidas,
                "data_inicio": cupom.dataInicio,
                "data_fim": cupom.dataFim,
                "limite_total_usos": cupom.limiteTotalUsos,
                "limite_por_cliente": cupom.limitePorCliente,
                "total_usos": cupom.totalUsos,
                "tipo_campanha": getattr(cupom, "tipoCampanha", None),
                "cliente_indicador_id": getattr(cupom, "clienteIndicadorId", None),
            },
            contexto,
            db or self.db,
        )

    async def _validar_regras_cupom_row(
        self,
        cupom_data: Dict[str, Any],
        contexto: Dict[str, Any],
        db: Client,
    ) -> Tuple[bool, str]:
        status = (cupom_data.get("status") or CUPOM_STATUS_ACTIVE).strip().lower()
        if status != CUPOM_STATUS_ACTIVE:
            status_msg = {
                CUPOM_STATUS_EXPIRED: "Cupom expirado",
                CUPOM_STATUS_CANCELLED: "Cupom cancelado",
                CUPOM_STATUS_MAX_USAGE: "Cupom esgotado",
            }.get(status, "Cupom inativo")
            return False, status_msg

        if not bool(cupom_data.get("ativo")):
            return False, "Cupom inativo"

        tipo_desconto = self._normalizar_tipo_desconto(cupom_data.get("tipo_desconto"))
        if tipo_desconto not in TIPOS_DESCONTO_VALIDOS:
            return False, "Cupom com tipo de desconto inválido"

        agora = now_utc()
        data_inicio = to_utc(cupom_data.get("data_inicio"))
        data_fim = to_utc(cupom_data.get("data_fim"))
        if not data_inicio or not data_fim:
            return False, "Cupom fora da validade"
        if agora < data_inicio:
            return False, "Cupom ainda nao esta vigente"
        if agora > data_fim:
            await self._marcar_cupom_expirado_se_possivel(db, cupom_data)
            return False, "Cupom fora da validade"

        limite_total_usos = cupom_data.get("limite_total_usos")
        total_usos = int(cupom_data.get("total_usos") or 0)
        if limite_total_usos is not None and total_usos >= int(limite_total_usos):
            await self._marcar_cupom_esgotado_se_possivel(db, cupom_data)
            return False, "Cupom esgotado"

        min_diarias = cupom_data.get("min_diarias")
        num_diarias = int(contexto.get("num_diarias") or 0)
        if min_diarias is not None and num_diarias < int(min_diarias):
            return False, f"Cupom exige no mínimo {int(min_diarias)} diária(s)"

        suites_permitidas = self._parse_suites_permitidas(cupom_data.get("suites_permitidas"))
        suite_tipo = (contexto.get("suite_tipo") or "").strip().upper()
        if suites_permitidas and suite_tipo and suite_tipo not in suites_permitidas:
            return False, "Cupom não é válido para esta suíte"

        limite_por_cliente = cupom_data.get("limite_por_cliente")
        cliente_id = contexto.get("cliente_id")
        if limite_por_cliente is not None and cliente_id:
            usos_cliente = await db.cupomuso.count(
                where={"cupomId": int(cupom_data["id"]), "clienteId": int(cliente_id)}
            )
            if usos_cliente >= int(limite_por_cliente):
                return False, "Cliente já atingiu o limite de uso deste cupom"

        tipo_campanha = (cupom_data.get("tipo_campanha") or "").strip().upper()
        cliente_indicador_id = cupom_data.get("cliente_indicador_id")
        if tipo_campanha == "CUPOM_AMIGO" and cliente_indicador_id and cliente_id:
            if int(cliente_indicador_id) == int(cliente_id):
                return False, "Autoindicacao nao permitida para cupom amigo"

            indicado_rows = await db.query_raw(
                """
                SELECT regexp_replace(documento, '\\D', '', 'g') AS cpf
                FROM clientes
                WHERE id = $1
                LIMIT 1
                """,
                int(cliente_id),
            )
            cpf_indicado = indicado_rows[0]["cpf"] if indicado_rows else None
            if cpf_indicado:
                indicacao_rows = await db.query_raw(
                    """
                    SELECT cliente_indicador_id, reserva_id, pontos_creditados
                    FROM indicacoes
                    WHERE cpf_indicado = $1
                    LIMIT 1
                    """,
                    cpf_indicado,
                )
                if indicacao_rows:
                    indicacao_existente = indicacao_rows[0]
                    reserva_existente_id = indicacao_existente.get("reserva_id")
                    reserva_contexto_id = contexto.get("reserva_id")
                    if int(indicacao_existente["cliente_indicador_id"]) != int(cliente_indicador_id):
                        return False, "CPF indicado ja usado em outra indicacao"
                    if bool(indicacao_existente.get("pontos_creditados")):
                        return False, "CPF indicado ja usado em indicacao creditada"
                    if reserva_existente_id and (
                        not reserva_contexto_id or int(reserva_existente_id) != int(reserva_contexto_id)
                    ):
                        return False, "CPF indicado ja usado em outra reserva"

        valor_total_base = contexto.get("valor_total_base")
        if valor_total_base is not None and self._to_decimal(valor_total_base) <= Decimal("0"):
            return False, "Valor base inválido para cálculo do cupom"

        return True, "Cupom válido"

    def _montar_update_uso_cupom(self, cupom_data: Dict[str, Any]) -> Dict[str, Any]:
        limite_total_usos = cupom_data.get("limite_total_usos")
        total_atual = int(cupom_data.get("total_usos") or 0)
        data: Dict[str, Any] = {"totalUsos": {"increment": 1}}
        if limite_total_usos is not None and total_atual + 1 >= int(limite_total_usos):
            data["ativo"] = False
            data["status"] = CUPOM_STATUS_MAX_USAGE
        return data

    async def _marcar_cupom_expirado_se_possivel(self, db: Client, cupom_data: Dict[str, Any]) -> None:
        try:
            await db.cupom.update(
                where={"id": int(cupom_data["id"])},
                data={"ativo": False, "status": CUPOM_STATUS_EXPIRED},
            )
        except Exception:
            pass

    async def _marcar_cupom_esgotado_se_possivel(self, db: Client, cupom_data: Dict[str, Any]) -> None:
        try:
            await db.cupom.update(
                where={"id": int(cupom_data["id"])},
                data={"ativo": False, "status": CUPOM_STATUS_MAX_USAGE},
            )
        except Exception:
            pass

    def _parse_suites_permitidas(self, raw_value: Optional[str]) -> List[str]:
        if not raw_value:
            return []

        raw_value = raw_value.strip()
        if not raw_value:
            return []

        if raw_value.startswith("["):
            try:
                data = json.loads(raw_value)
                if isinstance(data, list):
                    return [(item or "").strip().upper() for item in data if (item or "").strip()]
            except Exception:
                pass

        return [(item or "").strip().upper() for item in raw_value.split(",") if (item or "").strip()]

    def _normalizar_suites(self, suites: Optional[List[str]]) -> Optional[str]:
        if not suites:
            return None
        normalizadas = []
        for item in suites:
            suite = (item or "").strip().upper()
            if suite:
                normalizadas.append(suite)
        return ",".join(dict.fromkeys(normalizadas)) if normalizadas else None

    def _calcular_desconto(
        self,
        tipo_desconto: Any,
        valor_desconto: Any,
        valor_total_base: Any,
    ) -> Tuple[Decimal, Decimal]:
        valor_base_decimal = self._to_decimal(valor_total_base)
        valor_desconto_decimal = self._to_decimal(valor_desconto)
        tipo = self._normalizar_tipo_desconto(tipo_desconto)

        if tipo == "PERCENTUAL":
            desconto = (valor_base_decimal * valor_desconto_decimal / Decimal("100")).quantize(
                CASAS_MONETARIAS,
                rounding=ROUND_HALF_UP,
            )
        else:
            desconto = valor_desconto_decimal

        if desconto > valor_base_decimal:
            desconto = valor_base_decimal

        valor_final = (valor_base_decimal - desconto).quantize(CASAS_MONETARIAS, rounding=ROUND_HALF_UP)
        return desconto, valor_final

    def _normalizar_codigo(self, codigo: str) -> str:
        return (codigo or "").strip().upper()

    def _normalizar_tipo_desconto(self, tipo: Any) -> str:
        return (str(tipo or "")).strip().upper()

    def _to_decimal(self, value: Any) -> Decimal:
        if isinstance(value, Decimal):
            return value.quantize(CASAS_MONETARIAS, rounding=ROUND_HALF_UP)
        return Decimal(str(value)).quantize(CASAS_MONETARIAS, rounding=ROUND_HALF_UP)

    def _serialize_cupom(self, cupom) -> Dict[str, Any]:
        suites_permitidas = self._parse_suites_permitidas(getattr(cupom, "suitesPermitidas", None))
        return {
            "id": cupom.id,
            "codigo": cupom.codigo,
            "descricao": cupom.descricao,
            "tipo_desconto": cupom.tipoDesconto,
            "valor_desconto": float(cupom.valorDesconto),
            "pontos_bonus": int(cupom.pontosBonus or 0),
            "min_diarias": cupom.minDiarias,
            "suites_permitidas": suites_permitidas or None,
            "data_inicio": cupom.dataInicio.isoformat() if cupom.dataInicio else None,
            "data_fim": cupom.dataFim.isoformat() if cupom.dataFim else None,
            "limite_total_usos": cupom.limiteTotalUsos,
            "limite_por_cliente": cupom.limitePorCliente,
            "total_usos": int(cupom.totalUsos or 0),
            "ativo": bool(cupom.ativo),
            "status": getattr(cupom, "status", CUPOM_STATUS_ACTIVE),
            "tracking_slug": getattr(cupom, "trackingSlug", None),
            "criado_por": cupom.criadoPor,
            "tipo_campanha": getattr(cupom, "tipoCampanha", None),
            "influencer_nome": getattr(cupom, "influencerNome", None),
            "commission_percentual": (
                float(getattr(cupom, "commissionPercentual"))
                if getattr(cupom, "commissionPercentual", None) is not None
                else None
            ),
            "cliente_indicador_id": getattr(cupom, "clienteIndicadorId", None),
            "created_at": cupom.createdAt.isoformat() if cupom.createdAt else None,
            "updated_at": cupom.updatedAt.isoformat() if cupom.updatedAt else None,
        }

    def _serialize_cupom_admin_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        stats = {
            "usage_count": int(row.get("usos_registrados") or 0),
            "unique_customers": int(row.get("clientes_unicos") or 0),
            "gross_amount": float(self._to_decimal(row.get("valor_original_total") or 0)),
            "discount_amount": float(self._to_decimal(row.get("valor_desconto_total") or 0)),
            "net_amount": float(self._to_decimal(row.get("valor_final_total") or 0)),
        }
        commission_percentual = row.get("commission_percentual")
        commission_rate = self._to_decimal(commission_percentual) if commission_percentual is not None else Decimal("0.00")
        commission_base = self._to_decimal(row.get("valor_final_total") or 0)
        estimated_commission = (commission_base * commission_rate / Decimal("100")).quantize(
            CASAS_MONETARIAS,
            rounding=ROUND_HALF_UP,
        )
        stats["commission_base"] = float(commission_base)
        stats["estimated_commission"] = float(estimated_commission)

        data_inicio = row.get("data_inicio")
        data_fim = row.get("data_fim")
        created_at = row.get("created_at")
        updated_at = row.get("updated_at")
        return {
            "id": int(row["id"]),
            "codigo": row["codigo"],
            "descricao": row.get("descricao"),
            "tipo_desconto": row.get("tipo_desconto"),
            "valor_desconto": float(self._to_decimal(row.get("valor_desconto") or 0)),
            "pontos_bonus": int(row.get("pontos_bonus") or 0),
            "min_diarias": row.get("min_diarias"),
            "suites_permitidas": self._parse_suites_permitidas(row.get("suites_permitidas")) or None,
            "data_inicio": data_inicio.isoformat() if hasattr(data_inicio, "isoformat") else data_inicio,
            "data_fim": data_fim.isoformat() if hasattr(data_fim, "isoformat") else data_fim,
            "limite_total_usos": row.get("limite_total_usos"),
            "limite_por_cliente": row.get("limite_por_cliente"),
            "total_usos": int(row.get("total_usos") or 0),
            "ativo": bool(row.get("ativo")),
            "status": row.get("status") or CUPOM_STATUS_ACTIVE,
            "tracking_slug": row.get("tracking_slug"),
            "criado_por": row.get("criado_por"),
            "tipo_campanha": row.get("tipo_campanha"),
            "influencer_nome": row.get("influencer_nome"),
            "commission_percentual": (
                float(self._to_decimal(row.get("commission_percentual")))
                if row.get("commission_percentual") is not None
                else None
            ),
            "cliente_indicador_id": row.get("cliente_indicador_id"),
            "created_at": created_at.isoformat() if hasattr(created_at, "isoformat") else created_at,
            "updated_at": updated_at.isoformat() if hasattr(updated_at, "isoformat") else updated_at,
            "stats": stats,
        }

    def _serialize_cupom_uso_admin_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        created_at = row.get("created_at")
        return {
            "id": int(row["id"]),
            "reservation_id": row.get("reserva_id"),
            "reservation_code": row.get("codigo_reserva"),
            "customer_id": row.get("cliente_id"),
            "customer_name": row.get("cliente_nome"),
            "customer_document": row.get("cliente_documento"),
            "gross_amount": float(self._to_decimal(row.get("valor_original") or 0)),
            "discount_amount": float(self._to_decimal(row.get("valor_desconto") or 0)),
            "net_amount": float(self._to_decimal(row.get("valor_final") or 0)),
            "created_at": created_at.isoformat() if hasattr(created_at, "isoformat") else created_at,
        }

    def _serialize_cupom_uso(
        self,
        uso,
        cupom_codigo: Optional[str] = None,
        pontos_bonus: int = 0,
        tipo_campanha: Optional[str] = None,
        cliente_indicador_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        cupom = getattr(uso, "cupom", None)
        return {
            "id": uso.id,
            "cupom_id": uso.cupomId,
            "codigo": cupom_codigo,
            "valor_original": float(uso.valorOriginal),
            "valor_desconto": float(uso.valorDesconto),
            "valor_final": float(uso.valorFinal),
            "pontos_bonus": int(pontos_bonus or 0),
            "tipo_campanha": tipo_campanha or getattr(cupom, "tipoCampanha", None),
            "cliente_indicador_id": cliente_indicador_id or getattr(cupom, "clienteIndicadorId", None),
            "status": getattr(cupom, "status", None),
            "created_at": uso.createdAt.isoformat() if uso.createdAt else None,
        }
