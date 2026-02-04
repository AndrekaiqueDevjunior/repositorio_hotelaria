#!/usr/bin/env python3
"""
Demonstração completa do fluxo de reservas → check-in → check-out.

Execute em um terminal:
    cd backend
    .\venv312\Scripts\Activate.ps1
    python demo_checkin_checkout.py
"""
import asyncio
from datetime import datetime, timedelta

from app.core.database import connect_db, disconnect_db, get_db
from app.repositories.cliente_repo import ClienteRepository
from app.repositories.quarto_repo import QuartoRepository
from app.repositories.reserva_repo import ReservaRepository
from app.schemas.cliente_schema import ClienteCreate
from app.schemas.quarto_schema import QuartoCreate, TipoSuite, StatusQuarto
from app.schemas.reserva_schema import ReservaCreate


async def run_demo():
    await connect_db()
    db = get_db()

    cliente_repo = ClienteRepository(db)
    quarto_repo = QuartoRepository(db)
    reserva_repo = ReservaRepository(db)

    print("=" * 72)
    print("🏨 Demo de Check-in e Check-out")
    print("=" * 72)

    # 1. Garantir cliente e quarto reais
    cliente = await cliente_repo.create(
        ClienteCreate(
            nome_completo="João Pedro da Silva",
            documento="12345678909",
            telefone="21988887777",
            email="joao.silva@example.com",
        )
    ) if not (await db.cliente.find_unique(where={"documento": "12345678909"})) else await cliente_repo.get_by_documento("12345678909")

    quarto = await quarto_repo.create(
        QuartoCreate(
            numero="501",
            tipo_suite=TipoSuite.MASTER,
            status=StatusQuarto.LIVRE,
        )
    ) if not (await db.quarto.find_unique(where={"numero": "501"})) else await quarto_repo.get_by_numero("501")

    print(f"👤 Cliente: {cliente['nome_completo']} (CPF {cliente['documento']})")
    print(f"🛏️  Quarto: {quarto['numero']} ({quarto['tipo_suite']})")

    # 2. Criar reserva realista
    checkin_previsto = datetime.now().replace(hour=15, minute=0, second=0, microsecond=0) + timedelta(days=1)
    checkout_previsto = checkin_previsto + timedelta(days=3)

    reserva = await reserva_repo.create(
        ReservaCreate(
            cliente_id=cliente["id"],
            quarto_numero=quarto["numero"],
            tipo_suite=TipoSuite.MASTER,
            checkin_previsto=checkin_previsto,
            checkout_previsto=checkout_previsto,
            valor_diaria=320.0,
            num_diarias=3,
        )
    )
    print(f"\n📘 Reserva criada: {reserva['codigo_reserva']} - status {reserva['status']}")

    # 3. Simular chegada do hóspede
    reserva = await reserva_repo.checkin(reserva["id"])
    print(f"✅ Check-in efetuado em {reserva['checkin_realizado']} - status {reserva['status']}")

    # 4. Simular saída
    reserva = await reserva_repo.checkout(reserva["id"])
    print(f"🏁 Check-out efetuado em {reserva['checkout_realizado']} - status {reserva['status']}")
    print(f"💰 Valor total: R$ {reserva['valor_total']:.2f}")

    await disconnect_db()
    print("\n🚀 Pronto! Verifique a tela de reservas/pagamentos para ver os dados inseridos.")


if __name__ == "__main__":
    asyncio.run(run_demo())

