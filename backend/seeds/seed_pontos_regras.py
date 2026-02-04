"""Script para popular o banco de dados com regras oficiais de Real Points (RP).

- Idempotente: cria ou atualiza as regras do período.
- Usado pelo pontos_checkout_service (tabela pontos_regras / model pontosregra).

Regras oficiais:
- Base: a cada 2 diárias (diarias_base=2)
- LUXO: 3 RP
- DUPLA: 4 RP
- MASTER: 4 RP
- REAL: 5 RP

Vigência padrão: hoje -> +365 dias
"""

import asyncio
from datetime import date, datetime, timedelta, timezone

from app.core.database import connect_db, disconnect_db, get_db


def _date_to_db_datetime(d: date) -> datetime:
    return datetime(d.year, d.month, d.day, tzinfo=timezone.utc)


REGRAS = [
    {"suiteTipo": "LUXO", "diariasBase": 2, "rpPorBase": 3, "temporada": "OFICIAL"},
    {"suiteTipo": "DUPLA", "diariasBase": 2, "rpPorBase": 4, "temporada": "OFICIAL"},
    {"suiteTipo": "MASTER", "diariasBase": 2, "rpPorBase": 4, "temporada": "OFICIAL"},
    {"suiteTipo": "REAL", "diariasBase": 2, "rpPorBase": 5, "temporada": "OFICIAL"},
]


async def seed_pontos_regras() -> None:
    await connect_db()
    db = get_db()

    data_inicio = date.today()
    data_fim = data_inicio + timedelta(days=365)
    data_inicio_dt = _date_to_db_datetime(data_inicio)
    data_fim_dt = _date_to_db_datetime(data_fim)

    print("\n=== SEED REGRAS REAL POINTS (RP) ===\n")

    for r in REGRAS:
        suite = r["suiteTipo"]
        diarias_base = r["diariasBase"]
        rp_por_base = r["rpPorBase"]
        temporada = r.get("temporada")

        try:
            existente = await db.pontosregra.find_first(
                where={
                    "suiteTipo": suite,
                    "ativo": True,
                    "dataInicio": {"lte": data_fim_dt},
                    "dataFim": {"gte": data_inicio_dt},
                },
                order={"dataInicio": "desc"},
            )

            payload = {
                "suiteTipo": suite,
                "diariasBase": diarias_base,
                "rpPorBase": rp_por_base,
                "temporada": temporada,
                "dataInicio": data_inicio_dt,
                "dataFim": data_fim_dt,
                "ativo": True,
            }

            if existente:
                await db.pontosregra.update(where={"id": existente.id}, data=payload)
                print(f"🔁 Regra {suite} atualizada (id={existente.id})")
            else:
                criado = await db.pontosregra.create(data=payload)
                print(f"✅ Regra {suite} criada (id={criado.id})")

        except Exception as e:
            print(f"❌ Erro ao criar/atualizar regra {suite}: {e}")

    total = await db.pontosregra.count()
    print(f"\n📊 Total de regras em pontos_regras: {total}\n")

    await disconnect_db()


if __name__ == "__main__":
    asyncio.run(seed_pontos_regras())
