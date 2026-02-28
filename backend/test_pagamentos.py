import asyncio
from prisma import Prisma

async def test():
    db = Prisma()
    await db.connect()
    
    try:
        # Total de pagamentos
        total_pagamentos = await db.pagamento.count()
        print(f'Total de pagamentos no banco: {total_pagamentos}')
        
        # Pagamentos aprovados
        pagamentos_aprovados = await db.pagamento.find_many(
            where={'statusPagamento': 'APROVADO'}
        )
        print(f'Pagamentos aprovados: {len(pagamentos_aprovados)}')
        
        # Receita total
        receita = sum(float(p.valor) for p in pagamentos_aprovados)
        print(f'Receita total: R$ {receita:.2f}')
        
        # Todos os pagamentos (para debug)
        todos = await db.pagamento.find_many(take=10)
        print(f'\nPrimeiros 10 pagamentos:')
        for p in todos:
            print(f'  - ID {p.id}: R$ {float(p.valor):.2f} - Status: {p.statusPagamento}')
    finally:
        await db.disconnect()

asyncio.run(test())
