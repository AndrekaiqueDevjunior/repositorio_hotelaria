#!/usr/bin/env python3
"""
Script para testar o sistema de notificações
Cria uma reserva de teste e verifica se a notificação foi criada
"""
import asyncio
from datetime import datetime, timedelta
from app.core.database import get_db, connect_db, disconnect_db
from app.repositories.reserva_repo import ReservaRepository
from app.schemas.reserva_schema import ReservaCreate

async def test():
    await connect_db()
    db = get_db()
    
    print("\n=== TESTE DO SISTEMA DE NOTIFICAÇÕES ===\n")
    
    # Verificar clientes e quartos disponíveis
    clientes = await db.cliente.find_many(take=1)
    quartos = await db.quarto.find_many(take=1)
    
    if not clientes:
        print("❌ Nenhum cliente encontrado. Execute seed_5_users.py primeiro.")
        await disconnect_db()
        return
    
    if not quartos:
        print("❌ Nenhum quarto encontrado. Crie quartos primeiro.")
        await disconnect_db()
        return
    
    cliente = clientes[0]
    quarto = quartos[0]
    
    print(f"✅ Cliente: {cliente.nomeCompleto}")
    print(f"✅ Quarto: {quarto.numero}\n")
    
    # Contar notificações antes
    notifs_antes = await db.notificacao.count()
    print(f"📊 Notificações antes: {notifs_antes}")
    
    # Criar reserva de teste
    reserva_repo = ReservaRepository(db)
    
    try:
        checkin = datetime.now() + timedelta(days=1)
        checkout = checkin + timedelta(days=3)
        
        reserva_data = ReservaCreate(
            cliente_id=cliente.id,
            quarto_numero=quarto.numero,
            tipo_suite=quarto.tipoSuite,
            checkin_previsto=checkin,
            checkout_previsto=checkout,
            valor_diaria=250.0,
            num_diarias=3
        )
        
        print(f"\n🔄 Criando reserva de teste...")
        reserva = await reserva_repo.create(reserva_data)
        print(f"✅ Reserva criada: {reserva['codigo_reserva']}")
        
    except Exception as e:
        print(f"❌ Erro ao criar reserva: {e}")
        await disconnect_db()
        return
    
    # Contar notificações depois
    notifs_depois = await db.notificacao.count()
    print(f"\n📊 Notificações depois: {notifs_depois}")
    
    if notifs_depois > notifs_antes:
        print(f"✅ SUCESSO! {notifs_depois - notifs_antes} notificação(ões) criada(s)!\n")
        
        # Listar notificações criadas
        notifs = await db.notificacao.find_many(
            order={"dataCriacao": "desc"},
            take=5
        )
        
        print("📋 Últimas notificações:")
        for n in notifs:
            print(f"  - {n.titulo}")
            print(f"    Tipo: {n.tipo} | Categoria: {n.categoria} | Perfil: {n.perfil}")
            print(f"    Mensagem: {n.mensagem}")
            print()
    else:
        print("❌ FALHA! Nenhuma notificação foi criada.")
        print("   O sistema de notificações não está funcionando corretamente.")
    
    await disconnect_db()

if __name__ == "__main__":
    asyncio.run(test())
