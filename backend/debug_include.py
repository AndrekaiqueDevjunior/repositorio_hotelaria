import asyncio
from prisma import Client

async def debug_include():
    db = Client()
    await db.connect()
    
    # Simular exatamente o que o get_by_id faz
    reserva = await db.reserva.find_unique(
        where={'id': 7},
        include={'pagamentos': True}
    )
    
    print('🔍 Debug include:')
    print(f'Tem pagamentos: {hasattr(reserva, "pagamentos")}')
    print(f'Pagamentos: {reserva.pagamentos}')
    print(f'CheckinReal: {reserva.checkinReal}')
    print(f'CheckoutReal: {reserva.checkoutReal}')
    
    await db.disconnect()

asyncio.run(debug_include())
