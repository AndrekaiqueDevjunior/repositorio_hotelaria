import asyncio
from prisma import Prisma

async def test():
    db = Prisma()
    await db.connect()
    
    try:
        # Total de reservas
        total = await db.reserva.count()
        print(f'Total de reservas no banco: {total}')
        
        # Listar todas com seus status
        print('\nTodas as reservas e seus status:')
        todas = await db.reserva.find_many()
        for r in todas:
            print(f'  ID {r.id}: {r.statusReserva}')
        
        # Teste da query atual (CONFIRMADA, HOSPEDADO, CHECKIN_REALIZADO, EM_ANDAMENTO)
        ativas_atual = await db.reserva.count(
            where={'statusReserva': {'in': ['CONFIRMADA', 'HOSPEDADO', 'CHECKIN_REALIZADO', 'EM_ANDAMENTO']}}
        )
        print(f'\nReservas Ativas (query atual): {ativas_atual}')
        
        # Teste individual por status
        print('\nContagem por status individual:')
        for status in ['CONFIRMADA', 'HOSPEDADO', 'CHECKIN_REALIZADO', 'EM_ANDAMENTO', 'PENDENTE', 'PENDENTE_PAGAMENTO']:
            count = await db.reserva.count(where={'statusReserva': status})
            if count > 0:
                print(f'  {status}: {count}')
        
    finally:
        await db.disconnect()

asyncio.run(test())
