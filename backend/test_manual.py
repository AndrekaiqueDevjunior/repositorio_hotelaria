"""
Script manual para testar funcionalidades básicas do CRUD
Execute: python test_manual.py
"""
import asyncio
import sys
from datetime import datetime, timedelta

# Adicionar o diretório atual ao path
sys.path.insert(0, '.')

async def test_basico():
    """Teste básico de conexão e operações"""
    try:
        from app.core.database import get_db, connect_db, disconnect_db
        from app.repositories.cliente_repo import ClienteRepository
        from app.repositories.quarto_repo import QuartoRepository
        from app.repositories.reserva_repo import ReservaRepository
        from app.services.reserva_service import ReservaService
        from app.schemas.reserva_schema import ReservaCreate
        
        print("=" * 60)
        print("TESTE MANUAL - CRUD DE RESERVAS")
        print("=" * 60)
        
        # Conectar ao banco
        print("\n1. Conectando ao banco de dados...")
        await connect_db()
        db = get_db()
        print("✅ Conectado!")
        
        # Criar cliente de teste
        print("\n2. Criando cliente de teste...")
        cliente = await db.cliente.create(
            data={
                "nomeCompleto": "Cliente Teste Manual",
                "documento": f"TESTE{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "telefone": "21999999999",
                "email": "teste@teste.com"
            }
        )
        print(f"✅ Cliente criado: ID {cliente.id} - {cliente.nomeCompleto}")
        
        # Criar quarto de teste
        print("\n3. Criando quarto de teste...")
        quarto = await db.quarto.create(
            data={
                "numero": f"TEST{datetime.now().strftime('%H%M%S')}",
                "tipoSuite": "LUXO",
                "status": "LIVRE"
            }
        )
        print(f"✅ Quarto criado: {quarto.numero} - {quarto.tipoSuite}")
        
        # Criar reserva
        print("\n4. Criando reserva...")
        checkin = datetime.now() + timedelta(days=1)
        checkout = datetime.now() + timedelta(days=3)
        
        reserva_repo = ReservaRepository(db)
        reserva_data = ReservaCreate(
            cliente_id=cliente.id,
            quarto_numero=quarto.numero,
            tipo_suite="LUXO",
            checkin_previsto=checkin,
            checkout_previsto=checkout,
            valor_diaria=150.00,
            num_diarias=2
        )
        
        reserva = await reserva_repo.create(reserva_data)
        print(f"✅ Reserva criada: ID {reserva['id']} - Status: {reserva['status']}")
        print(f"   Código: {reserva['codigo_reserva']}")
        print(f"   Valor Total: R$ {reserva['valor_total']:.2f}")
        
        # Check-in
        print("\n5. Realizando check-in...")
        reserva_checkin = await reserva_repo.checkin(reserva['id'])
        print(f"✅ Check-in realizado!")
        print(f"   Status: {reserva_checkin['status']}")
        print(f"   Check-in realizado em: {reserva_checkin['checkin_realizado']}")
        
        # Verificar quarto
        quarto_atualizado = await db.quarto.find_unique(where={"numero": quarto.numero})
        print(f"   Quarto status: {quarto_atualizado.status}")
        
        # Check-out
        print("\n6. Realizando check-out...")
        reserva_checkout = await reserva_repo.checkout(reserva['id'])
        print(f"✅ Check-out realizado!")
        print(f"   Status: {reserva_checkout['status']}")
        print(f"   Check-out realizado em: {reserva_checkout['checkout_realizado']}")
        
        # Verificar quarto
        quarto_final = await db.quarto.find_unique(where={"numero": quarto.numero})
        print(f"   Quarto status: {quarto_final.status}")
        
        # Limpar dados de teste
        print("\n7. Limpando dados de teste...")
        await db.reserva.delete(where={"id": reserva['id']})
        await db.cliente.delete(where={"id": cliente.id})
        await db.quarto.delete(where={"id": quarto.id})
        print("✅ Dados limpos!")
        
        print("\n" + "=" * 60)
        print("✅ TODOS OS TESTES PASSARAM!")
        print("=" * 60)
        
        await disconnect_db()
        
    except Exception as e:
        print(f"\nERRO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_basico())

