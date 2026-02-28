import asyncio
from app.core.database import get_db

async def check_reserva_duplicata():
    db = get_db()
    await db.connect()
    
    # Buscar reserva específica pelo código
    reserva = await db.reserva.find_first(
        where={
            'codigoReserva': 'DUP-1767645101'
        },
        include={
            'cliente': True,
            'hospedagem': True,
            'pagamentos': True
        }
    )
    
    if not reserva:
        print('Reserva DUP-1767645101 não encontrada!')
        return
    
    print('=' * 60)
    print('ANÁLISE DA RESERVA DUPLICATA')
    print('=' * 60)
    print(f'Código: {reserva.codigoReserva}')
    print(f'ID: {reserva.id}')
    print(f'Status: {reserva.status}')
    print(f'Cliente: {reserva.cliente.nomeCompleto if reserva.cliente else "N/A"}')
    print(f'Data Criação: {reserva.createdAt}')
    print()
    
    # Datas da reserva
    print('DATAS DA RESERVA:')
    print(f'  Check-in previsto: {reserva.checkinPrevisto}')
    print(f'  Check-out previsto: {reserva.checkoutPrevisto}')
    print()
    
    # Informações de hospedagem
    if reserva.hospedagem:
        hosp = reserva.hospedagem
        print('HOSPEDAGEM:')
        print(f'  ID: {hosp.id}')
        print(f'  Status: {hosp.statusHospedagem}')
        print(f'  Check-in realizado: {hosp.checkinRealizadoEm}')
        print(f'  Check-out realizado: {hosp.checkoutRealizadoEm}')
        print(f'  Número hóspedes: {hosp.numHospedes}')
        print(f'  Data criação: {hosp.createdAt}')
    else:
        print('HOSPEDAGEM: Nenhuma')
    print()
    
    # Pagamentos
    if reserva.pagamentos:
        print('PAGAMENTOS:')
        for i, pag in enumerate(reserva.pagamentos, 1):
            print(f'  {i}. ID: {pag.id}')
            print(f'     Status: {pag.status}')
            print(f'     Método: {pag.metodo}')
            print(f'     Valor: R$ {pag.valor}')
            print(f'     Data: {pag.createdAt}')
            print(f'     ID Cielo: {pag.cieloPaymentId}')
            print()
    else:
        print('PAGAMENTOS: Nenhum')
    print()
    
    # Análise de inconsistências
    print('ANÁLISE DE INCONSISTÊNCIAS:')
    print('-' * 40)
    
    inconsistencias = []
    
    # Status da reserva vs checkout
    if reserva.status == 'CHECKED_OUT':
        if not reserva.hospedagem:
            inconsistencias.append('CHECKED_OUT sem registro de hospedagem')
        elif not reserva.hospedagem.checkoutRealizadoEm:
            inconsistencias.append('CHECKED_OUT sem checkout registrado')
        elif reserva.hospedagem.statusHospedagem != 'FINALIZADA':
            inconsistencias.append(f'CHECKED_OUT mas hospedagem status: {reserva.hospedagem.statusHospedagem}')
    
    # Status da reserva vs pagamentos
    if reserva.status == 'CONFIRMADA' and reserva.pagamentos:
        pagamentos_aprovados = [p for p in reserva.pagamentos if p.status in ['APROVADO', 'CONFIRMADO', 'PAGO']]
        if pagamentos_aprovados:
            inconsistencias.append(f'CONFIRMADA mas tem {len(pagamentos_aprovados)} pagamento(s) aprovado(s)')
    
    # Status da reserva vs datas
    if reserva.checkoutPrevisto and reserva.checkoutPrevisto < reserva.createdAt:
        inconsistencias.append('Checkout previsto anterior à criação')
    
    if inconsistencias:
        for inc in inconsistencias:
            print(f'❌ {inc}')
    else:
        print('✅ Nenhuma inconsistência encontrada')
    
    print()
    print('RECOMENDAÇÕES:')
    print('-' * 40)
    
    if reserva.status == 'CHECKED_OUT':
        print('✅ Status CHECKED_OUT está correto para saída já realizada')
        print('   Botão Pagar não deve aparecer (conforme validação)')
    elif reserva.status == 'CONFIRMADA':
        print('✅ Status CONFIRMADA está correto para reserva confirmada')
        print('   Botão Pagar deve aparecer (se não tiver pagamentos aprovados)')
    
    print()
    print('STATUS REAL NO BANCO:', reserva.status)
    print('STATUS VISÍVEL NO FRONTEND:', reserva.status)
    
    return reserva

if __name__ == "__main__":
    asyncio.run(check_reserva_duplicata())
