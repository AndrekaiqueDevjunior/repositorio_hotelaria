#!/usr/bin/env python3
"""
Criar quartos no banco de dados
"""
import asyncio
from app.core.database import get_db, connect_db, disconnect_db

QUARTOS = [
    {"numero": "102", "tipoSuite": "LUXO", "status": "LIVRE"},
    {"numero": "103", "tipoSuite": "LUXO", "status": "LIVRE"},
    {"numero": "104", "tipoSuite": "LUXO", "status": "LIVRE"},
    {"numero": "105", "tipoSuite": "LUXO", "status": "LIVRE"},
    {"numero": "106", "tipoSuite": "LUXO", "status": "LIVRE"},
    {"numero": "107", "tipoSuite": "LUXO", "status": "LIVRE"},
    {"numero": "108", "tipoSuite": "LUXO", "status": "LIVRE"},
    {"numero": "109", "tipoSuite": "LUXO", "status": "LIVRE"},
    {"numero": "110", "tipoSuite": "LUXO", "status": "LIVRE"},
    {"numero": "111", "tipoSuite": "LUXO", "status": "LIVRE"},
    {"numero": "112", "tipoSuite": "LUXO", "status": "LIVRE"},

    {"numero": "202", "tipoSuite": "LUXO 2º", "status": "LIVRE"},
    {"numero": "203", "tipoSuite": "LUXO 2º", "status": "LIVRE"},
    {"numero": "205", "tipoSuite": "LUXO 2º", "status": "LIVRE"},
    {"numero": "206", "tipoSuite": "LUXO 2º", "status": "LIVRE"},
    {"numero": "207", "tipoSuite": "LUXO 2º", "status": "LIVRE"},
    {"numero": "208", "tipoSuite": "LUXO 2º", "status": "LIVRE"},
    {"numero": "209", "tipoSuite": "LUXO 2º", "status": "LIVRE"},
    {"numero": "210", "tipoSuite": "LUXO 2º", "status": "LIVRE"},
    {"numero": "211", "tipoSuite": "LUXO 2º", "status": "LIVRE"},
    {"numero": "212", "tipoSuite": "LUXO 2º", "status": "LIVRE"},

    {"numero": "302", "tipoSuite": "LUXO 3º", "status": "LIVRE"},
    {"numero": "303", "tipoSuite": "LUXO 3º", "status": "LIVRE"},
    {"numero": "304", "tipoSuite": "LUXO 3º", "status": "LIVRE"},
    {"numero": "305", "tipoSuite": "LUXO 3º", "status": "LIVRE"},
    {"numero": "306", "tipoSuite": "LUXO 3º", "status": "LIVRE"},
    {"numero": "307", "tipoSuite": "LUXO 3º", "status": "LIVRE"},
    {"numero": "308", "tipoSuite": "LUXO 3º", "status": "LIVRE"},
    {"numero": "309", "tipoSuite": "LUXO 3º", "status": "LIVRE"},
    {"numero": "310", "tipoSuite": "LUXO 3º", "status": "LIVRE"},
    {"numero": "311", "tipoSuite": "LUXO 3º", "status": "LIVRE"},
    {"numero": "312", "tipoSuite": "LUXO 3º", "status": "LIVRE"},

    {"numero": "402", "tipoSuite": "LUXO 4º EC", "status": "LIVRE"},
    {"numero": "403", "tipoSuite": "LUXO 4º EC", "status": "LIVRE"},
    {"numero": "404", "tipoSuite": "LUXO 4º EC", "status": "LIVRE"},
    {"numero": "405", "tipoSuite": "LUXO 4º EC", "status": "LIVRE"},
    {"numero": "406", "tipoSuite": "LUXO 4º EC", "status": "LIVRE"},
    {"numero": "407", "tipoSuite": "LUXO 4º EC", "status": "LIVRE"},
    {"numero": "408", "tipoSuite": "LUXO 4º EC", "status": "LIVRE"},
    {"numero": "409", "tipoSuite": "LUXO 4º EC", "status": "LIVRE"},
    {"numero": "410", "tipoSuite": "LUXO 4º EC", "status": "LIVRE"},
    {"numero": "411", "tipoSuite": "LUXO 4º EC", "status": "LIVRE"},
    {"numero": "412", "tipoSuite": "LUXO 4º EC", "status": "LIVRE"},
    {"numero": "502", "tipoSuite": "LUXO 4º EC", "status": "LIVRE"},

    {"numero": "101", "tipoSuite": "DUPLA", "status": "LIVRE"},
    {"numero": "201", "tipoSuite": "DUPLA", "status": "LIVRE"},
    {"numero": "301", "tipoSuite": "DUPLA", "status": "LIVRE"},
    {"numero": "401", "tipoSuite": "DUPLA", "status": "LIVRE"},

    {"numero": "503", "tipoSuite": "MASTER", "status": "LIVRE"},
    {"numero": "501", "tipoSuite": "REAL", "status": "LIVRE"},
]

async def seed():
    await connect_db()
    db = get_db()
    
    print("\n=== CRIANDO QUARTOS ===\n")
    
    for q in QUARTOS:
        try:
            existente = await db.quarto.find_unique(where={"numero": q["numero"]})
            if existente:
                needs_update = (existente.tipoSuite != q["tipoSuite"]) or (existente.status != q["status"])
                if needs_update:
                    await db.quarto.update(
                        where={"numero": q["numero"]},
                        data={"tipoSuite": q["tipoSuite"], "status": q["status"]}
                    )
                    print(
                        f"🔁 Quarto {q['numero']} atualizado ({existente.tipoSuite} -> {q['tipoSuite']}, {existente.status} -> {q['status']})"
                    )
                else:
                    print(f"⚠️  Quarto {q['numero']} já existe")
            else:
                await db.quarto.create(data=q)
                print(f"✅ Quarto {q['numero']} criado ({q['tipoSuite']})")
        except Exception as e:
            print(f"❌ Erro ao criar quarto {q['numero']}: {e}")
    
    total = await db.quarto.count()
    print(f"\n📊 Total de quartos: {total}")
    
    await disconnect_db()

if __name__ == "__main__":
    asyncio.run(seed())
