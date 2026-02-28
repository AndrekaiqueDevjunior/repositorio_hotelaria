import asyncio
from prisma import Prisma

async def test():
    db = Prisma()
    await db.connect()
    
    try:
        # Pagamentos confirmados/aprovados
        pagamentos = await db.pagamento.find_many(
            where={'statusPagamento': {'in': ['CONFIRMADO', 'APROVADO']}}
        )
        print(f'Pagamentos CONFIRMADO/APROVADO: {len(pagamentos)}')
        
        receita = sum(float(p.valor) for p in pagamentos)
        print(f'Receita total: R$ {receita:.2f}')
        
        for p in pagamentos:
            print(f'  - ID {p.id}: R$ {float(p.valor):.2f} - Status: {p.statusPagamento}')
    finally:
        await db.disconnect()

asyncio.run(test())
