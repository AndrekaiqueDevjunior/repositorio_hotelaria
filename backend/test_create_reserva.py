import asyncio
import json
from datetime import datetime
from prisma import Client

async def test_create_reserva():
    db = Client()
    await db.connect()
    
    try:
        # Verificar quarto 102
        quarto = await db.quarto.find_unique(where={'numero': '102'})
        print(f"Quarto 102: {quarto.numero} - {quarto.tipoSuite} - {quarto.status}")
        
        # Criar reserva diretamente no banco
        import uuid
        
        codigo_reserva = str(uuid.uuid4())[:8].upper()
        valor_total = 350.0 * 2  # 2 diárias
        
        reserva = await db.reserva.create({
            'codigoReserva': codigo_reserva,
            'clienteId': 1,
            'quartoNumero': '102',
            'tipoSuite': 'LUXO',
            'checkinPrevisto': datetime(2026, 1, 10, 14, 0, 0),
            'checkoutPrevisto': datetime(2026, 1, 12, 11, 0, 0),
            'valorDiaria': 350.0,
            'numDiarias': 2,
            'clienteNome': 'João Teste',
            'status': 'PENDENTE'
        })
        
        print(f"✅ Reserva criada: {reserva.codigoReserva}")
        print(f"   ID: {reserva.id}")
        print(f"   Quarto: {reserva.quartoNumero}")
        print(f"   Status: {reserva.status}")
        print(f"   Valor total: R$ {reserva.valorDiaria * reserva.numDiarias}")
        
        # Verificar status do quarto após reserva
        quarto_atualizado = await db.quarto.find_unique(where={'numero': '102'})
        print(f"Status do quarto após reserva: {quarto_atualizado.status}")
        
        # Verificar se quarto ainda aparece como disponível (não deveria)
        from app.core.validators import QuartoValidator
        from datetime import date
        
        checkin = date(2026, 1, 10)
        checkout = date(2026, 1, 12)
        
        try:
            await QuartoValidator.validar_disponibilidade('102', checkin, checkout, db)
            print("❌ ERRO: Quarto ainda aparece como disponível (deveria estar ocupado)")
        except Exception as e:
            print(f"✅ Correto: Quarto não está mais disponível - {e.detail}")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
    finally:
        await db.disconnect()

if __name__ == "__main__":
    asyncio.run(test_create_reserva())
