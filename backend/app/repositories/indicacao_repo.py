from typing import Any, Dict, List, Optional


STATUS_ENVIADO = "enviado"
STATUS_RESERVADO = "reservado"
STATUS_HOSPEDADO = "hospedado"
STATUS_CREDITADO = "creditado"


def normalizar_documento(documento: str | None) -> str:
    return "".join(filter(str.isdigit, documento or ""))


class IndicacaoRepository:
    def __init__(self, db: Any):
        self.db = db

    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        rows = await self.db.query_raw(
            """
            INSERT INTO indicacoes (
                cliente_indicador_id,
                cliente_indicado_id,
                reserva_id,
                cpf_indicador,
                cpf_indicado,
                status,
                data_envio,
                data_reserva,
                pontos_creditados
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING *
            """,
            data["clienteIndicadorId"],
            data.get("clienteIndicadoId"),
            data.get("reservaId"),
            data["cpfIndicador"],
            data["cpfIndicado"],
            data.get("status", STATUS_ENVIADO),
            data.get("dataEnvio"),
            data.get("dataReserva"),
            bool(data.get("pontosCreditados", False)),
        )
        return self._serialize(rows[0])

    async def get_by_id(self, indicacao_id: int) -> Optional[Dict[str, Any]]:
        rows = await self.db.query_raw("SELECT * FROM indicacoes WHERE id = $1 LIMIT 1", indicacao_id)
        return self._serialize(rows[0]) if rows else None

    async def get_by_cpf_indicado(self, cpf_indicado: str) -> Optional[Dict[str, Any]]:
        rows = await self.db.query_raw(
            "SELECT * FROM indicacoes WHERE cpf_indicado = $1 LIMIT 1",
            normalizar_documento(cpf_indicado),
        )
        return self._serialize(rows[0]) if rows else None

    async def get_by_reserva_id(self, reserva_id: int) -> Optional[Dict[str, Any]]:
        rows = await self.db.query_raw("SELECT * FROM indicacoes WHERE reserva_id = $1 LIMIT 1", reserva_id)
        return self._serialize(rows[0]) if rows else None

    async def list_by_indicador(self, cliente_indicador_id: int) -> List[Dict[str, Any]]:
        indicacoes = await self.db.query_raw(
            """
            SELECT *
            FROM indicacoes
            WHERE cliente_indicador_id = $1
            ORDER BY created_at DESC
            """,
            cliente_indicador_id,
        )
        return [self._serialize(i) for i in indicacoes]

    async def vincular_reserva(self, indicacao_id: int, cliente_indicado_id: int, reserva_id: int, data_reserva) -> Dict[str, Any]:
        rows = await self.db.query_raw(
            """
            UPDATE indicacoes
            SET cliente_indicado_id = $1,
                reserva_id = $2,
                data_reserva = $3,
                status = $4,
                updated_at = now()
            WHERE id = $5
            RETURNING *
            """,
            cliente_indicado_id,
            reserva_id,
            data_reserva,
            STATUS_RESERVADO,
            indicacao_id,
        )
        return self._serialize(rows[0])

    async def marcar_checkin(self, indicacao_id: int, data_checkin) -> Dict[str, Any]:
        rows = await self.db.query_raw(
            """
            UPDATE indicacoes
            SET data_checkin = $1,
                status = $2,
                updated_at = now()
            WHERE id = $3
            RETURNING *
            """,
            data_checkin,
            STATUS_HOSPEDADO,
            indicacao_id,
        )
        return self._serialize(rows[0])

    async def listar_pendentes_com_checkout(self, limit: int = 100) -> List[Dict[str, Any]]:
        rows = await self.db.query_raw(
            """
            SELECT i.id, i.reserva_id
            FROM indicacoes i
            JOIN reservas r ON r.id = i.reserva_id
            LEFT JOIN hospedagens h ON h.reserva_id = r.id
            WHERE i.pontos_creditados = false
              AND i.reserva_id IS NOT NULL
              AND (r.checkout_real IS NOT NULL OR h.checkout_realizado_em IS NOT NULL)
            ORDER BY i.id ASC
            LIMIT $1
            """,
            limit,
        )
        return [{"id": int(r["id"]), "reserva_id": int(r["reserva_id"])} for r in rows]

    def _serialize(self, indicacao) -> Dict[str, Any]:
        if isinstance(indicacao, dict):
            return {
                "id": int(indicacao["id"]),
                "cliente_indicador_id": int(indicacao["cliente_indicador_id"]),
                "cliente_indicado_id": indicacao.get("cliente_indicado_id"),
                "reserva_id": indicacao.get("reserva_id"),
                "transacao_pontos_id": indicacao.get("transacao_pontos_id"),
                "cpf_indicador": indicacao["cpf_indicador"],
                "cpf_indicado": indicacao["cpf_indicado"],
                "status": indicacao["status"],
                "data_envio": indicacao.get("data_envio"),
                "data_reserva": indicacao.get("data_reserva"),
                "data_checkin": indicacao.get("data_checkin"),
                "data_checkout": indicacao.get("data_checkout"),
                "pontos_creditados": bool(indicacao.get("pontos_creditados", False)),
            }

        return {
            "id": indicacao.id,
            "cliente_indicador_id": indicacao.clienteIndicadorId,
            "cliente_indicado_id": getattr(indicacao, "clienteIndicadoId", None),
            "reserva_id": getattr(indicacao, "reservaId", None),
            "transacao_pontos_id": getattr(indicacao, "transacaoPontosId", None),
            "cpf_indicador": indicacao.cpfIndicador,
            "cpf_indicado": indicacao.cpfIndicado,
            "status": indicacao.status,
            "data_envio": getattr(indicacao, "dataEnvio", None),
            "data_reserva": getattr(indicacao, "dataReserva", None),
            "data_checkin": getattr(indicacao, "dataCheckin", None),
            "data_checkout": getattr(indicacao, "dataCheckout", None),
            "pontos_creditados": bool(getattr(indicacao, "pontosCreditados", False)),
        }
