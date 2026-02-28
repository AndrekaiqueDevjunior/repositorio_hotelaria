#!/usr/bin/env python3
"""
Script para testar criação de pagamento e fluxo de comprovante
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

async def test_payment_flow():
    """Testar fluxo completo de pagamento e comprovante"""
    print("💳 TESTE DE FLUXO DE PAGAMENTO")
    print("=" * 50)
    
    db = await get_db_connected()
    
    # 1. Buscar a reserva criada anteriormente
    print("\n📅 1. BUSCANDO RESERVA RCF-202601-E5356E")
    reserva = await db.reserva.find_unique(where={"codigoReserva": "RCF-202601-E5356E"})
    
    if not reserva:
        print("   ❌ Reserva não encontrada")
        return
    
    print(f"   ✅ Reserva encontrada:")
    print(f"   - ID: {reserva.id}")
    print(f"   - Status: {reserva.statusReserva}")
    print(f"   - Valor diária: R$ {reserva.valorDiaria}")
    print(f"   - Diárias: {reserva.numDiarias}")
    
    # 2. Criar pagamento
    print("\n💰 2. CRIANDO PAGAMENTO")
    
    valor_total = float(reserva.valorDiaria) * reserva.numDiarias
    print(f"   Valor total: R$ {valor_total}")
    
    try:
        pagamento = await db.pagamento.create(
            data={
                "reservaId": reserva.id,
                "clienteId": reserva.clienteId,
                "valor": valor_total,
                "metodo": "BALCAO",  # Pagamento em balcão (precisa comprovante)
                "statusPagamento": "PENDENTE",
                "idempotencyKey": f"pag_{reserva.id}_{now_utc().strftime('%Y%m%d%H%M%S')}"
            }
        )
        
        print(f"   ✅ Pagamento criado:")
        print(f"   - ID: {pagamento.id}")
        print(f"   - Valor: R$ {pagamento.valor}")
        print(f"   - Método: {pagamento.metodo}")
        print(f"   - Status: {pagamento.statusPagamento}")
        
    except Exception as e:
        print(f"   ❌ Erro ao criar pagamento: {e}")
        return
    
    # 3. Verificar status da reserva após pagamento
    print("\n📊 3. STATUS APÓS PAGAMENTO")
    reserva_atualizada = await db.reserva.find_unique(where={"id": reserva.id})
    print(f"   Status Reserva: {reserva_atualizada.statusReserva}")
    
    # 4. Verificar se a reserva deveria mudar de status
    print("\n🔍 4. ANÁLISE DE TRANSIÇÃO DE STATUS")
    
    if reserva_atualizada.statusReserva == "PENDENTE":
        print("   ⚠️ GAP IDENTIFICADO: Reserva continua PENDENTE após criação de pagamento")
        print("   💡 Sugestão: Reserva deveria mudar para AGUARDANDO_COMPROVANTE")
    
    # 5. Simular upload de comprovante
    print("\n📄 5. SIMULANDO UPLOAD DE COMPROVANTE")
    
    try:
        from datetime import datetime
        comprovante = await db.comprovantepagamento.create(
            data={
                "pagamentoId": pagamento.id,
                "tipoComprovante": "TRANSFERENCIA_BANCARIA",
                "nomeArquivo": "comprovante_teste.pdf",
                "caminhoArquivo": "/uploads/comprovantes/teste.pdf",
                "observacoes": "Comprovante de teste",
                "valorConfirmado": valor_total,
                "statusValidacao": "AGUARDANDO_COMPROVANTE",
                "dataUpload": now_utc()
            }
        )
        
        print(f"   ✅ Comprovante criado:")
        print(f"   - ID: {comprovante.id}")
        print(f"   - Status Validação: {comprovante.statusValidacao}")
        print(f"   - Valor: R$ {comprovante.valorConfirmado}")
        
    except Exception as e:
        print(f"   ❌ Erro ao criar comprovante: {e}")
        return
    
    # 6. Verificar status após upload do comprovante
    print("\n📊 6. STATUS APÓS UPLOAD DO COMPROVANTE")
    
    # Atualizar pagamento para PENDENTE (upload feito)
    await db.pagamento.update(
        where={"id": pagamento.id},
        data={"statusPagamento": "PENDENTE", "updatedAt": now_utc()}
    )
    
    # Verificar se a reserva mudou de status
    reserva_apos_upload = await db.reserva.find_unique(where={"id": reserva.id})
    print(f"   Status Reserva: {reserva_apos_upload.statusReserva}")
    
    if reserva_apos_upload.statusReserva == "PENDENTE":
        print("   ⚠️ GAP IDENTIFICADO: Reserva continua PENDENTE após upload de comprovante")
        print("   💡 Sugestão: Reserva deveria mudar para AGUARDANDO_COMPROVANTE ou EM_ANALISE")
    
    # 7. Simular aprovação do comprovante
    print("\n✅ 7. SIMULANDO APROVAÇÃO DO COMPROVANTE")
    
    try:
        # Aprovar comprovante
        comprovante_aprovado = await db.comprovantepagamento.update(
            where={"id": comprovante.id},
            data={
                "statusValidacao": "APROVADO",
                "dataValidacao": now_utc(),
                "validadorId": 1,  # Admin
                "observacoesInternas": "Aprovado automaticamente em teste"
            }
        )
        
        # Aprovar pagamento
        pagamento_aprovado = await db.pagamento.update(
            where={"id": pagamento.id},
            data={
                "statusPagamento": "CONFIRMADO",
                "updatedAt": now_utc()
            }
        )
        
        print(f"   ✅ Comprovante aprovado: {comprovante_aprovado.statusValidacao}")
        print(f"   ✅ Pagamento aprovado: {pagamento_aprovado.statusPagamento}")
        
    except Exception as e:
        print(f"   ❌ Erro ao aprovar: {e}")
        return
    
    # 8. Verificar status final da reserva
    print("\n🏆 8. STATUS FINAL DA RESERVA")
    
    reserva_final = await db.reserva.find_unique(where={"id": reserva.id})
    print(f"   Status Reserva: {reserva_final.statusReserva}")
    
    if reserva_final.statusReserva == "PENDENTE":
        print("   ❌ GAP CRÍTICO: Reserva continua PENDENTE mesmo após pagamento aprovado!")
        print("   💡 Reserva deveria estar CONFIRMADA para permitir check-in")
    elif reserva_final.statusReserva == "CONFIRMADA":
        print("   ✅ Status correto: CONFIRMADA (pode fazer check-in)")
    else:
        print(f"   ⚠️ Status inesperado: {reserva_final.statusReserva}")
    
    # 9. Verificar se hospedagem foi criada
    print("\n🛏️ 9. VERIFICANDO HOSPEDAGEM")
    hospedagem = await db.hospedagem.find_unique(where={"reservaId": reserva.id})
    
    if hospedagem:
        print(f"   ✅ Hospedagem encontrada: {hospedagem.statusHospedagem}")
    else:
        print("   ❌ Hospedagem não encontrada")
        print("   💡 Hospedagem deveria ser criada na confirmação da reserva")
    
    # 10. Resumo dos gaps encontrados
    print("\n🔍 10. RESUMO DOS GAPS")
    gaps = []
    
    if reserva_atualizada.statusReserva == "PENDENTE":
        gaps.append("❌ Reserva não muda de status após criação de pagamento")
    
    if reserva_apos_upload.statusReserva == "PENDENTE":
        gaps.append("❌ Reserva não muda de status após upload de comprovante")
    
    if reserva_final.statusReserva != "CONFIRMADA":
        gaps.append("❌ Reserva não fica CONFIRMADA após aprovação do pagamento")
    
    if not hospedagem:
        gaps.append("❌ Hospedagem não é criada na confirmação")
    
    if gaps:
        print("   Gaps encontrados no fluxo:")
        for gap in gaps:
            print(f"   {gap}")
    else:
        print("   ✅ Fluxo de pagamento funcionando corretamente")
    
    # 11. Próximos passos
    print("\n🔄 11. PRÓXIMOS PASSOS")
    if reserva_final.statusReserva == "CONFIRMADA" and hospedagem:
        print("   ✅ Reserva pronta para check-in!")
        print("   Para testar o check-in:")
        print("   1. Acessar frontend")
        print("   2. Fazer check-in da reserva")
        print("   3. Verificar se status muda para HOSPEDADO")
        print("   4. Verificar se botão checkout aparece")
    else:
        print("   ❌ Corrigir os gaps antes de testar check-in")

if __name__ == "__main__":
    asyncio.run(test_payment_flow())
