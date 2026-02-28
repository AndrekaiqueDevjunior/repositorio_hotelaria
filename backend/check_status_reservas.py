import asyncio
from app.core.database import get_db

async def check_status_reservas():
    db = get_db()
    await db.connect()
    
    # Buscar todas as reservas
    reservas = await db.reserva.find_many(
        include={
            'hospedagem': True
        },
        order={'id': 'desc'}
    )
    
    print(f'Total de reservas: {len(reservas)}')
    print()
    
    # Agrupar por status
    status_count = {}
    inconsistentes = []
    
    for reserva in reservas:
        status = reserva.status
        status_count[status] = status_count.get(status, 0) + 1
        
        # Verificar inconsistências
        if status == 'CONFIRMADA' and reserva.hospedagem:
            if reserva.hospedagem.checkoutRealizadoEm:
                inconsistentes.append({
                    'id': reserva.id,
                    'codigo': getattr(reserva, 'codigoReserva', 'N/A'),
                    'status_reserva': status,
                    'checkout_realizado': reserva.hospedagem.checkoutRealizadoEm,
                    'status_hospedagem': getattr(reserva.hospedagem, 'statusHospedagem', 'N/A')
                })
        elif status == 'HOSPEDADO' and reserva.hospedagem:
            if reserva.hospedagem.checkoutRealizadoEm:
                # Este é o correto
                pass
            else:
                # Hospedado sem checkout - pode ser normal
                pass
        elif status == 'CHECKED_OUT' and not reserva.hospedagem:
            # CHECKED_OUT sem hospedagem - inconsistência
            inconsistentes.append({
                'id': reserva.id,
                'codigo': getattr(reserva, 'codigoReserva', 'N/A'),
                'status_reserva': status,
                'hospedagem': 'NENHUMA',
                'observacao': 'CHECKED_OUT sem registro de hospedagem'
            })
    
    print('Status das reservas:')
    for status, count in sorted(status_count.items()):
        print(f'  {status}: {count}')
    
    print()
    print(f'Total de inconsistências encontradas: {len(inconsistentes)}')
    
    if inconsistentes:
        print()
        print('Reservas com inconsistências:')
        for inc in inconsistentes[:10]:  # Limitar a 10 para não sobrecarregar
            print(f'  ID: {inc["id"]} | Código: {inc["codigo"]} | Status: {inc["status_reserva"]}')
            if 'checkout_realizado' in inc:
                print(f'    Checkout: {inc["checkout_realizado"]}')
            if 'status_hospedagem' in inc:
                print(f'    Status Hospedagem: {inc["status_hospedagem"]}')
            if 'observacao' in inc:
                print(f'    Observacao: {inc["observacao"]}')
            print()
    
    return inconsistentes

if __name__ == "__main__":
    asyncio.run(check_status_reservas())
