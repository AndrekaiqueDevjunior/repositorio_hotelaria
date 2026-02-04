"""
Script de Verificação e Correção de Sincronização de Status

Verifica e corrige inconsistências entre status de reservas e hospedagens.
"""

import asyncio
from app.core.database import get_db, connect_db, disconnect_db

async def verificar_e_corrigir_sincronizacao():
    """
    Verifica todas as reservas e corrige inconsistências de status
    """
    await connect_db()
    db = get_db()
    
    try:
        print('🔍 VERIFICANDO SINCRONIZAÇÃO DE STATUS...')
        print()
        
        # Buscar todas as reservas com hospedagem
        reservas = await db.reserva.find_many(
            include={
                'hospedagem': True
            }
        )
        
        corrigidas = []
        
        for reserva in reservas:
            if not reserva.hospedagem:
                continue
                
            status_reserva = reserva.statusReserva
            status_hospedagem = reserva.hospedagem.statusHospedagem
            
            # Regras de sincronização
            status_correto = None
            
            if status_hospedagem == 'CHECKOUT_REALIZADO':
                status_correto = 'CHECKED_OUT'
            elif status_hospedagem == 'CHECKIN_REALIZADO':
                status_correto = 'HOSPEDADO'
            elif status_hospedagem == 'NAO_INICIADA':
                status_correto = 'CONFIRMADA'
            
            # Verificar se precisa corrigir
            if status_correto and status_reserva != status_correto:
                print(f'❌ Reserva #{reserva.id} ({reserva.codigoReserva})')
                print(f'   Status Atual: {status_reserva}')
                print(f'   Status Correto: {status_correto}')
                print(f'   Status Hospedagem: {status_hospedagem}')
                
                # Corrigir automaticamente
                await db.reserva.update(
                    where={'id': reserva.id},
                    data={'statusReserva': status_correto}
                )
                
                print(f'   ✅ CORRIGIDO para {status_correto}')
                print()
                
                corrigidas.append({
                    'id': reserva.id,
                    'codigo': reserva.codigoReserva,
                    'de': status_reserva,
                    'para': status_correto
                })
        
        # Resumo
        if corrigidas:
            print(f'🎯 RESUMO DA CORREÇÃO:')
            print(f'   ✅ {len(corrigidas)} reservas corrigidas')
            print()
            for corr in corrigidas:
                print(f'   - Reserva #{corr["id"]}: {corr["de"]} → {corr["para"]}')
        else:
            print('✅ TODAS AS RESERVAS ESTÃO SINCRONIZADAS!')
        
        print()
        print('🚀 Verificação concluída com sucesso!')
        
    except Exception as e:
        print(f'❌ ERRO: {e}')
        import traceback
        traceback.print_exc()
    finally:
        await disconnect_db()

if __name__ == "__main__":
    asyncio.run(verificar_e_corrigir_sincronizacao())
