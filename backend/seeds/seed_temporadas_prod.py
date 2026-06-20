#!/usr/bin/env python3
"""Seed de temporadas 2026 + cliente Andre Kaique para testes"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from seeds.bootstrap import bootstrap_seed_environment
bootstrap_seed_environment()

from app.core.database import get_db_connected, connect_db, disconnect_db, get_db
from app.schemas.cliente_schema import ClienteCreate
from app.repositories.cliente_repo import ClienteRepository


async def seed_temporadas(db):
    print("\n=== TEMPORADAS 2026 ===")
    # Estrutura real: suite_tipo, temporada, data_inicio, data_fim, preco_diaria, ativo
    await db.execute_raw("DELETE FROM tarifas_suites WHERE data_inicio >= '2026-01-01';")

    inserts = [
        ("LUXO",   "BAIXA", "2026-04-01", "2026-08-31", 290.0),
        ("MASTER", "BAIXA", "2026-04-01", "2026-08-31", 450.0),
        ("DUPLA",  "BAIXA", "2026-04-01", "2026-08-31", 580.0),
        ("REAL",   "BAIXA", "2026-04-01", "2026-08-31", 500.0),
        ("LUXO",   "MEDIA", "2026-09-01", "2026-10-31", 300.0),
        ("MASTER", "MEDIA", "2026-09-01", "2026-10-31", 450.0),
        ("DUPLA",  "MEDIA", "2026-09-01", "2026-10-31", 600.0),
        ("REAL",   "MEDIA", "2026-09-01", "2026-10-31", 550.0),
        ("LUXO",   "ALTA",  "2026-11-01", "2026-12-31", 350.0),
        ("MASTER", "ALTA",  "2026-11-01", "2026-12-31", 450.0),
        ("DUPLA",  "ALTA",  "2026-11-01", "2026-12-31", 700.0),
        ("REAL",   "ALTA",  "2026-11-01", "2026-12-31", 590.0),
        # Junho 2026 (mes atual) - BAIXA
        ("LUXO",   "BAIXA", "2026-06-01", "2026-07-31", 290.0),
        ("MASTER", "BAIXA", "2026-06-01", "2026-07-31", 450.0),
        ("DUPLA",  "BAIXA", "2026-06-01", "2026-07-31", 580.0),
        ("REAL",   "BAIXA", "2026-06-01", "2026-07-31", 500.0),
    ]

    from datetime import datetime as dt
    for tipo, temp, inicio, fim, preco in inserts:
        # Prisma Python precisa de datetime para campos Date
        d_inicio = dt.fromisoformat(inicio + "T00:00:00")
        d_fim    = dt.fromisoformat(fim    + "T00:00:00")
        await db.tarifasuite.create(data={
            "suiteTipo":  tipo,
            "temporada":  temp,
            "dataInicio": d_inicio,
            "dataFim":    d_fim,
            "precoDiaria": preco,
            "ativo":       True,
        })
        print(f"  ✅ {tipo} {temp} ({inicio} → {fim}) R${preco:.0f}")

    count = await db.tarifasuite.count()
    print(f"\n📊 Total tarifas no banco: {count}")


async def seed_cliente_andre(db):
    print("\n=== CLIENTE ANDRE KAIQUE ===")
    repo = ClienteRepository(db)

    # Usando os primeiros 11 digitos do numero como documento de teste
    # (atualizar com CPF real quando disponivel)
    cpf = "11968029860"
    telefone = "119680298600"

    existente = await db.cliente.find_first(where={"documento": cpf})
    if existente:
        print(f"⚠️  Andre Kaique ja existe (ID: {existente.id}, documento: {cpf})")
        return existente.id

    cliente_data = ClienteCreate(
        nome_completo="Andre Kaique",
        documento=cpf,
        telefone=telefone,
        email=None
    )
    cliente = await repo.create(cliente_data)
    print(f"✅ Cliente criado!")
    print(f"   Nome:      Andre Kaique")
    print(f"   Documento: {cpf}  ← atualizar com CPF real se necessario")
    print(f"   Telefone:  {telefone}")
    print(f"   ID:        {cliente['id']}")
    return cliente['id']


async def main():
    await connect_db()
    db = get_db()

    await seed_temporadas(db)
    cliente_id = await seed_cliente_andre(db)

    print(f"\n✅ Tudo pronto! Cliente ID={cliente_id}")
    print("   Acesse http://localhost:3000 para testar reservas e pontos.")

    await disconnect_db()


if __name__ == "__main__":
    asyncio.run(main())
