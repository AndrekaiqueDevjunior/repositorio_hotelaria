import asyncio
from prisma import Prisma

async def test():
    db = Prisma()
    await db.connect()
    
    try:
        # Total de reservas
        total = await db.reserva.count()
        print(f'Total de reservas: {total}')
        
        # Por status
        print('\nReservas por status:')
        todos_status = await db.reserva.find_many()
        status_count = {}
        for r in todos_status:
            status = r.statusReserva
            status_count[status] = status_count.get(status, 0) + 1
        
        for status, count in sorted(status_count.items()):
            print(f'  {status}: {count}')
        
        # Teste da query atual (CHECKED_OUT, CANCELADO)
        finalizadas_atual = await db.reserva.count(
            where={'statusReserva': {'in': ['CHECKED_OUT', 'CANCELADO']}}
        )
        print(f'\nFinalizadas (CHECKED_OUT, CANCELADO): {finalizadas_atual}')
        
        # Teste com outros status possíveis
        finalizadas_alt = await db.reserva.count(
            where={'statusReserva': {'in': ['CHECKOUT_REALIZADO', 'CANCELADA', 'CANCELADO', 'CHECKED_OUT', 'FINALIZADA']}}
        )
        print(f'Finalizadas (todos os status finais): {finalizadas_alt}')
        
    finally:
        await db.disconnect()

asyncio.run(test())
