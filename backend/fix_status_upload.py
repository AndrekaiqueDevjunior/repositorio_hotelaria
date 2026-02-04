#!/usr/bin/env python3
"""
Script para corrigir status de reservas para permitir upload de comprovante
"""

import asyncio
from app.core.database import get_db
from app.schemas.status_enums import StatusReserva

async def fix_reserva_status():
    """Corrige status da reserva 27 e outras para permitir upload de comprovante"""
    db = get_db()
    await db.connect()
    
    # Buscar reserva 27
    reserva = await db.reserva.find_unique(where={"id": 27})
    
    if reserva:
        print(f"Reserva 27 encontrada:")
        print(f"  Status atual: {reserva.statusReserva}")
        print(f"  Código: {getattr(reserva, 'codigo_reserva', 'N/A')}")
        
        # Verificar se o status é válido
        status_validos = [
            StatusReserva.PENDENTE_PAGAMENTO.value,
            StatusReserva.AGUARDANDO_COMPROVANTE.value
        ]
        
        if reserva.statusReserva not in status_validos:
            print(f"  Status inválido para upload! Alterando para AGUARDANDO_COMPROVANTE...")
            
            # Atualizar para status que permite upload
            await db.reserva.update(
                where={"id": 27},
                data={"statusReserva": StatusReserva.AGUARDANDO_COMPROVANTE.value}
            )
            
            print(f"  ✓ Status alterado para: {StatusReserva.AGUARDANDO_COMPROVANTE.value}")
            
            # Verificar se existe pagamento
            pagamento = await db.pagamento.find_first(where={"reservaId": 27})
            if not pagamento:
                print(f"  Criando pagamento para reserva...")
                pagamento = await db.pagamento.create({
                    "reservaId": 27,
                    "clienteId": reserva.clienteId,
                    "metodo": "DINHEIRO",
                    "valor": getattr(reserva, 'valor_previsto', 0) or 0,
                    "observacao": "Pagamento no balcão",
                    "status": "PENDENTE"
                })
                print(f"  ✓ Pagamento criado: ID {pagamento.id}")
            else:
                print(f"  Pagamento já existe: ID {pagamento.id}, Status: {pagamento.status}")
        else:
            print(f"  Status já é válido para upload!")
    else:
        print("Reserva 27 não encontrada!")
    
    # Listar todas as reservas com status inválidos
    print("\nVerificando outras reservas com status problemáticos...")
    reservas = await db.reserva.find_many(
        where={
            "statusReserva": {
                "notIn": [
                    StatusReserva.PENDENTE_PAGAMENTO.value,
                    StatusReserva.AGUARDANDO_COMPROVANTE.value,
                    StatusReserva.EM_ANALISE.value,
                    StatusReserva.PAGA_APROVADA.value,
                    StatusReserva.PAGA_REJEITADA.value,
                    StatusReserva.CHECKIN_LIBERADO.value,
                    StatusReserva.CHECKIN_REALIZADO.value,
                    StatusReserva.CHECKOUT_REALIZADO.value,
                    StatusReserva.CANCELADA.value,
                    StatusReserva.NO_SHOW.value
                ]
            }
        }
    )
    
    if reservas:
        print(f"\nEncontradas {len(reservas)} reservas com status inválidos:")
        for r in reservas:
            print(f"  ID: {r.id} | Status: {r.statusReserva} | Código: {getattr(r, 'codigo_reserva', 'N/A')}")
    else:
        print("\n✓ Nenhuma reserva com status inválido encontrado!")
    
    await db.disconnect()

if __name__ == "__main__":
    asyncio.run(fix_reserva_status())
