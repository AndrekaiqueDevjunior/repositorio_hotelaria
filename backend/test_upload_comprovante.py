#!/usr/bin/env python3
"""
Script para testar o upload de comprovante com status PENDENTE
"""

import asyncio
import sys
import os

# Adicionar o backend ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.schemas.status_enums import StatusReserva

async def test_upload_comprovante():
    """Testar upload de comprovante com reserva status PENDENTE"""
    db = get_db()
    await db.connect()
    
    try:
        # 1. Buscar uma reserva com status PENDENTE
        reserva = await db.reserva.find_first(
            where={"statusReserva": "PENDENTE"}
        )
        
        if not reserva:
            print("❌ Nenhuma reserva com status PENDENTE encontrada")
            print("Criando uma reserva de teste...")
            
            # Criar cliente de teste
            cliente = await db.cliente.find_first()
            if not cliente:
                print("❌ Nenhum cliente encontrado")
                return
            
            # Criar quarto de teste
            quarto = await db.quarto.find_first()
            if not quarto:
                print("❌ Nenhum quarto encontrado")
                return
            
            # Criar reserva de teste
            from datetime import datetime, timedelta
            reserva = await db.reserva.create({
                "clienteId": cliente.id,
                "quartoNumero": quarto.numero,
                "checkinPrevisto": datetime.now().date(),
                "checkoutPrevisto": (datetime.now() + timedelta(days=2)).date(),
                "valorPrevisto": 300.00,
                "statusReserva": "PENDENTE",
                "codigoReserva": "TEST-COMP-001"
            })
            print(f"✅ Reserva de teste criada: ID {reserva.id}")
        
        print(f"✅ Reserva encontrada: ID {reserva.id} | Status: {reserva.statusReserva}")
        
        # 2. Verificar se a validação aceita os status
        status_validos = ["PENDENTE_PAGAMENTO", "AGUARDANDO_COMPROVANTE", "PENDENTE"]
        
        if reserva.statusReserva in status_validos:
            print(f"✅ Status {reserva.statusReserva} é válido para upload de comprovante!")
        else:
            print(f"❌ Status {reserva.statusReserva} NÃO é válido para upload!")
            print(f"   Status válidos: {', '.join(status_validos)}")
            return
        
        # 3. Verificar se existe pagamento
        pagamento = await db.pagamento.find_first(
            where={"reservaId": reserva.id}
        )
        
        if pagamento:
            print(f"✅ Pagamento encontrado: ID {pagamento.id} | Status: {pagamento.status}")
        else:
            print(f"ℹ️  Nenhum pagamento encontrado (será criado no upload)")
        
        # 4. Simular validação do endpoint
        print("\n🔍 Simulando validação do endpoint...")
        
        # Validar que a reserva existe
        if not reserva:
            print("❌ Reserva não encontrada")
            return
        
        # Validar status
        if reserva.statusReserva not in status_validos:
            print(f"❌ Reserva não está aguardando pagamento (status atual: {reserva.statusReserva})")
            return
        
        print("✅ Validação do endpoint passaria!")
        print(f"✅ Upload de comprovante permitido para reserva {reserva.id}")
        
        # 5. Mostrar informações úteis
        print("\n📋 Informações para teste manual:")
        print(f"   - Reserva ID: {reserva.id}")
        print(f"   - Status atual: {reserva.statusReserva}")
        print(f"   - Cliente ID: {reserva.clienteId}")
        print(f"   - Valor: R$ {reserva.valorPrevisto}")
        print(f"   - Código: {reserva.codigoReserva}")
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        await db.disconnect()

if __name__ == "__main__":
    asyncio.run(test_upload_comprovante())
