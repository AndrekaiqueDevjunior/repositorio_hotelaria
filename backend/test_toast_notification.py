#!/usr/bin/env python3
"""
Script para testar o sistema de toast notifications
Cria uma nova reserva e verifica se a notificação é criada
"""
import asyncio
from datetime import datetime, timedelta
from app.core.database import get_db, connect_db, disconnect_db
from app.repositories.reserva_repo import ReservaRepository
from app.schemas.reserva_schema import ReservaCreate

async def test():
    await connect_db()
    db = get_db()
    
    print("\n=== TESTE DO SISTEMA DE TOAST NOTIFICATIONS ===\n")
    
    # Buscar cliente e quarto disponíveis (sem reservas ativas)
    clientes = await db.cliente.find_many(take=1)
    
    # Buscar quarto que não tem reservas ativas
    quartos = await db.quarto.find_many(where={"status": "LIVRE"})
    
    # Filtrar quartos sem reservas ativas
    quarto_disponivel = None
    for q in quartos:
        reservas_ativas = await db.reserva.find_many(
            where={
                "quartoNumero": q.numero,
                "status": {"in": ["PENDENTE", "HOSPEDADO"]}
            }
        )
        if not reservas_ativas:
            quarto_disponivel = q
            break
    
    quartos = [quarto_disponivel] if quarto_disponivel else []
    
    if not clientes or not quartos:
        print("❌ Dados insuficientes. Execute seed_5_users.py e seed_quartos.py")
        await disconnect_db()
        return
    
    cliente = clientes[0]
    quarto = quartos[0]
    
    print(f"📋 Cliente: {cliente.nomeCompleto}")
    print(f"🏨 Quarto: {quarto.numero} ({quarto.tipoSuite})\n")
    
    # Contar notificações antes
    notifs_antes = await db.notificacao.count()
    print(f"📊 Notificações no banco ANTES: {notifs_antes}")
    
    # Criar reserva
    reserva_repo = ReservaRepository(db)
    
    try:
        checkin = datetime.now() + timedelta(days=2)
        checkout = checkin + timedelta(days=3)
        
        reserva_data = ReservaCreate(
            cliente_id=cliente.id,
            quarto_numero=quarto.numero,
            tipo_suite=quarto.tipoSuite,
            checkin_previsto=checkin,
            checkout_previsto=checkout,
            valor_diaria=300.0,
            num_diarias=3
        )
        
        print(f"🔄 Criando nova reserva...")
        reserva = await reserva_repo.create(reserva_data)
        print(f"✅ Reserva criada: {reserva['codigo_reserva']}\n")
        
    except Exception as e:
        print(f"❌ Erro ao criar reserva: {e}")
        await disconnect_db()
        return
    
    # Contar notificações depois
    notifs_depois = await db.notificacao.count()
    print(f"📊 Notificações no banco DEPOIS: {notifs_depois}")
    
    if notifs_depois > notifs_antes:
        print(f"✅ SUCESSO! {notifs_depois - notifs_antes} notificação(ões) criada(s)!\n")
        
        # Mostrar última notificação
        ultima_notif = await db.notificacao.find_first(
            order={"dataCriacao": "desc"}
        )
        
        if ultima_notif:
            print("📬 Última notificação criada:")
            print(f"   Título: {ultima_notif.titulo}")
            print(f"   Mensagem: {ultima_notif.mensagem}")
            print(f"   Tipo: {ultima_notif.tipo}")
            print(f"   Categoria: {ultima_notif.categoria}")
            print(f"   Perfil: {ultima_notif.perfil}")
            print(f"   Lida: {ultima_notif.lida}")
            print()
            print("🎉 O toast deve aparecer no frontend em até 10 segundos!")
            print("   (Para usuários ADMIN ou RECEPCAO logados)")
    else:
        print("❌ FALHA! Nenhuma notificação foi criada.")
    
    await disconnect_db()

if __name__ == "__main__":
    asyncio.run(test())
