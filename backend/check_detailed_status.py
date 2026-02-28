import asyncio
from app.core.database import get_db

async def check_detailed_status():
    db = get_db()
    await db.connect()
    
    # Buscar todas as reservas com detalhes
    reservas = await db.reserva.find_many(
        include={
            'hospedagem': True,
            'cliente': True
        },
        order={'id': 'desc'}
    )
    
    print(f'Total de reservas: {len(reservas)}')
    print()
    
    print('Status das reservas:')
    status_count = {}
    for reserva in reservas:
        status = reserva.status
        status_count[status] = status_count.get(status, 0) + 1
    
    for status, count in sorted(status_count.items()):
        print(f'  {status}: {count}')
    
    print()
    print('Análise detalhada por status:')
    print('=' * 50)
    
    # Analisar cada status
    for status in ['PENDENTE', 'CONFIRMADA', 'HOSPEDADO', 'CHECKED_OUT', 'CANCELADO']:
        reservas_status = [r for r in reservas if r.status == status]
        
        print(f'\n{status} ({len(reservas_status)} reservas):')
        
        for reserva in reservas_status[:5]:  # Limitar a 5 por status
            print(f'  ID: {reserva.id} | Código: {getattr(reserva, "codigoReserva", "N/A")}')
            print(f'    Cliente: {getattr(reserva.cliente, "nomeCompleto", "N/A")}')
            
            if reserva.hospedagem:
                print(f'    Hospedagem: ID {reserva.hospedagem.id}')
                print(f'    Check-in: {reserva.hospedagem.checkinRealizadoEm}')
                print(f'    Check-out: {reserva.hospedagem.checkoutRealizadoEm}')
                print(f'    Status Hospedagem: {getattr(reserva.hospedagem, "statusHospedagem", "N/A")}')
            else:
                print(f'    Hospedagem: NENHUMA')
            
            print()
    
    # Verificar inconsistências específicas
    print('Inconsistências encontradas:')
    print('=' * 50)
    
    inconsistentes = []
    
    for reserva in reservas:
        # CONFIRMADA com checkout realizado
        if reserva.status == 'CONFIRMADA' and reserva.hospedagem and reserva.hospedagem.checkoutRealizadoEm:
            inconsistentes.append({
                'tipo': 'CONFIRMADA com checkout',
                'id': reserva.id,
                'codigo': getattr(reserva, 'codigoReserva', 'N/A'),
                'checkout': reserva.hospedagem.checkoutRealizadoEm
            })
        
        # CHECKED_OUT sem hospedagem
        elif reserva.status == 'CHECKED_OUT' and not reserva.hospedagem:
            inconsistentes.append({
                'tipo': 'CHECKED_OUT sem hospedagem',
                'id': reserva.id,
                'codigo': getattr(reserva, 'codigoReserva', 'N/A')
            })
        
        # HOSPEDADO sem check-in
        elif reserva.status == 'HOSPEDADO' and reserva.hospedagem and not reserva.hospedagem.checkinRealizadoEm:
            inconsistentes.append({
                'tipo': 'HOSPEDADO sem check-in',
                'id': reserva.id,
                'codigo': getattr(reserva, 'codigoReserva', 'N/A')
            })
    
    if inconsistentes:
        for inc in inconsistentes:
            print(f'  {inc["tipo"]}:')
            print(f'    ID: {inc["id"]} | Código: {inc["codigo"]}')
            if 'checkout' in inc:
                print(f'    Checkout: {inc["checkout"]}')
            print()
    else:
        print('  Nenhuma inconsistência encontrada!')
    
    return inconsistentes

if __name__ == "__main__":
    asyncio.run(check_detailed_status())
