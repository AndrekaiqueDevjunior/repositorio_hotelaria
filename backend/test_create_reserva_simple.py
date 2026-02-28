#!/usr/bin/env python3
"""
Script simplificado para testar criação de reserva do zero
"""
import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Adicionar o backend ao path
sys.path.append(str(Path(__file__).parent / "backend"))

from app.core.database import get_db_connected
from app.utils.datetime_utils import now_utc
import secrets

async def test_fluxo_completo():
    """Testar fluxo completo de criação de reserva"""
    print("🔍 TESTE SIMPLIFICADO - CRIAÇÃO DE RESERVA")
    print("=" * 50)
    
    db = await get_db_connected()
    
    # 1. Verificar clientes
    print("\n📋 1. CLIENTES")
    clientes = await db.cliente.find_many()
    print(f"   Encontrados: {len(clientes)}")
    
    if not clientes:
        # Criar cliente de teste
        cliente = await db.cliente.create({
            "nomeCompleto": "CLIENTE TESTE",
            "email": "teste@exemplo.com",
            "telefone": "21999999999",
            "documento": "12345678901",
            "dataNascimento": datetime(1990, 1, 1),
            "nacionalidade": "Brasil"
        })
        print(f"   ✅ Cliente criado: ID {cliente.id}")
    else:
        cliente = clientes[0]
        print(f"   ✅ Usando cliente: ID {cliente.id} - {cliente.nomeCompleto}")
    
    # 2. Verificar quartos
    print("\n🏨 2. QUARTOS")
    quartos = await db.quarto.find_many()
    quarto_disponivel = None
    
    for q in quartos:
        print(f"   - Quarto {q.numero}: {q.tipoSuite} - {q.status}")
        if q.status == "LIVRE" and not quarto_disponivel:
            quarto_disponivel = q
    
    if not quarto_disponivel:
        print("   ❌ Nenhum quarto disponível")
        return
    
    print(f"   ✅ Usando quarto: {quarto_disponivel.numero}")
    
    # 3. Criar reserva
    print("\n📅 3. CRIANDO RESERVA")
    
    amanha = now_utc() + timedelta(days=1)
    depois_de_amanha = now_utc() + timedelta(days=3)
    
    tentativa = 0
    reserva = None
    
    while tentativa < 5:
        tentativa += 1
        codigo_reserva = f"RCF-{now_utc().strftime('%Y%m')}-{secrets.token_hex(3).upper()}"
        
        try:
            reserva = await db.reserva.create(
                data={
                    "codigoReserva": codigo_reserva,
                    "clienteId": cliente.id,
                    "quartoId": quarto_disponivel.id,
                    "quartoNumero": quarto_disponivel.numero,
                    "tipoSuite": quarto_disponivel.tipoSuite,
                    "clienteNome": cliente.nomeCompleto,
                    "checkinPrevisto": amanha,
                    "checkoutPrevisto": depois_de_amanha,
                    "valorDiaria": 100.0,
                    "numDiarias": 2,
                    "statusReserva": "PENDENTE"
                }
            )
            break
        except Exception as e:
            print(f"   Tentativa {tentativa}: {e}")
            reserva = None
    
    if not reserva:
        print("   ❌ Falha ao criar reserva")
        return
    
    print(f"   ✅ Reserva criada!")
    print(f"   - ID: {reserva.id}")
    print(f"   - Código: {reserva.codigoReserva}")
    print(f"   - Status: {reserva.statusReserva}")
    print(f"   - Check-in: {reserva.checkinPrevisto.strftime('%d/%m/%Y')}")
    print(f"   - Check-out: {reserva.checkoutPrevisto.strftime('%d/%m/%Y')}")
    
    # 4. Verificar hospedagem
    print("\n🛏️ 4. HOSPEDAGEM")
    hospedagem = await db.hospedagem.find_unique(where={"reservaId": reserva.id})
    
    if hospedagem:
        print(f"   ✅ Hospedagem encontrada:")
        print(f"   - ID: {hospedagem.id}")
        print(f"   - Status: {hospedagem.statusHospedagem}")
    else:
        print(f"   ❌ Hospedagem NÃO encontrada")
        print(f"   🔍 GAP IDENTIFICADO: Hospedagem não é criada automaticamente")
    
    # 5. Verificar pagamentos
    print("\n💳 5. PAGAMENTOS")
    pagamentos = await db.pagamento.find_many(where={"reservaId": reserva.id})
    print(f"   Pagamentos: {len(pagamentos)}")
    
    for p in pagamentos:
        print(f"   - ID {p.id}: R$ {p.valor} - {p.statusPagamento}")
    
    # 6. Análise de status
    print("\n📊 6. ANÁLISE DE STATUS")
    print(f"   Status Reserva: {reserva.statusReserva}")
    print(f"   Status Hospedagem: {hospedagem.statusHospedagem if hospedagem else 'NÃO CRIADA'}")
    print(f"   Quantidade Pagamentos: {len(pagamentos)}")
    
    # 7. Gaps identificados
    print("\n🔍 7. GAPS IDENTIFICADOS")
    gaps = []
    
    if not hospedagem:
        gaps.append("❌ Hospedagem não criada automaticamente")
    
    if reserva.statusReserva == "PENDENTE":
        gaps.append("⚠️ Status 'PENDENTE' - deveria ser 'PENDENTE_PAGAMENTO'?")
    
    if len(pagamentos) == 0:
        gaps.append("⚠️ Nenhum pagamento criado (esperado para nova reserva)")
    
    if gaps:
        print("   Gaps encontrados:")
        for gap in gaps:
            print(f"   {gap}")
    else:
        print("   ✅ Nenhum gap encontrado")
    
    # 8. Próximos passos
    print("\n🔄 8. PRÓXIMOS PASSOS")
    print(f"   Para testar o fluxo completo da reserva {reserva.codigoReserva}:")
    print("   1. Criar pagamento")
    print("   2. Upload de comprovante")
    print("   3. Validar comprovante")
    print("   4. Verificar status CONFIRMADA")
    print("   5. Criar hospedagem (se necessário)")
    print("   6. Fazer check-in")
    print("   7. Verificar status HOSPEDADO")

if __name__ == "__main__":
    asyncio.run(test_fluxo_completo())
