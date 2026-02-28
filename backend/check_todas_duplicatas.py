import asyncio
from app.core.database import get_db

async def check_todas_duplicatas():
    db = get_db()
    await db.connect()
    
    # Buscar todas as reservas com código "DUP"
    reservas_dup = await db.reserva.find_many(
        where={
            'codigoReserva': {
                'startsWith': 'DUP'
            }
        },
        include={
            'cliente': True,
            'hospedagem': True,
            'pagamentos': True
        },
        order={'id': 'desc'}
    )
    
    print(f'Total de reservas com código "DUP": {len(reservas_dup)}')
    print('=' * 60)
    
    for i, reserva in enumerate(reservas_dup, 1):
        print(f'\n{i}. RESERVA: {reserva.codigoReserva}')
        print(f'   ID: {reserva.id}')
        print(f'   Status: {reserva.status}')
        print(f'   Cliente: {reserva.cliente.nomeCompleto}')
        print(f'   Check-in: {reserva.checkinPrevisto}')
        print(f'   Check-out: {reserva.checkoutPrevisto}')
        
        # Hospedagem
        if reserva.hospedagem:
            hosp = reserva.hospedagem
            print(f'   Hospedagem ID: {hosp.id}')
            print(f'   Status Hosp: {hosp.statusHospedagem}')
            print(f'   Check-in Real: {hosp.checkinRealizadoEm}')
            print(f'   Check-out Real: {hosp.checkoutRealizadoEm}')
        else:
            print(f'   Hospedagem: Nenhuma')
        
        # Pagamentos
        if reserva.pagamentos:
            print(f'   Pagamentos: {len(reserva.pagamentos)}')
            for pag in reserva.pagamentos:
                print(f'     - ID: {pag.id} | Status: {pag.status} | Valor: R${pag.valor}')
        else:
            print(f'   Pagamentos: Nenhum')
        
        # Verificar inconsistências
        inconsistencias = []
        
        if reserva.status == 'CHECKED_OUT':
            if not reserva.hospedagem:
                inconsistencias.append('CHECKED_OUT sem hospedagem')
            elif not reserva.hospedagem.checkoutRealizadoEm:
                inconsistencias.append('CHECKED_OUT sem checkout real')
        
        if inconsistencias:
            print(f'   ❌ Inconsistências: {", ".join(inconsistencias)}')
        else:
            print(f'   ✅ Status consistente')
    
    print('\n' + '=' * 60)
    print('RESUMO DOS STATUS DAS RESERVAS "DUP"')
    print('=' * 60)
    
    status_count = {}
    for reserva in reservas_dup:
        status_count[reserva.status] = status_count.get(reserva.status, 0) + 1
    
    for status, count in sorted(status_count.items()):
        print(f'{status}: {count} reservas')
    
    print(f'\nTotal analisado: {len(reservas_dup)} reservas')

if __name__ == "__main__":
    asyncio.run(check_todas_duplicatas())
