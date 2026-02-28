#!/usr/bin/env python3
"""
Script para corrigir inconsistência de status dos quartos
Atualiza o status do quarto baseado nas reservas ativas
"""

import asyncio
from app.core.database import get_db
from app.utils.datetime_utils import now_utc

async def corrigir_status_quartos():
    """Corrige o status de todos os quartos baseado nas reservas ativas"""
    print("🔧 CORRIGINDO STATUS DOS QUARTOS...")
    print("=" * 50)
    
    db = get_db()
    await db.connect()
    
    # Buscar todos os quartos
    quartos = await db.quarto.find_many()
    
    quartos_corrigidos = []
    
    for quarto in quartos:
        print(f"\n📍 Analisando Quarto {quarto.numero} ({quarto.tipoSuite})")
        print(f"   Status atual: {quarto.status}")
        
        # Buscar reservas ativas do quarto
        reservas_ativas = await db.reserva.find_many(
            where={
                'quartoNumero': quarto.numero,
                'status': {'in': ['PENDENTE', 'CONFIRMADA', 'HOSPEDADO']}
            },
            order={'checkinPrevisto': 'asc'}
        )
        
        # Determinar o status correto
        novo_status = 'LIVRE'
        motivo = ''
        
        if reservas_ativas:
            # Verificar se há alguém hospedado agora
            agora = now_utc()
            
            for reserva in reservas_ativas:
                if reserva.status == 'HOSPEDADO':
                    # Se está hospedado, quarto está OCUPADO
                    novo_status = 'OCUPADO'
                    motivo = f'Hóspede ativo (reserva {reserva.codigoReserva})'
                    break
                elif reserva.status == 'CONFIRMADA':
                    # Se há reserva confirmada, quarto está RESERVADO
                    if reserva.checkinPrevisto <= agora <= reserva.checkoutPrevisto:
                        novo_status = 'RESERVADO'
                        motivo = f'Reserva confirmada ativa (reserva {reserva.codigoReserva})'
                        break
                elif reserva.status == 'PENDENTE':
                    # Se há reserva pendente no período, quarto está RESERVADO
                    if reserva.checkinPrevisto <= agora <= reserva.checkoutPrevisto:
                        novo_status = 'RESERVADO'
                        motivo = f'Reserva pendente ativa (reserva {reserva.codigoReserva})'
                        break
                    elif reserva.checkinPrevisto > agora:
                        # Se reserva futura, quarto está RESERVADO
                        novo_status = 'RESERVADO'
                        motivo = f'Reserva futura (reserva {reserva.codigoReserva})'
                        break
        
        # Atualizar status se necessário
        if quarto.status != novo_status:
            print(f"   ⚠️  STATUS INCORRETO!")
            print(f"   📝 Corrigindo: {quarto.status} → {novo_status}")
            print(f"   📄 Motivo: {motivo}")
            
            # Atualizar no banco
            await db.quarto.update(
                where={'id': quarto.id},
                data={'status': novo_status}
            )
            
            quartos_corrigidos.append({
                'numero': quarto.numero,
                'status_antigo': quarto.status,
                'status_novo': novo_status,
                'motivo': motivo
            })
        else:
            print(f"   ✅ Status correto")
    
    print("\n" + "=" * 50)
    print(f"🎉 CORREÇÃO CONCLUÍDA!")
    print(f"📊 Quartos corrigidos: {len(quartos_corrigidos)}")
    
    if quartos_corrigidos:
        print("\n📋 DETALHE DAS CORREÇÕES:")
        for correcao in quartos_corrigidos:
            print(f"   • Quarto {correcao['numero']}: {correcao['status_antigo']} → {correcao['status_novo']}")
            print(f"     Motivo: {correcao['motivo']}")
    else:
        print("\n✅ Nenhum quarto precisou de correção")
    
    await db.disconnect()

if __name__ == "__main__":
    asyncio.run(corrigir_status_quartos())
