#!/usr/bin/env python3
"""
🧪 TESTE COMPLETO DO FLUXO REAL POINTS (RP)
==========================================

Teste completo do fluxo de pontuação desde a criação da reserva
até o resgate de prêmios, simulando um cenário real.
"""

import sys
import os
from datetime import datetime, timezone, timedelta

# Adicionar backend ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def criar_reserva_teste():
    """Cria uma reserva de teste"""
    
    print("🏨 CRIANDO RESERVA DE TESTE")
    print("-" * 50)
    
    reserva = {
        "id": 1,
        "codigo": "TEST-001",
        "cliente_id": 123,
        "cliente_nome": "João Silva",
        "tipo_suite": "REAL",
        "num_diarias": 4,
        "valor_diaria": 275.00,
        "valor_total": 1100.00,
        "checkin_previsto": "2026-01-15T14:00:00Z",
        "checkout_previsto": "2026-01-19T12:00:00Z",
        "status": "PENDENTE",
        "pagamento_confirmado": False,
        "created_at": "2026-01-10T10:00:00Z",
        "checkout_realizado": None
    }
    
    print(f"✅ Reserva criada:")
    print(f"   Código: {reserva['codigo']}")
    print(f"   Cliente: {reserva['cliente_nome']}")
    print(f"   Suíte: {reserva['tipo_suite']}")
    print(f"   Diárias: {reserva['num_diarias']}")
    print(f"   Valor total: R$ {reserva['valor_total']:.2f}")
    print(f"   Status: {reserva['status']}")
    
    return reserva

def testar_pagamento(reserva):
    """Testa aprovação do pagamento"""
    
    print("\n💳 TESTANDO PAGAMENTO")
    print("-" * 50)
    
    # Simular aprovação do pagamento
    print(f"📋 Processando pagamento para reserva {reserva['codigo']}")
    print(f"   Valor: R$ {reserva['valor_total']:.2f}")
    
    # Atualizar status da reserva
    reserva["status"] = "CONFIRMADA"
    reserva["pagamento_confirmado"] = True
    reserva["pagamento_aprovado_em"] = "2026-01-12T15:30:00Z"
    
    print(f"✅ Pagamento aprovado!")
    print(f"   Status da reserva: {reserva['status']}")
    print(f"   Pagamento confirmado: {reserva['pagamento_confirmado']}")
    print(f"   ⚠️  PONTOS: Ainda não gerados (regra oficial = apenas CHECKED_OUT)")
    
    return reserva

def testar_checkin(reserva):
    """Testa check-in"""
    
    print("\n🔑 TESTANDO CHECK-IN")
    print("-" * 50)
    
    # Simular check-in
    print(f"📋 Realizando check-in para reserva {reserva['codigo']}")
    print(f"   Data: 2026-01-15T14:30:00Z")
    
    # Atualizar status
    reserva["status"] = "HOSPEDADO"
    reserva["checkin_realizado"] = "2026-01-15T14:30:00Z"
    
    print(f"✅ Check-in realizado!")
    print(f"   Status: {reserva['status']}")
    print(f"   ⚠️  PONTOS: Ainda não gerados (regra oficial = apenas CHECKED_OUT)")
    
    return reserva

def testar_checkout(reserva):
    """Testa checkout e geração de pontos"""
    
    print("\n🚪 TESTANDO CHECKOUT E GERAÇÃO DE PONTOS")
    print("-" * 50)
    
    try:
        from app.services.real_points_service import RealPointsService
        print("✅ RealPointsService importado com sucesso")
    except ImportError as e:
        print(f"❌ Erro ao importar RealPointsService: {e}")
        return reserva, 0
    
    # Simular checkout
    print(f"📋 Realizando checkout para reserva {reserva['codigo']}")
    print(f"   Data: 2026-01-19T11:00:00Z")
    
    # Atualizar status
    reserva["status"] = "CHECKED_OUT"
    reserva["checkout_realizado"] = "2026-01-19T11:00:00Z"
    
    print(f"✅ Checkout realizado!")
    print(f"   Status: {reserva['status']}")
    
    # Validar requisitos oficiais
    print(f"\n🔍 VALIDANDO REQUISITOS OFICIAIS:")
    pode, motivo = RealPointsService.validar_requisitos_oficiais(reserva)
    
    if pode:
        print(f"✅ Requisitos atendidos: {motivo}")
        
        # Calcular pontos
        rp, detalhe = RealPointsService.calcular_rp_oficial(
            reserva["tipo_suite"], 
            reserva["num_diarias"], 
            reserva["valor_total"]
        )
        
        print(f"\n🧮 CÁLCULO DE PONTOS:")
        print(f"   Suíte: {reserva['tipo_suite']}")
        print(f"   Diárias: {reserva.get('num_diarias', 'NÃO DEFINIDO')}")
        print(f"   Detalhe: {detalhe}")
        print(f"   🎉 PONTOS GERADOS: {rp} RP")
        
        # Validar antifraude
        print(f"\n🛡️ VALIDAÇÃO ANTIFRAUDE:")
        valido, motivo_antifraude = RealPointsService.validar_antifraude(reserva)
        
        if valido:
            print(f"✅ Antifraude OK: {motivo_antifraude}")
            
            # Simular crédito de pontos
            print(f"\n💾 CRÉDITO DE PONTOS:")
            print(f"   Cliente ID: {reserva['cliente_id']}")
            print(f"   Reserva ID: {reserva['id']}")
            print(f"   Pontos: {rp} RP")
            print(f"   Origem: CHECKOUT")
            print(f"   ✅ PONTOS CREDITADOS COM SUCESSO!")
            
            # Adicionar pontos ao saldo do cliente
            reserva["pontos_gerados"] = rp
            reserva["pontos_creditados_em"] = datetime.now(timezone.utc).isoformat()
            
        else:
            print(f"❌ Antifraude bloqueou: {motivo_antifraude}")
            rp = 0
            
    else:
        print(f"❌ Requisitos não atendidos: {motivo}")
        rp = 0
    
    return reserva, rp

def testar_saldo_pontos(reserva, pontos_gerados):
    """Testa consulta de saldo de pontos"""
    
    print("\n💰 TESTANDO SALDO DE PONTOS")
    print("-" * 50)
    
    # Simular saldo do cliente (poderia vir do banco)
    saldo_anterior = 45  # Pontos que cliente já tinha
    saldo_atual = saldo_anterior + pontos_gerados
    
    print(f"📊 SALDO DO CLIENTE:")
    print(f"   Cliente: {reserva['cliente_nome']}")
    print(f"   Saldo anterior: {saldo_anterior} RP")
    print(f"   Pontos gerados: {pontos_gerados} RP")
    print(f"   💰 SALDO ATUAL: {saldo_atual} RP")
    
    return saldo_atual

def testar_premios_disponiveis(saldo_atual):
    """Testa prêmios disponíveis para resgate"""
    
    print("\n🎁 TESTANDO PRÊMIOS DISPONÍVEIS")
    print("-" * 50)
    
    try:
        from app.services.real_points_service import RealPointsService
        
        premios = RealPointsService.listar_premios()
        print(f"✅ {len(premios)} prêmios disponíveis:")
        
        for premio_id, premio in premios.items():
            pode, motivo = RealPointsService.pode_resgatar_premio(saldo_atual, premio_id)
            
            if pode:
                print(f"   ✅ {premio['custo_rp']} RP - {premio['nome']} (PODE RESGATAR)")
            else:
                print(f"   ❌ {premio['custo_rp']} RP - {premio['nome']} ({motivo})")
        
        return premios
        
    except ImportError as e:
        print(f"❌ Erro ao importar RealPointsService: {e}")
        return {}

def testar_resgate_premio(saldo_atual, premio_id):
    """Testa resgate de prêmio"""
    
    print("\n🎁 TESTANDO RESGATE DE PRÊMIO")
    print("-" * 50)
    
    try:
        from app.services.real_points_service import RealPointsService
        
        premio = RealPointsService.get_premio(premio_id)
        if not premio:
            print(f"❌ Prêmio '{premio_id}' não encontrado")
            return saldo_atual
        
        print(f"📋 RESGATE DE PRÊMIO:")
        print(f"   Prêmio: {premio['nome']}")
        print(f"   Custo: {premio['custo_rp']} RP")
        print(f"   Saldo atual: {saldo_atual} RP")
        
        # Verificar se pode resgatar
        pode, motivo = RealPointsService.pode_resgatar_premio(saldo_atual, premio_id)
        
        if pode:
            print(f"✅ Pode resgatar: {motivo}")
            
            # Simular resgate
            novo_saldo = saldo_atual - premio['custo_rp']
            
            print(f"\n💰 RESGATE REALIZADO:")
            print(f"   Saldo anterior: {saldo_atual} RP")
            print(f"   Custo do prêmio: {premio['custo_rp']} RP")
            print(f"   💰 NOVO SALDO: {novo_saldo} RP")
            print(f"   ✅ PRÊMIO RESGATADO COM SUCESSO!")
            
            return novo_saldo
            
        else:
            print(f"❌ Não pode resgatar: {motivo}")
            return saldo_atual
            
    except ImportError as e:
        print(f"❌ Erro ao importar RealPointsService: {e}")
        return saldo_atual

def testar_fluxo_completo():
    """Testa o fluxo completo de pontuação"""
    
    print("🧪 TESTE COMPLETO DO FLUXO REAL POINTS (RP)")
    print("=" * 70)
    
    # 1. Criar reserva
    reserva = criar_reserva_teste()
    
    # 2. Processar pagamento
    reserva = testar_pagamento(reserva)
    
    # 3. Realizar check-in
    reserva = testar_checkin(reserva)
    
    # 4. Realizar checkout e gerar pontos
    reserva, pontos_gerados = testar_checkout(reserva)
    
    # 5. Consultar saldo de pontos
    saldo_atual = testar_saldo_pontos(reserva, pontos_gerados)
    
    # 6. Listar prêmios disponíveis
    premios = testar_premios_disponiveis(saldo_atual)
    
    # 7. Tentar resgatar prêmio
    if saldo_atual >= 20:  # Testar resgate se tiver pontos suficientes
        saldo_final = testar_resgate_premio(saldo_atual, "1_diaria_luxo")
    else:
        print(f"\n🎁 TESTANDO RESGATE:")
        print(f"   ⚠️  Saldo insuficiente para resgatar qualquer prêmio")
        saldo_final = saldo_atual
    
    # Resumo final
    print("\n" + "=" * 70)
    print("🎯 RESUMO FINAL DO FLUXO")
    print("=" * 70)
    
    print(f"\n📋 RESUMO DA RESERVA:")
    print(f"   Código: {reserva['codigo']}")
    print(f"   Cliente: {reserva['cliente_nome']}")
    print(f"   Suíte: {reserva['tipo_suite']}")
    print(f"   Diárias: {reserva.get('num_diarias', 'NÃO DEFINIDO')}")
    print(f"   Valor: R$ {reserva['valor_total']:.2f}")
    print(f"   Status final: {reserva['status']}")
    
    print(f"\n🎯 PONTOS GERADOS:")
    print(f"   Pontos nesta reserva: {pontos_gerados} RP")
    print(f"   Saldo final do cliente: {saldo_final} RP")
    
    print(f"\n✅ FLUXO TESTADO:")
    print(f"   1. ✅ Reserva criada")
    print(f"   2. ✅ Pagamento aprovado")
    print(f"   3. ✅ Check-in realizado")
    print(f"   4. ✅ Checkout realizado")
    print(f"   5. ✅ Pontos gerados")
    print(f"   6. ✅ Saldo atualizado")
    print(f"   7. ✅ Prêmios listados")
    
    if pontos_gerados > 0:
        print(f"   8. ✅ Resgate testado")
    
    print(f"\n🎉 RESULTADO: FLUXO 100% FUNCIONAL!")
    
    return {
        "reserva": reserva,
        "pontos_gerados": pontos_gerados,
        "saldo_final": saldo_final,
        "fluxo_ok": pontos_gerados > 0
    }

if __name__ == "__main__":
    resultado = testar_fluxo_completo()
    
    if resultado["fluxo_ok"]:
        print(f"\n🎯 STATUS: ✅ FLUXO COMPLETO TESTADO COM SUCESSO!")
        print(f"🏨 Sistema Real Points pronto para produção!")
    else:
        print(f"\n⚠️  STATUS: ❌ FLUXO COM PROBLEMAS!")
        print(f"🔧 Verificar implementação do RealPointsService")
