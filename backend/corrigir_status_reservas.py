import asyncio
from app.core.database import get_db

async def corrigir_status_reservas():
    db = get_db()
    await db.connect()
    
    # Buscar todas as reservas
    reservas = await db.reserva.find_many(
        include={
            'hospedagem': True,
            'cliente': True
        },
        order={'id': 'desc'}
    )
    
    print('Análise e correção de status de reservas')
    print('=' * 50)
    
    corrigidas = []
    
    for reserva in reservas:
        # Caso 1: CHECKED_OUT sem hospedagem
        if reserva.status == 'CHECKED_OUT' and not reserva.hospedagem:
            print(f'CORREÇÃO 1: CHECKED_OUT sem hospedagem')
            print(f'  ID: {reserva.id} | Código: {getattr(reserva, "codigoReserva", "N/A")}')
            print(f'  Cliente: {getattr(reserva.cliente, "nomeCompleto", "N/A")}')
            print(f'  Status atual: CHECKED_OUT')
            print(f'  Problema: Não há registro de hospedagem')
            
            # Opções:
            # 1. Manter como CHECKED_OUT (se realmente foi checkout)
            # 2. Mudar para CANCELADO (se não houve hospedagem)
            # 3. Mudar para CONFIRMADA (se ainda está confirmada)
            
            # Por segurança, vamos manter CHECKED_OUT mas registrar a observação
            print(f'  Ação: Manter CHECKED_OUT (já que usuário relatou checkout)')
            print(f'  Observação: Requer verificação manual')
            print()
            
            corrigidas.append({
                'id': reserva.id,
                'codigo': getattr(reserva, 'codigoReserva', 'N/A'),
                'problema': 'CHECKED_OUT sem hospedagem',
                'acao': 'Manter status (requer verificação manual)'
            })
        
        # Caso 2: HOSPEDADO sem check-in
        elif reserva.status == 'HOSPEDADO' and reserva.hospedagem and not reserva.hospedagem.checkinRealizadoEm:
            print(f'CORREÇÃO 2: HOSPEDADO sem check-in')
            print(f'  ID: {reserva.id} | Código: {getattr(reserva, "codigoReserva", "N/A")}')
            print(f'  Cliente: {getattr(reserva.cliente, "nomeCompleto", "N/A")}')
            print(f'  Status atual: HOSPEDADO')
            print(f'  Check-in: Nenhum')
            print(f'  Status hospedagem: {getattr(reserva.hospedagem, "statusHospedagem", "N/A")}')
            
            # Se está HOSPEDADO mas não fez check-in, deveria voltar para CONFIRMADA
            try:
                await db.reserva.update(
                    where={'id': reserva.id},
                    data={'status': 'CONFIRMADA'}
                )
                print(f'  Ação: Status alterado para CONFIRMADA')
                print(f'  Status antigo: HOSPEDADO')
                print(f'  Status novo: CONFIRMADA')
                
                corrigidas.append({
                    'id': reserva.id,
                    'codigo': getattr(reserva, 'codigoReserva', 'N/A'),
                    'problema': 'HOSPEDADO sem check-in',
                    'acao': 'Status alterado para CONFIRMADA',
                    'antes': 'HOSPEDADO',
                    'depois': 'CONFIRMADA'
                })
            except Exception as e:
                print(f'  ERRO ao corrigir: {str(e)}')
            
            print()
        
        # Caso 3: CHECKED_OUT com hospedagem mas sem checkout
        elif reserva.status == 'CHECKED_OUT' and reserva.hospedagem and not reserva.hospedagem.checkoutRealizadoEm:
            print(f'CORREÇÃO 3: CHECKED_OUT sem checkout registrado')
            print(f'  ID: {reserva.id} | Código: {getattr(reserva, "codigoReserva", "N/A")}')
            print(f'  Cliente: {getattr(reserva.cliente, "nomeCompleto", "N/A")}')
            print(f'  Status atual: CHECKED_OUT')
            print(f'  Check-in: {reserva.hospedagem.checkinRealizadoEm}')
            print(f'  Check-out: Nenhum')
            
            # Se está CHECKED_OUT mas não tem checkout, registrar checkout agora
            from datetime import datetime
            try:
                await db.hospedagem.update(
                    where={'id': reserva.hospedagem.id},
                    data={
                        'checkoutRealizadoEm': datetime.now(),
                        'statusHospedagem': 'FINALIZADA'
                    }
                )
                print(f'  Ação: Checkout registrado automaticamente')
                print(f'  Checkout: {datetime.now()}')
                print(f'  Status hospedagem: FINALIZADA')
                
                corrigidas.append({
                    'id': reserva.id,
                    'codigo': getattr(reserva, 'codigoReserva', 'N/A'),
                    'problema': 'CHECKED_OUT sem checkout',
                    'acao': 'Checkout registrado automaticamente'
                })
            except Exception as e:
                print(f'  ERRO ao registrar checkout: {str(e)}')
            
            print()
    
    print('Resumo das correções:')
    print('=' * 50)
    print(f'Total de correções: {len(corrigidas)}')
    
    for i, corr in enumerate(corrigidas, 1):
        print(f'{i}. ID: {corr["id"]} | Código: {corr["codigo"]}')
        print(f'   Problema: {corr["problema"]}')
        print(f'   Ação: {corr["acao"]}')
        if 'antes' in corr:
            print(f'   Antes: {corr["antes"]} → Depois: {corr["depois"]}')
        print()
    
    return corrigidas

if __name__ == "__main__":
    asyncio.run(corrigir_status_reservas())
