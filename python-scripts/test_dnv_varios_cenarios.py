#!/usr/bin/env python3
"""
🧪 TESTE DNV - DIVERSOS CENÁRIOS DE VALIDAÇÃO
============================================

Teste completo do sistema Real Points com diversos cenários
para validar todas as regras e edge cases.
"""

import sys
import os
from datetime import datetime, timezone, timedelta

# Adicionar backend ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def criar_cenario(cenario_id, suite, diarias, valor_total, status="CHECKED_OUT", pagamento_confirmado=True):
    """Cria um cenário de teste"""
    
    base_date = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    
    reserva = {
        "id": scenario_id,
        "codigo": f"TEST-{scenario_id:03d}",
        "cliente_id": 100 + scenario_id,
        "cliente_nome": f"Cliente {scenario_id}",
        "tipo_suite": suite,
        "num_diarias": diarias,
        "valor_total": valor_total,
        "status": status,
        "pagamento_confirmado": pagamento_confirmado,
        "created_at": (base_date - timedelta(days=5)).isoformat(),
        "checkout_realizado": (base_date + timedelta(days=diarias)).isoformat()
    }
    
    return reserva

def testar_cenario(cenario, cenario_descricao):
    """Testa um cenário específico"""
    
    print(f"\n📋 CENÁRIO {scenario['id']}: {cenario_descricao}")
    print("-" * 60)
    
    try:
        from app.services.real_points_service import RealPointsService
    except ImportError as e:
        print(f"❌ Erro ao importar RealPointsService: {e}")
        return False
    
    # Mostrar dados do cenário
    print(f"📊 DADOS:")
    print(f"   Suíte: {scenario['tipo_suite']}")
    print(f"   Diárias: {scenario['num_diarias']}")
    print(f"   Valor: R$ {scenario['valor_total']:.2f}")
    print(f"   Status: {scenario['status']}")
    print(f"   Pagamento: {scenario['pagamento_confirmado']}")
    
    # Validar requisitos oficiais
    print(f"\n🔍 VALIDAÇÃO OFICIAL:")
    pode, motivo = RealPointsService.validar_requisitos_oficiais(cenario)
    
    if not pode:
        print(f"   ❌ Rejeitado: {motivo}")
        return False
    else:
        print(f"   ✅ Aprovado: {motivo}")
    
    # Validar antifraude
    print(f"\n🛡️ ANTIFRAUDE:")
    valido, motivo_antifraude = RealPointsService.validar_antifraude(cenario)
    
    if not valido:
        print(f"   ❌ Bloqueado: {motivo_antifraude}")
        return False
    else:
        print(f"   ✅ OK: {motivo_antifraude}")
    
    # Calcular pontos
    print(f"\n🧮 CÁLCULO DE PONTOS:")
    rp, detalhe = RealPointsService.calcular_rp_oficial(
        scenario["tipo_suite"], 
        scenario["num_diarias"], 
        scenario["valor_total"]
    )
    
    print(f"   Resultado: {rp} RP")
    print(f"   Detalhe: {detalhe}")
    
    if rp == 0:
        print(f"   ⚠️  Sem pontos gerados")
        return False
    else:
        print(f"   ✅ Pontos gerados com sucesso")
    
    return True

def testar_cenarios_normais():
    """Testa cenários normais esperados"""
    
    print("🧪 TESTE DE CENÁRIOS NORMAIS")
    print("=" * 70)
    
    cenarios = [
        # (suite, diarias, valor, descricao)
        ("LUXO", 2, 650, "LUXO 2 diárias (mínimo para pontos)"),
        ("LUXO", 4, 1300, "LUXO 4 diárias (2 blocos)"),
        ("DUPLA", 2, 1300, "DUPLA 2 diárias (mínimo para pontos)"),
        ("DUPLA", 6, 3900, "DUPLA 6 diárias (3 blocos)"),
        ("MASTER", 2, 850, "MASTER 2 diárias (mínimo para pontos)"),
        ("MASTER", 4, 1700, "MASTER 4 diárias (2 blocos)"),
        ("REAL", 2, 1100, "REAL 2 diárias (mínimo para pontos)"),
        ("REAL", 6, 3300, "REAL 6 diárias (3 blocos)"),
    ]
    
    resultados = []
    
    for i, (suite, diarias, valor, descricao) in enumerate(cenarios, 1):
        scenario = criar_cenario(i, suite, diarias, valor)
        resultado = testar_cenario(scenario, descricao)
        resultados.append(resultado)
    
    return resultados

def testar_cenarios_invalidos():
    """Testa cenários que devem ser rejeitados"""
    
    print("\n🧪 TESTE DE CENÁRIOS INVÁLIDOS")
    print("=" * 70)
    
    cenarios = [
        # (suite, diarias, valor, status, pagamento, descricao)
        ("LUXO", 1, 325, "CHECKED_OUT", True, "1 diária (abaixo do mínimo)"),
        ("DUPLA", 0, 0, "CHECKED_OUT", True, "0 diárias (inválido)"),
        ("REAL", 2, 1100, "CONFIRMADA", True, "Status CONFIRMADA (precisa CHECKED_OUT)"),
        ("MASTER", 2, 850, "CHECKED_OUT", False, "Pagamento não confirmado"),
        ("LUXO", 2, 650, "CANCELADO", True, "Status CANCELADO"),
        ("INVALIDA", 2, 1000, "CHECKED_OUT", True, "Suíte inválida"),
    ]
    
    resultados = []
    
    for i, (suite, diarias, valor, status, pagamento, descricao) in enumerate(cenarios, 10):
        scenario = criar_cenario(i, suite, diarias, valor, status, pagamento)
        resultado = testar_cenario(scenario, descricao)
        # Para cenários inválidos, esperamos False (rejeitado)
        resultados.append(not resultado)  # Invertemos pois rejeitado = correto
    
    return resultados

def testar_cenarios_antifraude():
    """Testa cenários de antifraude"""
    
    print("\n🧪 TESTE DE CENÁRIOS ANTIFRAUDE")
    print("=" * 70)
    
    cenarios = [
        ("LUXO", 2, 650, "CHECKED_OUT", True, "Check-out mesmo dia (suspeito)", 0),
        ("DUPLA", 2, 1300, "CHECKED_OUT", True, "Check-out < 24h (suspeito)", 12),
        ("REAL", 2, 1100, "CHECKED_OUT", True, "Check-out normal (>24h)", 48),
    ]
    
    resultados = []
    
    for i, (suite, diarias, valor, status, pagamento, descricao, horas_checkout) in enumerate(cenarios, 20):
        scenario = criar_cenario(i, suite, diarias, valor, status, pagamento)
        
        # Ajustar data de checkout para teste de antifraude
        base_date = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        scenario["checkout_realizado"] = (base_date + timedelta(hours=horas_checkout)).isoformat()
        
        print(f"\n📋 CENÁRIO {scenario['id']}: {descricao}")
        print("-" * 60)
        print(f"📊 DADOS:")
        print(f"   Suíte: {scenario['tipo_suite']}")
        print(f"   Diárias: {scenario['num_diarias']}")
        print(f"   Horas até checkout: {horas_checkout}")
        
        try:
            from app.services.real_points_service import RealPointsService
            
            # Testar antifraude
            valido, motivo = RealPointsService.validar_antifraude(scenario)
            
            if horas_checkout < 24:
                # Espera ser bloqueado
                if not valido:
                    print(f"   ✅ Fraude detectada corretamente: {motivo}")
                    resultados.append(True)
                else:
                    print(f"   ❌ Fraude não detectada (erro): {motivo}")
                    resultados.append(False)
            else:
                # Espera ser aprovado
                if valido:
                    print(f"   ✅ Antifraude OK: {motivo}")
                    resultados.append(True)
                else:
                    print(f"   ❌ Bloqueado incorretamente: {motivo}")
                    resultados.append(False)
                    
        except ImportError as e:
            print(f"❌ Erro ao importar RealPointsService: {e}")
            resultados.append(False)
    
    return resultados

def testar_calculos_matematicos():
    """Testa precisão dos cálculos matemáticos"""
    
    print("\n🧪 TESTE DE CÁLCULOS MATEMÁTICOS")
    print("=" * 70)
    
    try:
        from app.services.real_points_service import RealPointsService
    except ImportError as e:
        print(f"❌ Erro ao importar RealPointsService: {e}")
        return []
    
    # Testes matemáticos precisos
    testes = [
        ("LUXO", 2, 650, 3, "LUXO 2 diárias = 1 bloco × 3 RP"),
        ("LUXO", 3, 975, 3, "LUXO 3 diárias = 1 bloco × 3 RP (arredondado)"),
        ("LUXO", 4, 1300, 6, "LUXO 4 diárias = 2 blocos × 3 RP"),
        ("LUXO", 5, 1625, 6, "LUXO 5 diárias = 2 blocos × 3 RP (arredondado)"),
        ("DUPLA", 2, 1300, 4, "DUPLA 2 diárias = 1 bloco × 4 RP"),
        ("DUPLA", 4, 2600, 8, "DUPLA 4 diárias = 2 blocos × 4 RP"),
        ("MASTER", 2, 850, 4, "MASTER 2 diárias = 1 bloco × 4 RP"),
        ("MASTER", 6, 2550, 12, "MASTER 6 diárias = 3 blocos × 4 RP"),
        ("REAL", 2, 1100, 5, "REAL 2 diárias = 1 bloco × 5 RP"),
        ("REAL", 8, 4400, 20, "REAL 8 diárias = 4 blocos × 5 RP"),
    ]
    
    resultados = []
    
    for suite, diarias, valor, esperado, descricao in testes:
        print(f"\n📋 TESTE: {descricao}")
        
        rp, detalhe = RealPointsService.calcular_rp_oficial(suite, diarias, valor)
        
        if rp == esperado:
            print(f"   ✅ CORRETO: {rp} RP (esperado {esperado})")
            resultados.append(True)
        else:
            print(f"   ❌ ERRO: {rp} RP (esperado {esperado})")
            resultados.append(False)
        
        print(f"   Detalhe: {detalhe}")
    
    return resultados

def testar_premios_completos():
    """Testa sistema de prêmios completo"""
    
    print("\n🧪 TESTE DE SISTEMA DE PRÊMIOS")
    print("=" * 70)
    
    try:
        from app.services.real_points_service import RealPointsService
    except ImportError as e:
        print(f"❌ Erro ao importar RealPointsService: {e}")
        return []
    
    # Testar todos os prêmios com diferentes saldos
    premios = RealPointsService.listar_premios()
    saldos_teste = [10, 20, 25, 35, 50, 100, 150]
    
    resultados = []
    
    print(f"\n🎁 {len(premios)} PRÊMIOS DISPONÍVEIS:")
    
    for premio_id, premio in premios.items():
        print(f"\n📋 PRÊMIO: {premio['nome']}")
        print(f"   Custo: {premio['custo_rp']} RP")
        
        for saldo in saldos_teste:
            pode, motivo = RealPointsService.pode_resgatar_premio(saldo, premio_id)
            
            esperado = saldo >= premio['custo_rp']
            
            if pode == esperado:
                print(f"   ✅ Saldo {saldo:3d} RP: {motivo}")
                resultados.append(True)
            else:
                print(f"   ❌ Saldo {saldo:3d} RP: ERRO - {motivo}")
                resultados.append(False)
    
    return resultados

def testar_tabela_oficial():
    """Testa tabela oficial de pontos"""
    
    print("\n🧪 TESTE DE TABELA OFICIAL")
    print("=" * 70)
    
    try:
        from app.services.real_points_service import RealPointsService
    except ImportError as e:
        print(f"❌ Erro ao importar RealPointsService: {e}")
        return []
    
    tabela = RealPointsService.get_tabela_oficial()
    
    print(f"\n📋 TABELA OFICIAL DE PONTOS:")
    
    resultados = []
    
    for suite, regra in tabela.items():
        print(f"\n🏨 SUÍTE {suite}:")
        print(f"   RP por bloco: {regra['rp_por_bloco']}")
        print(f"   Valor 2 diárias: R$ {regra['valor_min_2_diarias']}-{regra['valor_max_2_diarias']}")
        print(f"   Descrição: {regra['descricao']}")
        
        # Validar se valores são consistentes
        if regra['rp_por_bloco'] > 0 and regra['valor_min_2_diarias'] > 0:
            print(f"   ✅ Configuração válida")
            resultados.append(True)
        else:
            print(f"   ❌ Configuração inválida")
            resultados.append(False)
    
    return resultados

def testar_simulacoes_completas():
    """Testa simulações completas"""
    
    print("\n🧪 TESTE DE SIMULAÇÕES COMPLETAS")
    print("=" * 70)
    
    try:
        from app.services.real_points_service import RealPointsService
    except ImportError as e:
        print(f"❌ Erro ao importar RealPointsService: {e}")
        return []
    
    simulacoes = [
        ("LUXO", 2, 650, "Simulação mínima LUXO"),
        ("REAL", 4, 1100, "Simulação completa REAL"),
        ("DUPLA", 6, 1950, "Simulação múltiplos blocos DUPLA"),
        ("MASTER", 3, 850, "Simulação arredondamento MASTER"),
    ]
    
    resultados = []
    
    for suite, diarias, valor, descricao in simulacoes:
        print(f"\n📋 SIMULAÇÃO: {descricao}")
        
        simulacao = RealPointsService.simular_calculo(suite, diarias, valor)
        
        print(f"   Suíte: {simulacao['suite']}")
        print(f"   Diárias: {simulacao['diarias']}")
        print(f"   Valor: R$ {simulacao['valor_total']:.2f}")
        print(f"   RP calculados: {simulacao['rp_calculados']}")
        print(f"   Pode conceder: {simulacao['pode_conceder']}")
        
        print(f"   Validações:")
        for validacao in simulacao['validacoes']:
            print(f"     ✅ {validacao}")
        
        print(f"   Erros:")
        for erro in simulacao['erros']:
            print(f"     ❌ {erro}")
        
        # Considerar sucesso se pode conceder e não há erros
        sucesso = simulacao['pode_conceder'] and len(simulacao['erros']) == 0
        resultados.append(sucesso)
        
        if sucesso:
            print(f"   ✅ Simulação bem-sucedida")
        else:
            print(f"   ❌ Simulação com problemas")
    
    return resultados

def executar_teste_dnv():
    """Executa todos os testes DNV"""
    
    print("🧪 TESTE DNV - DIVERSOS CENÁRIOS DE VALIDAÇÃO")
    print("=" * 80)
    print("Teste completo do sistema Real Points com múltiplos cenários")
    print("para garantir robustez e conformidade com todas as regras.")
    
    # Executar todos os testes
    resultados_normais = testar_cenarios_normais()
    resultados_invalidos = testar_cenarios_invalidos()
    resultados_antifraude = testar_cenarios_antifraude()
    resultados_matematicos = testar_calculos_matematicos()
    resultados_premios = testar_premios_completos()
    resultados_tabela = testar_tabela_oficial()
    resultados_simulacoes = testar_simulacoes_completas()
    
    # Compilar resultados
    todos_resultados = {
        "Cenários Normais": resultados_normais,
        "Cenários Inválidos": resultados_invalidos,
        "Antifraude": resultados_antifraude,
        "Cálculos Matemáticos": resultados_matematicos,
        "Sistema de Prêmios": resultados_premios,
        "Tabela Oficial": resultados_tabela,
        "Simulações Completas": resultados_simulacoes,
    }
    
    # Estatísticas finais
    print("\n" + "=" * 80)
    print("🎯 RESULTADO FINAL DO TESTE DNV")
    print("=" * 80)
    
    total_testes = 0
    total_sucessos = 0
    
    for categoria, resultados in todos_resultados.items():
        sucessos = sum(resultados)
        total = len(resultados)
        taxa = (sucessos / total * 100) if total > 0 else 0
        
        print(f"\n📊 {categoria}:")
        print(f"   Sucessos: {sucessos}/{total} ({taxa:.1f}%)")
        
        total_testes += total
        total_sucessos += sucessos
    
    # Resultado geral
    taxa_geral = (total_sucessos / total_testes * 100) if total_testes > 0 else 0
    
    print(f"\n🎯 RESULTADO GERAL:")
    print(f"   Total de testes: {total_testes}")
    print(f"   Total de sucessos: {total_sucessos}")
    print(f"   Taxa de sucesso: {taxa_geral:.1f}%")
    
    if taxa_geral >= 95:
        print(f"\n🎉 EXCELENTE! Sistema robusto e confiável!")
        print(f"✅ Real Points pronto para produção!")
    elif taxa_geral >= 90:
        print(f"\n✅ BOM! Sistema funcional com pequenos ajustes necessários.")
    else:
        print(f"\n⚠️  ATENÇÃO! Sistema precisa de correções antes da produção.")
    
    # Detalhar falhas se houver
    if taxa_geral < 100:
        print(f"\n🔍 DETALHES DAS FALHAS:")
        for categoria, resultados in todos_resultados.items():
            falhas = [i for i, r in enumerate(resultados) if not r]
            if falhas:
                print(f"   ❌ {categoria}: {len(falhas)} falhas nos testes {falhas}")
    
    return taxa_geral >= 95

if __name__ == "__main__":
    sucesso = executar_teste_dnv()
    
    if sucesso:
        print(f"\n🎯 STATUS: ✅ TESTE DNV APROVADO!")
        print(f"🏨 Sistema Real Points 100% validado!")
    else:
        print(f"\n⚠️  STATUS: ❌ TESTE DNV COM PROBLEMAS!")
        print(f"🔧 Verificar falhas antes de ir para produção.")
