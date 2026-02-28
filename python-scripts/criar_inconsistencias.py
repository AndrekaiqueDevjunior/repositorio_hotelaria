import asyncio
from app.core.database import get_db, connect_db, disconnect_db
from datetime import datetime, timedelta

async def criar_inconsistencias_status():
    await connect_db()
    db = get_db()
    
    try:
        print('🔧 CRIANDO INCONSISTÊNCIAS DE STATUS...')
        print()
        
        # Buscar as 3 novas reservas criadas
        reservas = await db.reserva.find_many(
            where={
                'codigoReserva': {
                    'in': ['RCF-202601-826786', 'RCF-202601-A11970', 'RCF-202601-9BBAE1']
                }
            },
            include={'hospedagem': True}
        )
        
        print(f'Encontradas {len(reservas)} reservas para manipular')
        print()
        
        # Cenário 1: Reserva PENDENTE com hospedagem CHECKIN_REALIZADO
        if len(reservas) >= 1:
            reserva1 = reservas[0]
            print(f'1. Manipulando reserva {reserva1.codigoReserva}...')
            
            # Criar hospedagem com check-in realizado
            if not reserva1.hospedagem:
                hospedagem1 = await db.hospedagem.create({
                    'data': {
                        'reservaId': reserva1.id,
                        'statusHospedagem': 'CHECKIN_REALIZADO',
                        'checkinRealizadoEm': datetime.now() - timedelta(hours=2),
                        'checkinRealizadoPor': 1,
                        'numHospedes': 2,
                        'numCriancas': 0,
                        'placaVeiculo': 'ABC1234',
                        'observacoes': 'Check-in realizado manualmente para teste'
                    }
                })
                print(f'   ✅ Hospedagem criada: CHECKIN_REALIZADO')
                print(f'   📝 Status: Reserva={reserva1.statusReserva}, Hospedagem=CHECKIN_REALIZADO')
                print(f'   ⚠️  INCONSISTÊNCIA: Reserva PENDENTE mas hospedagem já fez check-in!')
            else:
                print(f'   ℹ️  Hospedagem já existe')
        
        print()
        
        # Cenário 2: Reserva PENDENTE com hospedagem CHECKOUT_REALIZADO
        if len(reservas) >= 2:
            reserva2 = reservas[1]
            print(f'2. Manipulando reserva {reserva2.codigoReserva}...')
            
            # Criar hospedagem com checkout realizado
            if not reserva2.hospedagem:
                hospedagem2 = await db.hospedagem.create({
                    'data': {
                        'reservaId': reserva2.id,
                        'statusHospedagem': 'CHECKOUT_REALIZADO',
                        'checkinRealizadoEm': datetime.now() - timedelta(days=1),
                        'checkinRealizadoPor': 1,
                        'checkoutRealizadoEm': datetime.now() - timedelta(hours=1),
                        'checkoutRealizadoPor': 1,
                        'numHospedes': 1,
                        'numCriancas': 0,
                        'observacoes': 'Checkout realizado manualmente para teste'
                    }
                })
                print(f'   ✅ Hospedagem criada: CHECKOUT_REALIZADO')
                print(f'   📝 Status: Reserva={reserva2.statusReserva}, Hospedagem=CHECKOUT_REALIZADO')
                print(f'   ⚠️  INCONSISTÊNCIA GRAVE: Reserva PENDENTE mas hospedagem já fez checkout!')
            else:
                print(f'   ℹ️  Hospedagem já existe')
        
        print()
        
        # Cenário 3: Reserva PENDENTE com hospedagem em status intermediário
        if len(reservas) >= 3:
            reserva3 = reservas[2]
            print(f'3. Manipulando reserva {reserva3.codigoReserva}...')
            
            # Criar hospedagem com status intermediário
            if not reserva3.hospedagem:
                hospedagem3 = await db.hospedagem.create({
                    'data': {
                        'reservaId': reserva3.id,
                        'statusHospedagem': 'EM_ANDAMENTO',
                        'checkinRealizadoEm': datetime.now() - timedelta(hours=6),
                        'checkinRealizadoPor': 1,
                        'numHospedes': 3,
                        'numCriancas': 1,
                        'placaVeiculo': 'XYZ5678',
                        'observacoes': 'Status intermediário para teste'
                    }
                })
                print(f'   ✅ Hospedagem criada: EM_ANDAMENTO')
                print(f'   📝 Status: Reserva={reserva3.statusReserva}, Hospedagem=EM_ANDAMENTO')
                print(f'   ⚠️  INCONSISTÊNCIA: Reserva PENDENTE mas hospedagem está EM_ANDAMENTO!')
            else:
                print(f'   ℹ️  Hospedagem já existe')
        
        print()
        print('🎯 INCONSISTÊNCIAS CRIADAS COM SUCESSO!')
        print()
        print('📋 RESUMO DOS CENÁRIOS:')
        print('   1. Reserva PENDENTE + Hospedagem CHECKIN_REALIZADO')
        print('   2. Reserva PENDENTE + Hospedagem CHECKOUT_REALIZADO')
        print('   3. Reserva PENDENTE + Hospedagem EM_ANDAMENTO')
        print()
        print('🔍 AGORA USE O SCRIPT DE VERIFICAÇÃO PARA ENCONTRAR ESTAS INCONSISTÊNCIAS!')
        
    except Exception as e:
        print('ERRO:', e)
        import traceback
        traceback.print_exc()
    finally:
        await disconnect_db()

if __name__ == '__main__':
    asyncio.run(criar_inconsistencias_status())
