import asyncio
from prisma import Prisma

async def test():
    db = Prisma()
    await db.connect()
    
    aguardando = await db.comprovantepagamento.count(
        where={'statusValidacao': 'AGUARDANDO_COMPROVANTE'}
    )
    em_analise = await db.comprovantepagamento.count(
        where={'statusValidacao': 'EM_ANALISE'}
    )
    aprovado = await db.comprovantepagamento.count(
        where={'statusValidacao': 'APROVADO'}
    )
    recusado = await db.comprovantepagamento.count(
        where={'statusValidacao': 'RECUSADO'}
    )
    
    print(f'AGUARDANDO={aguardando}')
    print(f'EM_ANALISE={em_analise}')
    print(f'APROVADO={aprovado}')
    print(f'RECUSADO={recusado}')
    
    todos = await db.comprovantepagamento.find_many(
        include={
            'pagamento': {
                'include': {
                    'reserva': {
                        'include': {'cliente': True}
                    }
                }
            }
        }
    )
    
    print(f'\nTOTAL={len(todos)}')
    for c in todos[:5]:
        cliente_nome = 'N/A'
        if c.pagamento and c.pagamento.reserva and c.pagamento.reserva.cliente:
            cliente_nome = c.pagamento.reserva.cliente.nomeCompleto
        print(f'ID={c.id} status={c.statusValidacao} pag={c.pagamentoId} cliente={cliente_nome}')
    
    await db.disconnect()

asyncio.run(test())
