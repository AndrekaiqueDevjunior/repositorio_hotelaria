"""Registra os efeitos iniciais de uma reserva ainda nao paga.

A reserva e o pagamento permanecem pendentes. O voucher identifica a reserva,
mas nunca promove seu status; somente a aprovacao financeira pode confirma-la.
"""

from typing import Any, Dict

from app.repositories.pagamento_repo import PagamentoRepository
from app.schemas.pagamento_schema import PagamentoCreate
from app.services.voucher_service import gerar_voucher


class ReservaPublicaConfirmationService:
    """Mantem atomicos os efeitos obrigatorios da criacao da reserva."""

    STATUS_PENDENTES = {"PENDENTE", "PENDENTE_PAGAMENTO", "AGUARDANDO_PAGAMENTO"}

    def __init__(self, db):
        self.db = db

    async def registrar_pagamento_pendente_e_voucher(
        self,
        reserva_id: int,
        valor_total: float,
    ) -> Dict[str, Any]:
        """Registra cobranca pendente e voucher sem confirmar a reserva.

        O valor e sempre calculado pelo backend (incluindo cupom aplicado) e
        nunca e recebido do cliente como fonte de verdade.
        """
        async with self.db.tx() as tx:
            reserva = await tx.reserva.find_unique(where={"id": reserva_id})
            if not reserva:
                raise ValueError("Reserva nao encontrada")
            if reserva.statusReserva not in self.STATUS_PENDENTES:
                raise ValueError(
                    "Reserva nao pode iniciar o pagamento no estado atual: "
                    f"{reserva.statusReserva}"
                )

            hospedagem = await tx.hospedagem.find_unique(where={"reservaId": reserva_id})
            if not hospedagem:
                await tx.hospedagem.create(
                    data={"reservaId": reserva_id, "statusHospedagem": "NAO_INICIADA"}
                )

            pagamento = await PagamentoRepository(tx).create(
                PagamentoCreate(
                    reserva_id=reserva_id,
                    valor=valor_total,
                    metodo="tef",
                ),
                idempotency_key=f"reserva-publica-pendente:{reserva_id}",
                status_inicial="PENDENTE",
            )
            voucher = await gerar_voucher(reserva_id, db=tx)

        return {
            "reserva": reserva,
            "pagamento": pagamento,
            "voucher": voucher,
        }
