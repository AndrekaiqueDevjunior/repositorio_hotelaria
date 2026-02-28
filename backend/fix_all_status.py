#!/usr/bin/env python3
"""
Script para corrigir todos os status de reservas para os novos valores da enum
"""

import asyncio
from app.core.database import get_db
from app.schemas.status_enums import StatusReserva

async def fix_all_status():
    """Corrige todos os status de reservas para usar os valores corretos da enum"""
    db = get_db()
    await db.connect()
    
    # Mapeamento de status antigos para novos
    status_mapping = {
        "PENDENTE": StatusReserva.PENDENTE_PAGAMENTO.value,
        "CANCELADO": StatusReserva.CANCELADA.value,
        "CHECKED_OUT": StatusReserva.CHECKOUT_REALIZADO.value,
        "CHECKED_IN": StatusReserva.CHECKIN_REALIZADO.value,
        "HOSPEDADO": StatusReserva.CHECKIN_REALIZADO.value,
        "CONFIRMADA": StatusReserva.PAGA_APROVADA.value,
        "FINALIZADA": StatusReserva.CHECKOUT_REALIZADO.value,
    }
    
    # Buscar todas as reservas
    reservas = await db.reserva.find_many()
    
    print(f"Verificando {len(reservas)} reservas...")
    print("=" * 60)
    
    corrigidas = 0
    
    for reserva in reservas:
        status_atual = reserva.statusReserva
        
        # Verificar se precisa corrigir
        if status_atual in status_mapping:
            novo_status = status_mapping[status_atual]
            
            if status_atual != novo_status:
                print(f"ID: {reserva.id}")
                print(f"  Código: {getattr(reserva, 'codigo_reserva', 'N/A')}")
                print(f"  Status antigo: {status_atual}")
                print(f"  Status novo: {novo_status}")
                
                # Atualizar status
                await db.reserva.update(
                    where={"id": reserva.id},
                    data={"statusReserva": novo_status}
                )
                
                print(f"  ✓ Corrigido!")
                print()
                corrigidas += 1
        else:
            # Verificar se já é um status válido
            status_validos = [s.value for s in StatusReserva]
            if status_atual not in status_validos:
                print(f"ID: {reserva.id} - Status desconhecido: {status_atual}")
                # Mudar para status padrão
                await db.reserva.update(
                    where={"id": reserva.id},
                    data={"statusReserva": StatusReserva.PENDENTE_PAGAMENTO.value}
                )
                print(f"  ✓ Alterado para PENDENTE_PAGAMENTO (status desconhecido)")
                print()
                corrigidas += 1
    
    print("=" * 60)
    print(f"Total de reservas corrigidas: {corrigidas}")
    
    # Verificar resultado final
    print("\nVerificando status finais...")
    status_count = {}
    
    for reserva in await db.reserva.find_many():
        status = reserva.statusReserva
        status_count[status] = status_count.get(status, 0) + 1
    
    print("Distribuição de status:")
    for status, count in sorted(status_count.items()):
        print(f"  {status}: {count}")
    
    await db.disconnect()

if __name__ == "__main__":
    asyncio.run(fix_all_status())
