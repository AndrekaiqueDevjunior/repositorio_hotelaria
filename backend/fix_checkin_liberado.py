import asyncio
from prisma import Prisma

async def fix():
    db = Prisma()
    await db.connect()
    
    # Buscar reservas com CHECKIN_LIBERADO
    reservas = await db.reserva.find_many(
        where={'statusReserva': 'CHECKIN_LIBERADO'}
    )
    
    print(f'Encontradas {len(reservas)} reservas com CHECKIN_LIBERADO')
    
    for r in reservas:
        print(f'  - Reserva {r.codigoReserva} (ID={r.id}): CHECKIN_LIBERADO -> CONFIRMADA')
        await db.reserva.update(
            where={'id': r.id},
            data={'statusReserva': 'CONFIRMADA'}
        )
    
    print(f'\n✅ Corrigidas {len(reservas)} reservas')
    
    await db.disconnect()

asyncio.run(fix())
