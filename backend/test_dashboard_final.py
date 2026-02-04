import asyncio
from prisma import Prisma

async def test():
    db = Prisma()
    await db.connect()
    
    try:
        # Teste das 3 categorias
        pendentes = await db.reserva.count(
            where={'statusReserva': {'in': ['PENDENTE', 'PENDENTE_PAGAMENTO', 'AGUARDANDO_COMPROVANTE', 'EM_ANALISE', 'PAGA_REJEITADA']}}
        )
        
        ativas = await db.reserva.count(
            where={'statusReserva': {'in': ['CONFIRMADA', 'HOSPEDADO', 'CHECKIN_REALIZADO', 'EM_ANDAMENTO']}}
        )
        
        finalizadas = await db.reserva.count(
            where={'statusReserva': {'in': ['CHECKOUT_REALIZADO', 'CHECKED_OUT', 'CANCELADA', 'CANCELADO', 'FINALIZADA', 'NO_SHOW']}}
        )
        
        print('Dashboard - 3 Categorias de Reservas:')
        print(f'⏳ Pendentes (aguardando pagamento): {pendentes}')
        print(f'✅ Ativas (confirmadas/em andamento): {ativas}')
        print(f'🏁 Finalizadas (checkout/canceladas): {finalizadas}')
        print(f'\nTotal: {pendentes + ativas + finalizadas}')
        
    finally:
        await db.disconnect()

asyncio.run(test())
