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


class CupomRepository:
    def __init__(self, db: Client):
        self.db = db

    async def list_all(self, apenas_ativos: bool = False) -> List[Dict[str, Any]]:
        where = {"ativo": True} if apenas_ativos else {}
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
                "criadoPor": criado_por,
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

        if not update_data:
            return self._serialize_cupom(existente)

        cupom = await self.db.cupom.update(where={"id": cupom_id}, data=update_data)
        return self._serialize_cupom(cupom)

    async def set_ativo(self, cupom_id: int, ativo: bool) -> Optional[Dict[str, Any]]:
        existente = await self.db.cupom.find_unique(where={"id": cupom_id})
        if not existente:
            return None
        cupom = await self.db.cupom.update(where={"id": cupom_id}, data={"ativo": ativo})
        return self._serialize_cupom(cupom)

    async def delete(self, cupom_id: int) -> bool:
        existente = await self.db.cupom.find_unique(where={"id": cupom_id})
        if not existente:
            return False
        await self.db.cupom.update(where={"id": cupom_id}, data={"ativo": False})
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
                data={"totalUsos": {"increment": 1}},
            )

        return self._serialize_cupom_uso(uso, cupom_codigo=cupom.codigo, pontos_bonus=int(cupom.pontosBonus or 0))

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
                    await transaction.cupom.update(
                        where={"id": uso.cupomId},
                        data={"totalUsos": {"decrement": 1}},
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
        if not bool(cupom_data.get("ativo")):
            return False, "Cupom inativo"

        tipo_desconto = self._normalizar_tipo_desconto(cupom_data.get("tipo_desconto"))
        if tipo_desconto not in TIPOS_DESCONTO_VALIDOS:
            return False, "Cupom com tipo de desconto inválido"

        agora = now_utc()
        data_inicio = to_utc(cupom_data.get("data_inicio"))
        data_fim = to_utc(cupom_data.get("data_fim"))
        if not data_inicio or not data_fim or agora < data_inicio or agora > data_fim:
            return False, "Cupom fora da validade"

        limite_total_usos = cupom_data.get("limite_total_usos")
        total_usos = int(cupom_data.get("total_usos") or 0)
        if limite_total_usos is not None and total_usos >= int(limite_total_usos):
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

        valor_total_base = contexto.get("valor_total_base")
        if valor_total_base is not None and self._to_decimal(valor_total_base) <= Decimal("0"):
            return False, "Valor base inválido para cálculo do cupom"

        return True, "Cupom válido"

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
            "criado_por": cupom.criadoPor,
            "created_at": cupom.createdAt.isoformat() if cupom.createdAt else None,
            "updated_at": cupom.updatedAt.isoformat() if cupom.updatedAt else None,
        }

    def _serialize_cupom_uso(
        self,
        uso,
        cupom_codigo: Optional[str] = None,
        pontos_bonus: int = 0,
    ) -> Dict[str, Any]:
        return {
            "id": uso.id,
            "cupom_id": uso.cupomId,
            "codigo": cupom_codigo,
            "valor_original": float(uso.valorOriginal),
            "valor_desconto": float(uso.valorDesconto),
            "valor_final": float(uso.valorFinal),
            "pontos_bonus": int(pontos_bonus or 0),
            "created_at": uso.createdAt.isoformat() if uso.createdAt else None,
        }
