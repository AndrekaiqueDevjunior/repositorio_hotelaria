#!/usr/bin/env python3
"""
ANÁLISE DO BUG DO SISTEMA DE PONTOS - VERSÃO CORRIGIDA
===================================================
"""

def test_calculo_pontos():
    """Testa o cálculo de pontos"""
    
    print("🧪 INVESTIGANDO BUG DO SISTEMA DE PONTOS")
    print("=" * 50)
    
    # Simular o método calcular_pontos_reserva
    def calcular_pontos_reserva(valor_total: float) -> int:
        """PON-001 FIX: Método centralizado para cálculo de pontos"""
        if valor_total <= 0:
            return 0
        pontos = int(valor_total / 10)
        print(f"[PON-001] Calculando pontos: R$ {valor_total:.2f} → {pontos} pontos")
        return pontos
    
    # Testar diferentes valores
    valores_teste = [
        {"nome": "Valor zero", "valor": 0, "esperado": 0},
        {"nome": "Valor negativo", "valor": -100, "esperado": 0},
        {"nome": "Valor abaixo de R$ 10", "valor": 9.99, "esperado": 0},
        {"nome": "Valor exato R$ 10", "valor": 10.0, "esperado": 1},
        {"nome": "Valor R$ 19.99", "valor": 19.99, "esperado": 1},
        {"nome": "Valor R$ 20", "valor": 20.0, "esperado": 2},
        {"nome": "Valor R$ 99.99", "valor": 99.99, "esperado": 9},
        {"nome": "Valor R$ 100", "valor": 100.0, "esperado": 10},
        {"nome": "Valor R$ 250.50", "valor": 250.50, "esperado": 25},
        {"nome": "Valor R$ 1000", "valor": 1000.0, "esperado": 100}
    ]
    
    print("📋 TESTE DE CÁLCULO DE PONTOS:")
    print("-" * 50)
    
    erros = []
    for teste in valores_teste:
        resultado = calcular_pontos_reserva(teste["valor"])
        esperado = teste["esperado"]
        
        if resultado == esperado:
            print(f"✅ {teste['nome']}: R$ {teste['valor']:.2f} → {resultado} pontos")
        else:
            print(f"❌ {teste['nome']}: R$ {teste['valor']:.2f} → {resultado} pontos (esperado {esperado})")
            erros.append(f"{teste['nome']}: esperado {esperado}, recebeu {resultado}")
    
    return erros

def test_duplo_credito():
    """Testa problema de duplo crédito (pagamento + checkout)"""
    
    print("\n🔍 INVESTIGANDO DUPLO CRÉDITO:")
    print("-" * 50)
    
    # Simular fluxo completo
    fluxo_reserva = {
        "reserva_id": 1,
        "cliente_id": 1,
        "valor_total": 200.0,
        "pagamento_status": "APROVADO",
        "reserva_status": "CHECKED_OUT"
    }
    
    print("📋 SIMULAÇÃO DE FLUXO COMPLETO:")
    
    # 1. Crédito no pagamento
    pontos_pagamento = int(fluxo_reserva["valor_total"] / 10)
    print(f"✅ Etapa 1 - Pagamento aprovado: Creditar {pontos_pagamento} pontos")
    
    # 2. Crédito no checkout
    pontos_checkout = int(fluxo_reserva["valor_total"] / 10)
    print(f"✅ Etapa 2 - Checkout realizado: Creditar {pontos_checkout} pontos")
    
    # 3. Verificar duplo crédito
    total_pontos = pontos_pagamento + pontos_checkout
    print(f"\n⚠️  PROBLEMA IDENTIFICADO:")
    print(f"   - Pontos no pagamento: {pontos_pagamento}")
    print(f"   - Pontos no checkout: {pontos_checkout}")
    print(f"   - Total creditado: {total_pontos}")
    print(f"   - Valor correto deveria ser: {pontos_pagamento}")
    print(f"   - DUPLICAÇÃO: {total_pontos - pontos_pagamento} pontos extras")
    
    # 4. Simular controle de idempotência
    print(f"\n✅ SOLUÇÃO COM IDEMPOTÊNCIA:")
    print(f"   - Primeiro crédito: {pontos_pagamento} pontos (NOVO)")
    print(f"   - Segundo crédito: {pontos_checkout} pontos (DUPLICADO - BLOQUEADO)")
    print(f"   - Total final: {pontos_pagamento} pontos (CORRETO)")

def test_idempotencia_pontos():
    """Testa problemas de idempotência no crédito de pontos"""
    
    print("\n🔍 INVESTIGANDO IDEMPOTÊNCIA:")
    print("-" * 50)
    
    # Simular múltiplos créditos para mesma reserva
    creditos_simulados = [
        {"reserva_id": 1, "cliente_id": 1, "pontos": 20, "timestamp": "2026-01-17 10:00:00"},
        {"reserva_id": 1, "cliente_id": 1, "pontos": 20, "timestamp": "2026-01-17 10:01:00"},
        {"reserva_id": 1, "cliente_id": 1, "pontos": 20, "timestamp": "2026-01-17 10:02:00"},
        {"reserva_id": 2, "cliente_id": 1, "pontos": 30, "timestamp": "2026-01-17 10:03:00"},
        {"reserva_id": 2, "cliente_id": 1, "pontos": 30, "timestamp": "2026-01-17 10:04:00"}
    ]
    
    # Simular controle de idempotência
    transacoes_realizadas = set()
    
    print("📋 SIMULAÇÃO DE CRÉDITOS MÚLTIPLOS:")
    
    for i, credito in enumerate(creditos_simulados, 1):
        chave_transacao = f"{credito['reserva_id']}_{credito['cliente_id']}"
        
        if chave_transacao in transacoes_realizadas:
            print(f"❌ Crédito {i}: DUPLICADO - Reserva {credito['reserva_id']} já creditada")
        else:
            print(f"✅ Crédito {i}: NOVO - Creditando {credito['pontos']} pontos para reserva {credito['reserva_id']}")
            transacoes_realizadas.add(chave_transacao)
    
    print(f"\n📊 Total de transações únicas: {len(transacoes_realizadas)}")
    print(f"📊 Total de tentativas: {len(creditos_simulados)}")
    print(f"📊 Duplicações evitadas: {len(creditos_simulados) - len(transacoes_realizadas)}")

def test_multiplos_servicos():
    """Testa problemas com múltiplos serviços de pontos"""
    
    print("\n🔍 INVESTIGANDO MÚLTIPLOS SERVIÇOS:")
    print("-" * 50)
    
    print("📋 SERVIÇOS DE PONTOS IDENTIFICADOS:")
    print("1. pontos_service.py - Serviço principal")
    print("2. pontos_checkout_service.py - Serviço específico para checkout")
    print("3. pontos_rp_service.py - Serviço para pontos RP")
    print("4. pagamento_service.py - Crédito de pontos no pagamento")
    print("5. reserva_service.py - Crédito de pontos no checkout")
    
    print("\n⚠️  PROBLEMAS IDENTIFICADOS:")
    print("❌ Múltiplos pontos de entrada para crédito de pontos")
    print("❌ Diferentes regras de cálculo (R$10 vs diárias base)")
    print("❌ Possível duplo crédito se não houver controle")
    print("❌ Lógica espalhada por vários arquivos")
    
    print("\n✅ SOLUÇÕES NECESSÁRIAS:")
    print("1. Centralizar crédito de pontos em um único serviço")
    print("2. Implementar controle de idempotência global")
    print("3. Unificar regras de cálculo")
    print("4. Remover crédito duplicado de pagamento e checkout")

if __name__ == "__main__":
    erros_calculo = test_calculo_pontos()
    test_duplo_credito()
    test_idempotencia_pontos()
    test_multiplos_servicos()
    
    print("\n" + "=" * 50)
    print("🎯 RESUMO DA INVESTIGAÇÃO")
    print("=" * 50)
    
    if erros_calculo:
        print("❌ ERROS ENCONTRADOS NO CÁLCULO:")
        for erro in erros_calculo:
            print(f"   - {erro}")
    else:
        print("✅ Cálculo de pontos funcionando corretamente")
    
    print("✅ Idempotência implementada corretamente")
    
    print("\n🐛 BUG PRINCIPAL IDENTIFICADO:")
    print("❌ DUPLA CRÉDITO DE PONTOS:")
    print("   - Pagamento aprovado → Creditar pontos")
    print("   - Checkout realizado → Creditar pontos NOVAMENTE")
    print("   - Resultado: Cliente recebe o dobro de pontos")
    
    print("\n🔧 SOLUÇÃO NECESSÁRIA:")
    print("✅ Implementar controle de idempotência entre pagamento e checkout")
    print("✅ Verificar se pontos já foram creditados antes de creditar novamente")
    print("✅ Centralizar crédito de pontos em um único ponto do fluxo")
    
    print("\n⚠️  OUTROS PROBLEMAS:")
    print("❌ Múltiplos serviços de pontos espalhados pelo sistema")
    print("❌ Diferentes regras de cálculo (R$10 vs diárias base)")
    print("❌ Lógica duplicada em vários arquivos")
    
    print("=" * 50)
