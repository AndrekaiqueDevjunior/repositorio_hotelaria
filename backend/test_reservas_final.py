import asyncio
from prisma import Prisma

async def test():
    db = Prisma()
    await db.connect()
    
    try:
        # Teste da query corrigida
        finalizadas = await db.reserva.count(
            where={'statusReserva': {'in': ['CHECKOUT_REALIZADO', 'CHECKED_OUT', 'CANCELADA', 'CANCELADO', 'FINALIZADA']}}
        )
        print(f'✅ Reservas Finalizadas/Excluídas: {finalizadas}')
        
        # Detalhes
        reservas_fin = await db.reserva.find_many(
            where={'statusReserva': {'in': ['CHECKOUT_REALIZADO', 'CHECKED_OUT', 'CANCELADA', 'CANCELADO', 'FINALIZADA']}}
        )
        for r in reservas_fin:
            print(f'  - ID {r.id}: Status {r.statusReserva}')
        
    finally:
        await db.disconnect()

asyncio.run(test())
