"""
Script para testar fluxo de status do quarto
"""
import asyncio
from prisma import Prisma

async def testar_fluxo():
    db = Prisma()
    await db.connect()
    
    print("\n" + "="*60)
    print("🧪 TESTE: Fluxo de Status do Quarto")
    print("="*60)
    
    # Buscar uma reserva CONFIRMADA para testar
    reserva = await db.reserva.find_first(
        where={"status": "CONFIRMADA"},
        include={"hospedagem": True}
    )
    
    if not reserva:
        print("\n❌ Nenhuma reserva CONFIRMADA encontrada para testar")
        print("💡 Crie uma reserva e faça o pagamento primeiro")
        return
    
    print(f"\n📋 Reserva selecionada: #{reserva.id}")
    print(f"   Cliente: {reserva.clienteNome}")
    print(f"   Quarto: {reserva.quartoNumero}")
    print(f"   Status Reserva: {reserva.status}")
    
    # Verificar status atual do quarto
    quarto = await db.quarto.find_unique(where={"numero": reserva.quartoNumero})
    print(f"\n🏨 Status atual do quarto: {quarto.status}")
    
    # Verificar hospedagem
    if reserva.hospedagem:
        print(f"🛏️  Status hospedagem: {reserva.hospedagem.statusHospedagem}")
    else:
        print("⚠️  Hospedagem não encontrada (será criada no check-in)")
    
    print("\n" + "-"*60)
    print("📊 ANÁLISE DO FLUXO:")
    print("-"*60)
    
    # Verificar consistência
    if reserva.status == "CONFIRMADA":
        if quarto.status == "LIVRE":
            print("✅ CORRETO: Reserva confirmada, quarto ainda LIVRE")
        else:
            print(f"❌ ERRO: Reserva confirmada mas quarto está {quarto.status}")
    
    elif reserva.status == "HOSPEDADO":
        if quarto.status == "OCUPADO":
            print("✅ CORRETO: Check-in realizado, quarto OCUPADO")
        else:
            print(f"❌ ERRO: Check-in realizado mas quarto está {quarto.status}")
    
    elif reserva.status == "CHECKED_OUT":
        if quarto.status == "LIVRE":
            print("✅ CORRETO: Checkout realizado, quarto LIVRE")
        else:
            print(f"❌ ERRO: Checkout realizado mas quarto está {quarto.status}")
    
    # Buscar todas as reservas e verificar inconsistências
    print("\n" + "-"*60)
    print("🔍 VERIFICANDO INCONSISTÊNCIAS NO BANCO:")
    print("-"*60)
    
    # Quartos OCUPADOS sem hóspede
    quartos_ocupados = await db.quarto.find_many(where={"status": "OCUPADO"})
    for q in quartos_ocupados:
        reserva_ativa = await db.reserva.find_first(
            where={
                "quartoNumero": q.numero,
                "status": "HOSPEDADO"
            }
        )
        if not reserva_ativa:
            print(f"❌ INCONSISTÊNCIA: Quarto {q.numero} está OCUPADO mas sem hóspede")
    
    # Quartos LIVRE com hóspede
    reservas_hospedadas = await db.reserva.find_many(
        where={"status": "HOSPEDADO"}
    )
    for r in reservas_hospedadas:
        quarto_reserva = await db.quarto.find_unique(where={"numero": r.quartoNumero})
        if quarto_reserva and quarto_reserva.status != "OCUPADO":
            print(f"❌ INCONSISTÊNCIA: Reserva #{r.id} está HOSPEDADA mas quarto {r.quartoNumero} está {quarto_reserva.status}")
    
    print("\n" + "="*60)
    print("✅ Teste concluído!")
    print("="*60 + "\n")
    
    await db.disconnect()

if __name__ == "__main__":
    asyncio.run(testar_fluxo())
