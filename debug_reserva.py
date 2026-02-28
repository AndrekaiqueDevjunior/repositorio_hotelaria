import asyncio
from prisma import Prisma

async def debug():
    db = Prisma()
    await db.connect()
    
    # Buscar reserva RCF-202601-FB3FDD
    reserva = await db.reserva.find_first(
        where={'codigoReserva': 'RCF-202601-FB3FDD'},
        include={
            'pagamentos': True,
            'hospedagem': True
        }
    )
    
    if not reserva:
        print('Reserva não encontrada')
        await db.disconnect()
        return
    
    print(f'=== RESERVA {reserva.codigoReserva} ===')
    print(f'ID: {reserva.id}')
    print(f'statusReserva: {reserva.statusReserva}')
    print(f'clienteId: {reserva.clienteId}')
    
    print(f'\n=== PAGAMENTOS ({len(reserva.pagamentos)}) ===')
    for p in reserva.pagamentos:
        print(f'  - ID={p.id} | valor={p.valor} | metodo={p.metodo} | statusPagamento={p.statusPagamento}')
    
    print(f'\n=== HOSPEDAGEM ===')
    if reserva.hospedagem:
        print(f'  - ID={reserva.hospedagem.id} | statusHospedagem={reserva.hospedagem.statusHospedagem}')
    else:
        print('  - Nenhuma hospedagem criada')
    
    # Validar check-in
    print(f'\n=== VALIDAÇÃO CHECK-IN ===')
    print(f'statusReserva == "CONFIRMADA"? {reserva.statusReserva == "CONFIRMADA"}')
    
    if reserva.pagamentos:
        pag = reserva.pagamentos[0]
        print(f'statusPagamento == "CONFIRMADO"? {pag.statusPagamento == "CONFIRMADO"}')
    else:
        print('Nenhum pagamento encontrado')
    
    if reserva.hospedagem:
        print(f'statusHospedagem == "NAO_INICIADA"? {reserva.hospedagem.statusHospedagem == "NAO_INICIADA"}')
    else:
        print('Hospedagem não existe (precisa criar?)')
    
    await db.disconnect()

asyncio.run(debug())
