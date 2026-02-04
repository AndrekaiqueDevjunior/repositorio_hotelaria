#!/usr/bin/env python3
import asyncio
from app.core.database import get_db, connect_db, disconnect_db

async def check():
    await connect_db()
    db = get_db()
    
    print("\n=== VERIFICANDO FOREIGN KEYS DE NOTIFICAÇÕES ===\n")
    
    # Buscar notificações com relacionamentos
    notifs = await db.notificacao.find_many(
        include={
            'reserva': True,
            'pagamento': True
        },
        order={'dataCriacao': 'desc'}
    )
    
    print(f"📊 Total de notificações: {len(notifs)}\n")
    
    for n in notifs:
        print(f"📬 {n.titulo}")
        print(f"   Tipo: {n.tipo} | Categoria: {n.categoria}")
        print(f"   Perfil: {n.perfil} | Lida: {n.lida}")
        
        if n.reserva:
            print(f"   ✅ FK Reserva: {n.reserva.codigoReserva} (ID: {n.reservaId})")
        elif n.reservaId:
            print(f"   ⚠️  FK Reserva: ID {n.reservaId} (reserva não encontrada)")
        else:
            print(f"   ➖ Sem FK de Reserva")
        
        if n.pagamento:
            print(f"   ✅ FK Pagamento: ID {n.pagamento.id} - R$ {float(n.pagamento.valor):.2f}")
        elif n.pagamentoId:
            print(f"   ⚠️  FK Pagamento: ID {n.pagamentoId} (pagamento não encontrado)")
        else:
            print(f"   ➖ Sem FK de Pagamento")
        
        print()
    
    # Verificar integridade
    print("=" * 60)
    print("🔍 VERIFICAÇÃO DE INTEGRIDADE:")
    print("=" * 60)
    
    notifs_com_reserva = [n for n in notifs if n.reservaId]
    notifs_com_pagamento = [n for n in notifs if n.pagamentoId]
    
    print(f"✅ Notificações com FK de Reserva: {len(notifs_com_reserva)}")
    print(f"✅ Notificações com FK de Pagamento: {len(notifs_com_pagamento)}")
    print(f"✅ Notificações sem FK: {len(notifs) - len(notifs_com_reserva) - len(notifs_com_pagamento)}")
    
    # Verificar se todas as FKs são válidas
    fks_invalidas = 0
    for n in notifs:
        if n.reservaId and not n.reserva:
            fks_invalidas += 1
            print(f"❌ FK inválida: Notificação {n.id} referencia reserva {n.reservaId} que não existe")
        if n.pagamentoId and not n.pagamento:
            fks_invalidas += 1
            print(f"❌ FK inválida: Notificação {n.id} referencia pagamento {n.pagamentoId} que não existe")
    
    if fks_invalidas == 0:
        print("\n✅ Todas as Foreign Keys estão válidas!")
    else:
        print(f"\n⚠️  {fks_invalidas} FK(s) inválida(s) encontrada(s)")
    
    await disconnect_db()

if __name__ == "__main__":
    asyncio.run(check())
