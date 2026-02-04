import asyncio
from app.core.database import get_db, connect_db, disconnect_db

async def verificar_inconsistencias():
    await connect_db()
    db = get_db()
    
    try:
        # Buscar todas as reservas com problemas de sincronização
        reservas = await db.reserva.find_many(
            include={
                'hospedagem': True,
                'pagamentos': True
            }
        )
        
        print('=== VERIFICAÇÃO DE INCONSISTÊNCIAS DE STATUS ===')
        print()
        
        inconsistentes = []
        
        for reserva in reservas:
            status_reserva = reserva.statusReserva
            
            if reserva.hospedagem:
                status_hospedagem = reserva.hospedagem.statusHospedagem
                
                # Verificar inconsistências
                inconsistencia = None
                
                if status_reserva == 'PENDENTE' and status_hospedagem == 'CHECKIN_REALIZADO':
                    inconsistencia = 'Reserva PENDENTE mas hospedagem CHECKIN_REALIZADO'
                elif status_reserva == 'PENDENTE' and status_hospedagem == 'CHECKOUT_REALIZADO':
                    inconsistencia = 'Reserva PENDENTE mas hospedagem CHECKOUT_REALIZADO'
                elif status_reserva == 'PENDENTE' and status_hospedagem == 'EM_ANDAMENTO':
                    inconsistencia = 'Reserva PENDENTE mas hospedagem EM_ANDAMENTO'
                elif status_reserva == 'CONFIRMADA' and status_hospedagem == 'CHECKIN_REALIZADO':
                    inconsistencia = 'Reserva CONFIRMADA mas hospedagem já fez check-in'
                elif status_reserva == 'CHECKED_OUT' and status_hospedagem != 'CHECKOUT_REALIZADO':
                    inconsistencia = 'Reserva CHECKED_OUT mas hospedagem não CHECKOUT_REALIZADO'
                elif status_reserva == 'HOSPEDADO' and status_hospedagem == 'CHECKOUT_REALIZADO':
                    inconsistencia = 'Reserva HOSPEDADO mas hospedagem CHECKOUT_REALIZADO'
                
                if inconsistencia:
                    inconsistentes.append({
                        'id': reserva.id,
                        'codigo': reserva.codigoReserva,
                        'status_reserva': status_reserva,
                        'status_hospedagem': status_hospedagem,
                        'problema': inconsistencia
                    })
        
        if inconsistentes:
            print(f'🚨 ENCONTRADAS {len(inconsistentes)} RESERVAS INCONSISTENTES:')
            print()
            for i, inc in enumerate(inconsistentes, 1):
                print(f'{i}. Reserva ID: {inc[\"id\"]}')
                print(f'   Código: {inc[\"codigo\"]}')
                print(f'   Status Reserva: {inc[\"status_reserva\"]}')
                print(f'   Status Hospedagem: {inc[\"status_hospedagem\"]}')
                print(f'   🚨 PROBLEMA: {inc[\"problema\"]}')
                print()
        else:
            print('✅ NENHUMA INCONSISTÊNCIA ENCONTRADA')
            print('Todas as reservas estão sincronizadas!')
        
        # Estatísticas finais
        total_reservas = len(reservas)
        total_inconsistentes = len(inconsistentes)
        taxa_inconsistencia = (total_inconsistentes / total_reservas * 100) if total_reservas > 0 else 0
        
        print()
        print('📊 ESTATÍSTICAS:')
        print(f'   Total de reservas: {total_reservas}')
        print(f'   Inconsistentes: {total_inconsistentes}')
        print(f'   Taxa de inconsistência: {taxa_inconsistencia:.1f}%')
        
    except Exception as e:
        print('ERRO:', e)
        import traceback
        traceback.print_exc()
    finally:
        await disconnect_db()

if __name__ == '__main__':
    asyncio.run(verificar_inconsistencias())
