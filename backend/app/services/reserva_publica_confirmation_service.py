"""Finaliza o fluxo de uma reserva criada pelo site.

Uma reserva do cliente pode ser confirmada antes da quitação. O pagamento
continua pendente e o voucher comprova a reserva, não a liquidação.
"""

from typing import Any, Dict

from app.repositories.pagamento_repo import PagamentoRepository
from app.schemas.pagamento_schema import PagamentoCreate
from app.services.voucher_service import gerar_voucher


class ReservaPublicaConfirmationService:
    """Mantém atômicos os efeitos obrigatórios da reserva pública."""

    STATUS_CONFIRMAVEIS = {"PENDENTE", "PENDENTE_PAGAMENTO", "AGUARDANDO_PAGAMENTO"}

    def __init__(self, db):
        self.db = db

    async def confirmar_com_pagamento_pendente(
        self,
        reserva_id: int,
        valor_total: float,
    ) -> Dict[str, Any]:
        """Confirma, registra pagamento pendente e emite voucher em uma transação.

        O valor é sempre calculado pelo backend (incluindo cupom aplicado) e
        nunca é recebido do cliente como fonte de verdade.
        """
        async with self.db.tx() as tx:
            reserva = await tx.reserva.find_unique(where={"id": reserva_id})
            if not reserva:
                raise ValueError("Reserva não encontrada")
            if reserva.statusReserva not in self.STATUS_CONFIRMAVEIS:
                raise ValueError(
                    "Reserva não pode ser confirmada no estado atual: "
                    f"{reserva.statusReserva}"
                )

            reserva_confirmada = await tx.reserva.update(
                where={"id": reserva_id},
                data={"statusReserva": "CONFIRMADA"},
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
            "reserva": reserva_confirmada,
            "pagamento": pagamento,
            "voucher": voucher,
        }
