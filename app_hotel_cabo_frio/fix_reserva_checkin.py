import asyncio
from prisma import Prisma
from datetime import datetime

async def fix():
    db = Prisma()
    await db.connect()
    
    # 1. Corrigir statusPagamento de APROVADO para CONFIRMADO
    print('=== CORRIGINDO PAGAMENTOS APROVADO -> CONFIRMADO ===')
    pagamentos_aprovado = await db.pagamento.find_many(
        where={'statusPagamento': 'APROVADO'}
    )
    print(f'Encontrados {len(pagamentos_aprovado)} pagamentos com APROVADO')
    
    for p in pagamentos_aprovado:
        await db.pagamento.update(
            where={'id': p.id},
            data={'statusPagamento': 'CONFIRMADO'}
        )
        print(f'  - Pagamento {p.id}: APROVADO -> CONFIRMADO')
    
    # 2. Criar hospedagem para reservas CONFIRMADAS sem hospedagem
    print('\n=== CRIANDO HOSPEDAGENS FALTANTES ===')
    reservas_confirmadas = await db.reserva.find_many(
        where={'statusReserva': 'CONFIRMADA'},
        include={'hospedagem': True}
    )
    
    criadas = 0
    for r in reservas_confirmadas:
        if not r.hospedagem:
            await db.hospedagem.create(
                data={
                    'reserva': {'connect': {'id': r.id}},
                    'statusHospedagem': 'NAO_INICIADA'
                }
            )
            print(f'  - Criada hospedagem para reserva {r.codigoReserva} (ID={r.id})')
            criadas += 1
    
    print(f'\n✅ Corrigidos {len(pagamentos_aprovado)} pagamentos')
    print(f'✅ Criadas {criadas} hospedagens')
    
    await db.disconnect()

asyncio.run(fix())
