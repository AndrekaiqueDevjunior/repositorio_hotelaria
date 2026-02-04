#!/usr/bin/env python3
"""
Popular o banco Prisma com dados de demonstração para testar o dia a dia.

Uso:
    cd backend
    .\\venv312\\Scripts\\Activate.ps1  # Windows
    python seed_demo_data.py
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any

from app.core.database import connect_db, disconnect_db, get_db
from app.repositories.cliente_repo import ClienteRepository
from app.repositories.quarto_repo import QuartoRepository
from app.repositories.reserva_repo import ReservaRepository
from app.repositories.funcionario_repo import FuncionarioRepository
from app.repositories.pagamento_repo import PagamentoRepository
from app.schemas.cliente_schema import ClienteCreate
from app.schemas.quarto_schema import QuartoCreate, TipoSuite, StatusQuarto
from app.schemas.reserva_schema import ReservaCreate
from app.schemas.funcionario_schema import FuncionarioCreate
from app.schemas.pagamento_schema import PagamentoCreate


DEMO_CLIENTES = [
    {
        "nome_completo": "Ana Souza",
        "documento": "11122233344",
        "telefone": "21999998888",
        "email": "ana.souza@example.com",
    },
    {
        "nome_completo": "Bruno Lima",
        "documento": "55566677788",
        "telefone": "21988887777",
        "email": "bruno.lima@example.com",
    },
    {
        "nome_completo": "Carla Mendes",
        "documento": "99900011122",
        "telefone": "21977776666",
        "email": "carla.mendes@example.com",
    },
]


DEMO_QUARTOS = [
    {"numero": "101", "tipo_suite": TipoSuite.DUPLA, "status": StatusQuarto.LIVRE},
    {"numero": "102", "tipo_suite": TipoSuite.LUXO, "status": StatusQuarto.LIVRE},
    {"numero": "501", "tipo_suite": TipoSuite.REAL, "status": StatusQuarto.LIVRE},
]


DEMO_FUNCIONARIOS = [
    {
        "nome": "Administrador",
        "email": "admin@hotelreal.com.br",
        "perfil": "ADMIN",
        "status": "ATIVO",
        "senha": "admin123",
    },
    {
        "nome": "Fernanda Recepção",
        "email": "recepcao@hotelreal.com.br",
        "perfil": "RECEPCAO",
        "status": "ATIVO",
        "senha": "recepcao123",
    },
]


DEMO_RESERVAS = [
    {
        "cliente_documento": "11122233344",
        "quarto_numero": "101",
        "tipo_suite": TipoSuite.DUPLA,
        "checkin_offset": 1,
        "num_diarias": 3,
        "valor_diaria": 180.0,
        "cenario": "pendente",
    },
    {
        "cliente_documento": "55566677788",
        "quarto_numero": "102",
        "tipo_suite": TipoSuite.LUXO,
        "checkin_offset": 0,
        "num_diarias": 4,
        "valor_diaria": 250.0,
        "cenario": "hospedado",
    },
    {
        "cliente_documento": "99900011122",
        "quarto_numero": "501",
        "tipo_suite": TipoSuite.REAL,
        "checkin_offset": -5,
        "num_diarias": 2,
        "valor_diaria": 320.0,
        "cenario": "finalizada",
    },
]


async def ensure_cliente(repo: ClienteRepository, data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        cliente = await repo.create(ClienteCreate(**data))
        cliente["created_now"] = True
        return cliente
    except ValueError:
        cliente = await repo.get_by_documento(data["documento"])
        cliente["created_now"] = False
        return cliente


async def ensure_quarto(repo: QuartoRepository, data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        quarto = await repo.create(
            QuartoCreate(numero=data["numero"], tipo_suite=data["tipo_suite"], status=data["status"])
        )
        quarto["created_now"] = True
        return quarto
    except ValueError:
        quarto = await repo.get_by_numero(data["numero"])
        quarto["created_now"] = False
        return quarto


async def ensure_funcionario(repo: FuncionarioRepository, data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        funcionario = await repo.create(FuncionarioCreate(**data))
        funcionario["created_now"] = True
        return funcionario
    except ValueError:
        funcionario = await repo.get_by_email(data["email"])
        funcionario["created_now"] = False
        return funcionario


def build_datetime(offset_days: int) -> datetime:
    base = datetime.now().replace(hour=15, minute=0, second=0, microsecond=0)
    return base + timedelta(days=offset_days)


async def seed():
    await connect_db()
    db = get_db()

    cliente_repo = ClienteRepository(db)
    quarto_repo = QuartoRepository(db)
    reserva_repo = ReservaRepository(db)
    funcionario_repo = FuncionarioRepository(db)
    pagamento_repo = PagamentoRepository(db)

    print("=" * 70)
    print("🌱 Populando banco com dados de demonstração")
    print("=" * 70)

    clientes = {}
    for data in DEMO_CLIENTES:
        cliente = await ensure_cliente(cliente_repo, data)
        clientes[data["documento"]] = cliente
        status = "criado" if cliente.get("created_now") else "já existia"
        print(f"👤 Cliente {cliente['nome_completo']} ({data['documento']}) - {status}")

    quartos = {}
    for data in DEMO_QUARTOS:
        quarto = await ensure_quarto(quarto_repo, data)
        quartos[data["numero"]] = quarto
        status = "criado" if quarto.get("created_now") else "já existia"
        print(f"🛏️  Quarto {quarto['numero']} ({quarto['tipo_suite']}) - {status}")

    funcionarios = {}
    for data in DEMO_FUNCIONARIOS:
        funcionario = await ensure_funcionario(funcionario_repo, data)
        funcionarios[data["email"]] = funcionario
        status = "criado" if funcionario.get("created_now") else "já existia"
        print(f"👔 Funcionário {funcionario['nome']} ({funcionario['perfil']}) - {status}")

    created_reservas = []
    for data in DEMO_RESERVAS:
        cliente = clientes[data["cliente_documento"]]
        checkin = build_datetime(data["checkin_offset"])
        checkout = checkin + timedelta(days=data["num_diarias"])

        reserva_payload = ReservaCreate(
            cliente_id=cliente["id"],
            quarto_numero=data["quarto_numero"],
            tipo_suite=data["tipo_suite"],
            checkin_previsto=checkin,
            checkout_previsto=checkout,
            valor_diaria=data["valor_diaria"],
            num_diarias=data["num_diarias"],
        )

        try:
            reserva = await reserva_repo.create(reserva_payload)
            print(
                f"📘 Reserva {reserva['codigo_reserva']} criada para {cliente['nome_completo']} no quarto {data['quarto_numero']}"
            )
        except ValueError as exc:
            print(f"⚠️  Não foi possível criar reserva para {cliente['nome_completo']}: {exc}")
            continue

        cenario = data["cenario"]
        if cenario == "hospedado":
            reserva = await reserva_repo.checkin(reserva["id"])
            print(f"   ➜ Check-in realizado (status: {reserva['status']})")
        elif cenario == "finalizada":
            reserva = await reserva_repo.checkin(reserva["id"])
            reserva = await reserva_repo.checkout(reserva["id"])
            print(f"   ➜ Reserva finalizada (status: {reserva['status']})")

            pagamento = await pagamento_repo.create(
                PagamentoCreate(
                    reserva_id=reserva["id"],
                    valor=reserva["valor_total"],
                    metodo="credit_card",
                    parcelas=1,
                    cartao_numero="4111111111111111",
                    cartao_validade="12/28",
                    cartao_cvv="123",
                    cartao_nome=cliente["nome_completo"],
                )
            )
            await pagamento_repo.update_status(pagamento["id"], "APROVADO", cielo_payment_id=f"CIELO-{reserva['id']}")
            print(f"   💳 Pagamento registrado (R$ {pagamento['valor']:.2f})")

        created_reservas.append(reserva)

    print("\nResumo:")
    print(f" - Clientes: {len(clientes)}")
    print(f" - Quartos: {len(quartos)}")
    print(f" - Funcionários: {len(funcionarios)}")
    print(f" - Reservas criadas: {len(created_reservas)}")
    print(f" - Pagamentos simulados: 1 (para reserva finalizada)")

    await disconnect_db()
    print("\n✅ Pronto! Abra o dashboard para visualizar os dados de exemplo.")


if __name__ == "__main__":
    asyncio.run(seed())

