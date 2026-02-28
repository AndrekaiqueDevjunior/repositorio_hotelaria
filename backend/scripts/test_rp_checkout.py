import asyncio
import os
import random
import string
import sys
from datetime import datetime, timedelta, timezone

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.core.database import connect_db, disconnect_db, get_db
from app.services.pontos_checkout_service import creditar_rp_no_checkout
from app.services.real_points_service import RealPointsService


def _rand_digits(n: int) -> str:
    return "".join(str(random.randint(0, 9)) for _ in range(n))


def _rand_token(n: int = 8) -> str:
    alphabet = string.ascii_lowercase + string.digits
    return "".join(random.choice(alphabet) for _ in range(n))


async def _criar_cliente(db):
    cpf = _rand_digits(11)
    token = _rand_token(10)

    cliente = await db.cliente.create(
        data={
            "nomeCompleto": f"TESTE RP {cpf}",
            "documento": cpf,
            "telefone": "21999999999",
            "email": f"teste.rp.{token}.{cpf}@example.com",
            "status": "ATIVO",
        }
    )

    return cliente


async def _criar_reserva(db, cliente, quarto_numero: str, tipo_suite: str, diarias: int):
    now = datetime.now(timezone.utc)

    checkin_previsto = now - timedelta(days=diarias + 1)
    checkout_previsto = now - timedelta(days=1)

    quarto = await db.quarto.find_unique(where={"numero": quarto_numero})
    if not quarto:
        raise RuntimeError(f"Quarto {quarto_numero} não encontrado")

    # Valor total não é usado no cálculo oficial no fallback (passa 0), mas o modelo exige valorDiaria.
    tarifa = await db.tarifasuite.find_first(
        where={
            "suiteTipo": tipo_suite,
            "ativo": True,
            "dataInicio": {"lte": now},
            "dataFim": {"gte": now},
        },
        order={"dataInicio": "desc"},
    )
    if not tarifa:
        raise RuntimeError(f"Sem tarifa ativa para {tipo_suite}")

    reserva = await db.reserva.create(
        data={
            "codigoReserva": f"RPTEST-{tipo_suite}-{_rand_digits(6)}",
            "clienteId": cliente.id,
            "clienteNome": cliente.nomeCompleto,
            "quartoId": quarto.id,
            "quartoNumero": quarto.numero,
            "tipoSuite": tipo_suite,
            "checkinPrevisto": checkin_previsto,
            "checkoutPrevisto": checkout_previsto,
            "valorDiaria": tarifa.precoDiaria,
            "numDiarias": diarias,
            "statusReserva": "CHECKED_OUT",
            "checkoutReal": now,
        }
    )

    return reserva


async def main():
    await connect_db()
    db = get_db()

    try:
        cliente = await _criar_cliente(db)
        print("CLIENTE", cliente.id, cliente.nomeCompleto, cliente.documento)

        # Cenário: 2 reservas, suítes diferentes, 2 diárias (bloco completo)
        reservas = [
            ("102", "LUXO", 2),
            ("101", "DUPLA", 2),
        ]

        total_creditado = 0

        for quarto_numero, tipo_suite, diarias in reservas:
            reserva = await _criar_reserva(db, cliente, quarto_numero, tipo_suite, diarias)

            esperado, detalhe = RealPointsService.calcular_rp_oficial(tipo_suite, diarias, 0)
            resultado = await creditar_rp_no_checkout(
                db,
                reserva_id=reserva.id,
                funcionario_id=1,
                checkout_datetime=getattr(reserva, "checkoutReal", None),
            )

            creditado = bool(resultado.get("creditado"))
            pontos = int(resultado.get("pontos") or 0)
            total_creditado += pontos if creditado else 0

            print(
                "RESERVA",
                reserva.id,
                "suite",
                tipo_suite,
                "diarias",
                diarias,
                "esperado",
                esperado,
                f"({detalhe})",
                "resultado",
                resultado,
            )

        trans = await db.transacaopontos.find_many(
            where={"clienteId": cliente.id, "origem": "CHECKOUT"},
            order={"createdAt": "asc"},
        )

        print("TRANSACOES_CHECKOUT", len(trans))
        for t in trans:
            print(
                " -",
                t.id,
                "reserva",
                t.reservaId,
                "pontos",
                t.pontos,
                "tipo",
                t.tipo,
                "origem",
                t.origem,
            )

        saldo = await db.usuariopontos.find_first(where={"clienteId": cliente.id})
        print("SALDO", saldo.saldo if saldo else None, "TOTAL_CREDITADO", total_creditado)

    finally:
        await disconnect_db()


if __name__ == "__main__":
    asyncio.run(main())
