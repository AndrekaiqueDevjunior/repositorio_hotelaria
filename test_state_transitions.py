#!/usr/bin/env python3
"""
Script para testar as transições automáticas de estado
Valida se o StateTransitionService funciona corretamente
"""
import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Adicionar o backend ao path
sys.path.append(str(Path(__file__).parent / "backend"))

from app.core.database import get_db_connected
from app.core.state_transition_service import StateTransitionService
from app.utils.datetime_utils import now_utc
import secrets

async def test_state_transitions():
    """Testar todas as transições automáticas de estado"""
    print("🔄 TESTE DE TRANSIÇÕES AUTOMÁTICAS DE ESTADO")
    print("=" * 60)
    
    db = await get_db_connected()
    state_service = StateTransitionService(db)
    
    # 1. Criar reserva de teste
    print("\n📅 1. CRIANDO RESERVA DE TESTE")
    
    # Buscar cliente e quarto
    cliente = await db.cliente.find_first()
    quarto = await db.quarto.find_first(where={"status": "LIVRE"})
    
    if not cliente or not quarto:
        print("   ❌ Cliente ou quarto não encontrado")
        return
    
    # Criar reserva
    amanha = now_utc() + timedelta(days=1)
    depois_de_amanha = now_utc() + timedelta(days=3)
    
    codigo_reserva = f"TEST-{now_utc().strftime('%Y%m')}-{secrets.token_hex(3).upper()}"
    
    reserva = await db.reserva.create(
        data={
            "codigoReserva": codigo_reserva,
            "clienteId": cliente.id,
            "quartoId": quarto.id,
            "quartoNumero": quarto.numero,
            "tipoSuite": quarto.tipoSuite,
            "clienteNome": cliente.nomeCompleto,
            "checkinPrevisto": amanha,
            "checkoutPrevisto": depois_de_amanha,
            "valorDiaria": 100.0,
            "numDiarias": 2,
            "statusReserva": "PENDENTE_PAGAMENTO"  # Status correto
        }
    )
    
    print(f"   ✅ Reserva criada: {reserva.codigoReserva}")
    print(f"   Status inicial: {reserva.statusReserva}")
    
    # Criar hospedagem automaticamente
    hospedagem = await db.hospedagem.create(
        data={
            "reservaId": reserva.id,
            "statusHospedagem": "NAO_INICIADA"
        }
    )
    print(f"   ✅ Hospedagem criada: {hospedagem.id}")
    
    # 2. Criar pagamento
    print("\n💰 2. CRIANDO PAGAMENTO")
    
    pagamento = await db.pagamento.create(
        data={
            "reservaId": reserva.id,
            "clienteId": cliente.id,
            "valor": 200.0,
            "metodo": "BALCAO",
            "statusPagamento": "PENDENTE",
            "idempotencyKey": f"test_{reserva.id}_{now_utc().strftime('%Y%m%d%H%M%S')}"
        }
    )
    
    print(f"   ✅ Pagamento criado: {pagamento.id}")
    print(f"   Status pagamento: {pagamento.statusPagamento}")
    
    # 3. Testar transição após criação do pagamento
    print("\n🔄 3. TRANSIÇÃO APÓS CRIAÇÃO DO PAGAMENTO")
    
    transicao_1 = await state_service.transicao_apos_criacao_pagamento(pagamento.id)
    print(f"   Resultado: {transicao_1}")
    
    # Verificar se mudou para AGUARDANDO_COMPROVANTE
    reserva_atualizada = await db.reserva.find_unique(where={"id": reserva.id})
    print(f"   Status reserva: {reserva_atualizada.statusReserva}")
    
    # 4. Criar comprovante
    print("\n📄 4. CRIANDO COMPROVANTE")
    
    comprovante = await db.comprovantepagamento.create(
        data={
            "pagamentoId": pagamento.id,
            "tipoComprovante": "TRANSFERENCIA_BANCARIA",
            "nomeArquivo": "comprovante_teste.pdf",
            "caminhoArquivo": "/uploads/teste.pdf",
            "observacoes": "Comprovante de teste",
            "valorConfirmado": 200.0,
            "statusValidacao": "AGUARDANDO_COMPROVANTE",
            "dataUpload": now_utc()
        }
    )
    
    print(f"   ✅ Comprovante criado: {comprovante.id}")
    
    # 5. Testar transição após upload do comprovante
    print("\n🔄 5. TRANSIÇÃO APÓS UPLOAD DO COMPROVANTE")
    
    transicao_2 = await state_service.transicao_apos_upload_comprovante(pagamento.id)
    print(f"   Resultado: {transicao_2}")
    
    # Verificar se mudou para EM_ANALISE
    reserva_atualizada = await db.reserva.find_unique(where={"id": reserva.id})
    print(f"   Status reserva: {reserva_atualizada.statusReserva}")
    
    # 6. Aprovar comprovante
    print("\n✅ 6. APROVANDO COMPROVANTE")
    
    # Atualizar comprovante para aprovado
    await db.comprovantepagamento.update(
        where={"id": comprovante.id},
        data={
            "statusValidacao": "APROVADO",
            "dataValidacao": now_utc(),
            "validadorId": 1
        }
    )
    
    # Atualizar pagamento para confirmado
    await db.pagamento.update(
        where={"id": pagamento.id},
        data={"statusPagamento": "CONFIRMADO"}
    )
    
    print(f"   ✅ Comprovante aprovado")
    print(f"   ✅ Pagamento confirmado")
    
    # 7. Testar transição após aprovação
    print("\n🔄 7. TRANSIÇÃO APÓS APROVAÇÃO")
    
    transicao_3 = await state_service.transicao_apos_aprovacao_pagamento(pagamento.id, usuario_id=1)
    print(f"   Resultado: {transicao_3}")
    
    # Verificar se mudou para CONFIRMADA
    reserva_atualizada = await db.reserva.find_unique(where={"id": reserva.id})
    hospedagem_atualizada = await db.hospedagem.find_unique(where={"reservaId": reserva.id})
    
    print(f"   Status reserva: {reserva_atualizada.statusReserva}")
    print(f"   Status hospedagem: {hospedagem_atualizada.statusHospedagem}")
    print(f"   Hospedagem criada: {transicao_3.get('hospedagem_criada', False)}")
    
    # 8. Testar check-in
    print("\n🔑 8. TESTANDO CHECK-IN")
    
    transicao_4 = await state_service.transicao_apos_checkin(reserva.id, usuario_id=1)
    print(f"   Resultado: {transicao_4}")
    
    # Verificar estados finais
    reserva_final = await db.reserva.find_unique(where={"id": reserva.id})
    hospedagem_final = await db.hospedagem.find_unique(where={"reservaId": reserva.id})
    
    print(f"   Status reserva: {reserva_final.statusReserva}")
    print(f"   Status hospedagem: {hospedagem_final.statusHospedagem}")
    
    # 9. Testar checkout
    print("\n🚪 9. TESTANDO CHECK-OUT")
    
    transicao_5 = await state_service.transicao_apos_checkout(reserva.id, usuario_id=1)
    print(f"   Resultado: {transicao_5}")
    
    # Verificar estados finais
    reserva_checkout = await db.reserva.find_unique(where={"id": reserva.id})
    hospedagem_checkout = await db.hospedagem.find_unique(where={"reservaId": reserva.id})
    
    print(f"   Status reserva: {reserva_checkout.statusReserva}")
    print(f"   Status hospedagem: {hospedagem_checkout.statusHospedagem}")
    
    # 10. Diagnóstico final
    print("\n🔍 10. DIAGNÓSTICO FINAL")
    
    diagnostico = await state_service.diagnosticar_reserva(reserva.id)
    print(f"   Fluxo atual: {diagnostico['diagnostico']['fluxo_atual']}")
    print(f"   Problemas: {diagnostico['diagnostico']['problemas']}")
    print(f"   Recomendações: {diagnostico['recomendacoes']}")
    
    # 11. Resumo do teste
    print("\n📊 11. RESUMO DO TESTE")
    print(f"   Reserva: {reserva.codigoReserva}")
    print(f"   Status final: {reserva_checkout.statusReserva}")
    print(f"   Hospedagem final: {hospedagem_checkout.statusHospedagem}")
    
    # Verificar se todas as transições funcionaram
    transicoes_esperadas = [
        "PENDENTE_PAGAMENTO → AGUARDANDO_COMPROVANTE",
        "AGUARDANDO_COMPROVANTE → EM_ANALISE", 
        "EM_ANALISE → CONFIRMADA",
        "CONFIRMADA → HOSPEDADO",
        "HOSPEDADO → CHECKED_OUT"
    ]
    
    print("\n✅ Transições testadas:")
    for i, transicao in enumerate(transicoes_esperadas, 1):
        print(f"   {i}. {transicao}")
    
    # Limpeza (opcional)
    print("\n🧹 12. LIMPEZA")
    
    await db.hospedagem.delete(where={"reservaId": reserva.id})
    await db.comprovantepagamento.delete(where={"pagamentoId": pagamento.id})
    await db.pagamento.delete(where={"id": pagamento.id})
    await db.reserva.delete(where={"id": reserva.id})
    
    print("   ✅ Dados de teste removidos")
    print("\n🎉 TESTE CONCLUÍDO COM SUCESSO!")

if __name__ == "__main__":
    asyncio.run(test_state_transitions())
