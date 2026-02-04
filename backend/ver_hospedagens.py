"""
Script para visualizar hospedagens e verificar redundâncias
"""
import asyncio
from prisma import Prisma


async def ver_hospedagens():
    """Visualiza hospedagens e analisa redundâncias"""
    print("🔍 Verificando hospedagens e redundâncias...\n")
    
    db = Prisma()
    await db.connect()
    
    try:
        # Buscar todas as hospedagens com reservas
        hospedagens = await db.hospedagem.find_many(
            include={
                'reserva': {
                    'include': {
                        'pagamentos': True
                    }
                }
            }
        )
        
        print(f"📊 Total de hospedagens: {len(hospedagens)}\n")
        print("="*80)
        
        # Analisar cada hospedagem
        for h in hospedagens:
            r = h.reserva
            
            print(f"\n🏨 Hospedagem #{h.id}")
            print(f"   Reserva: {r.codigoReserva} - {r.clienteNome}")
            print(f"   Quarto: {r.tipoSuite} - {r.quartoNumero}")
            
            # ANÁLISE DE REDUNDÂNCIA
            print(f"\n   📊 ESTADOS:")
            print(f"   • Reserva.status_reserva: {r.status_reserva}")
            print(f"   • Reserva.status (legacy): {r.status}")
            print(f"   • Hospedagem.status_hospedagem: {h.statusHospedagem}")
            
            # Verificar se há pagamentos
            if r.pagamentos:
                pag = r.pagamentos[0]
                print(f"   • Pagamento.status: {pag.status}")
                if pag.statusPagamento:
                    print(f"   • Pagamento.status_pagamento: {pag.statusPagamento}")
            
            # ANÁLISE DE DATAS
            print(f"\n   📅 DATAS:")
            print(f"   • Check-in previsto: {r.checkinPrevisto}")
            print(f"   • Check-out previsto: {r.checkoutPrevisto}")
            
            # Verificar redundância de datas
            if r.checkinReal or r.checkoutReal:
                print(f"\n   ⚠️ REDUNDÂNCIA DETECTADA:")
                if r.checkinReal:
                    print(f"   • Reserva.checkin_real: {r.checkinReal}")
                if h.checkinRealizadoEm:
                    print(f"   • Hospedagem.checkin_realizado_em: {h.checkinRealizadoEm}")
                if r.checkoutReal:
                    print(f"   • Reserva.checkout_real: {r.checkoutReal}")
                if h.checkoutRealizadoEm:
                    print(f"   • Hospedagem.checkout_realizado_em: {h.checkoutRealizadoEm}")
            else:
                if h.checkinRealizadoEm:
                    print(f"   • Hospedagem.checkin_realizado_em: {h.checkinRealizadoEm}")
                if h.checkoutRealizadoEm:
                    print(f"   • Hospedagem.checkout_realizado_em: {h.checkoutRealizadoEm}")
            
            print(f"\n   👥 DADOS OPERACIONAIS:")
            print(f"   • Hóspedes: {h.numHospedes or 'N/A'}")
            print(f"   • Crianças: {h.numCriancas or 'N/A'}")
            print(f"   • Placa: {h.placaVeiculo or 'N/A'}")
            
            print("="*80)
        
        # RESUMO DE REDUNDÂNCIAS
        print("\n\n📋 ANÁLISE DE REDUNDÂNCIAS:\n")
        
        print("1️⃣ CAMPOS DUPLICADOS (Reserva vs Hospedagem):")
        print("   ⚠️ checkin_real (Reserva) ↔ checkin_realizado_em (Hospedagem)")
        print("   ⚠️ checkout_real (Reserva) ↔ checkout_realizado_em (Hospedagem)")
        print("   📌 RECOMENDAÇÃO: Usar APENAS campos de Hospedagem")
        
        print("\n2️⃣ CAMPOS DUPLICADOS (Status):")
        print("   ⚠️ Reserva.status (legacy) ↔ Reserva.status_reserva (novo)")
        print("   ⚠️ Pagamento.status (legacy) ↔ Pagamento.status_pagamento (novo)")
        print("   📌 RECOMENDAÇÃO: Migrar gradualmente para novos campos")
        
        print("\n3️⃣ CAMPOS ÚNICOS (Sem redundância):")
        print("   ✅ Hospedagem.status_hospedagem (único)")
        print("   ✅ Hospedagem.num_hospedes (único)")
        print("   ✅ Hospedagem.num_criancas (único)")
        print("   ✅ Hospedagem.placa_veiculo (único)")
        print("   ✅ Hospedagem.checkin_realizado_por (único)")
        print("   ✅ Hospedagem.checkout_realizado_por (único)")
        
        print("\n4️⃣ ESTRATÉGIA DE MIGRAÇÃO:")
        print("   📝 FASE 1 (Atual): Manter campos legacy por compatibilidade")
        print("   📝 FASE 2: Atualizar código para usar novos campos")
        print("   📝 FASE 3: Deprecar campos legacy")
        print("   📝 FASE 4: Remover campos legacy (após 100% migração)")
        
        print("\n5️⃣ CAMPOS A MANTER:")
        print("   ✅ Reserva.checkin_real / checkout_real → Manter temporariamente")
        print("   ✅ Reserva.status → Manter temporariamente")
        print("   ✅ Pagamento.status → Manter temporariamente")
        print("   📌 Motivo: Compatibilidade com código existente")
        
        print("\n6️⃣ CAMPOS A USAR NO CÓDIGO NOVO:")
        print("   ✅ Hospedagem.checkin_realizado_em (fonte primária)")
        print("   ✅ Hospedagem.checkout_realizado_em (fonte primária)")
        print("   ✅ Hospedagem.status_hospedagem (fonte primária)")
        print("   ✅ Reserva.status_reserva (fonte primária)")
        print("   ✅ Pagamento.status_pagamento (fonte primária)")
        
        print("\n✅ Análise concluída!")
        
    finally:
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(ver_hospedagens())
