from typing import Any, Dict, List

from app.services.notification_service import NotificationService
from app.utils.datetime_utils import now_utc


class CheckoutAlertService:
    def __init__(self, db):
        self.db = db

    async def listar_pendentes(self, limit: int = 20) -> Dict[str, Any]:
        limite = max(1, min(int(limit or 20), 100))
        rows = await self.db.query_raw(
            """
            SELECT
                r.id,
                r.codigo_reserva,
                r.cliente_nome,
                r.quarto_numero,
                r.checkout_previsto,
                r.status_reserva,
                h.status_hospedagem,
                n.id AS notificacao_id
            FROM reservas r
            LEFT JOIN hospedagens h ON h.reserva_id = r.id
            LEFT JOIN notificacoes n
              ON n.reserva_id = r.id
             AND n.categoria = 'checkout_pendente'
             AND n.lida = FALSE
            WHERE r.checkout_previsto <= $1::timestamptz
              AND r.checkout_real IS NULL
              AND COALESCE(h.status_hospedagem, r.status_reserva) IN (
                'CHECKIN_REALIZADO',
                'HOSPEDADO',
                'CHECKIN',
                'EM_ANDAMENTO'
              )
              AND NOT EXISTS (
                SELECT 1
                FROM notificacoes nx
                WHERE nx.reserva_id = r.id
                  AND nx.categoria = 'checkout_pendente'
                  AND nx.lida = TRUE
              )
            ORDER BY r.checkout_previsto ASC
            LIMIT $2
            """,
            now_utc(),
            limite,
        )

        alerts: List[Dict[str, Any]] = []
        for row in rows:
            notificacao_id = row.get("notificacao_id")
            if not notificacao_id:
                notificacao = await NotificationService.notificar_checkout_pendente(self.db, row)
                notificacao_id = notificacao.get("id") if notificacao else None
            checkout_at = row.get("checkout_previsto")
            checkout_iso = checkout_at.isoformat() if hasattr(checkout_at, "isoformat") else checkout_at
            alerts.append({
                "notification_id": int(notificacao_id) if notificacao_id else None,
                "reservation_id": int(row["id"]),
                "codigo_reserva": row.get("codigo_reserva"),
                "room": row.get("quarto_numero"),
                "room_number": row.get("quarto_numero"),
                "guest_name": row.get("cliente_nome"),
                "checkout_at": checkout_iso,
                "checkout_previsto": checkout_iso,
                "viewed": False,
                "alert_sound": True,
                "alert_visual": True,
                "message": f"CHECKOUT - Quarto {row.get('quarto_numero')}",
            })

        return {"success": True, "alerts": alerts, "total": len(alerts)}

    async def marcar_visto(self, reservation_id: int) -> Dict[str, Any]:
        rows = await self.db.query_raw(
            """
            UPDATE notificacoes
            SET lida = TRUE
            WHERE reserva_id = $1
              AND categoria = 'checkout_pendente'
              AND lida = FALSE
            RETURNING id
            """,
            int(reservation_id),
        )
        return {
            "success": True,
            "reservation_id": int(reservation_id),
            "viewed": True,
            "notifications_marked": len(rows),
        }

