import asyncio
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.core.database import connect_db, disconnect_db, get_db


async def main():
    await connect_db()
    db = get_db()

    try:
        cliente_id = 13
        reserva_ids = [28, 29]

        cliente = await db.cliente.find_unique(where={"id": cliente_id})
        print("CLIENTE", getattr(cliente, "id", None), getattr(cliente, "nomeCompleto", None), getattr(cliente, "documento", None), getattr(cliente, "email", None))

        reservas = await db.reserva.find_many(where={"id": {"in": reserva_ids}})
        reservas = sorted(reservas, key=lambda r: r.id)
        print("RESERVAS", len(reservas))
        for r in reservas:
            print(
                " -",
                r.id,
                "clienteId",
                getattr(r, "clienteId", None),
                "codigo",
                getattr(r, "codigoReserva", None),
                "suite",
                getattr(r, "tipoSuite", None),
                "diarias",
                getattr(r, "numDiarias", None),
                "status",
                getattr(r, "statusReserva", None),
                "checkoutReal",
                getattr(r, "checkoutReal", None),
            )

        trans = await db.transacaopontos.find_many(
            where={"clienteId": cliente_id, "origem": "CHECKOUT"},
            order={"id": "asc"},
        )
        print("TRANSACOES_CHECKOUT", len(trans))
        for t in trans:
            print(
                " -",
                t.id,
                "reservaId",
                getattr(t, "reservaId", None),
                "tipo",
                getattr(t, "tipo", None),
                "origem",
                getattr(t, "origem", None),
                "pontos",
                getattr(t, "pontos", None),
                "saldoAnterior",
                getattr(t, "saldoAnterior", None),
                "saldoPosterior",
                getattr(t, "saldoPosterior", None),
                "createdAt",
                getattr(t, "createdAt", None),
            )

        saldo = await db.usuariopontos.find_first(where={"clienteId": cliente_id})
        print("USUARIOS_PONTOS", getattr(saldo, "id", None), "clienteId", getattr(saldo, "clienteId", None), "saldo", getattr(saldo, "saldo", None))

    finally:
        await disconnect_db()


if __name__ == "__main__":
    asyncio.run(main())
