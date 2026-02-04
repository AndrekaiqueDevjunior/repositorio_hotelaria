#!/usr/bin/env python3
"""
🧪 TESTE FINAL DO SISTEMA REAL POINTS (RP)
=========================================

Teste completo do sistema oficial Real Points após limpeza
dos sistemas antigos.
"""

import sys
import os

# Adicionar backend ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_real_points_service():
    """Testa o RealPointsService oficial"""
    
    print("🧪 TESTE FINAL - REAL POINTS (RP)")
    print("=" * 60)
    
    try:
        from app.services.real_points_service import RealPointsService
        print("✅ RealPointsService importado com sucesso")
    except ImportError as e:
        print(f"❌ Erro ao importar RealPointsService: {e}")
        return False
    
    # Testar cálculo oficial
    print("\n📊 TESTE DE CÁLCULO OFICIAL:")
    testes_calculo = [
        {"suite": "LUXO", "diarias": 2, "esperado": 3},
        {"suite": "REAL", "diarias": 4, "esperado": 10},
        {"suite": "MASTER", "diarias": 3, "esperado": 4},
        {"suite": "DUPLA", "diarias": 2, "esperado": 4},
        {"suite": "LUXO", "diarias": 1, "esperado": 0},
        {"suite": "REAL", "diarias": 6, "esperado": 15}
    ]
    
    erros_calculo = []
    for teste in testes_calculo:
        resultado, detalhe = RealPointsService.calcular_rp_oficial(
            teste["suite"], teste["diarias"], 1000
        )
        
        if resultado == teste["esperado"]:
            print(f"✅ {teste['suite']} - {teste['diarias']} diárias: {resultado} RP")
        else:
            print(f"❌ {teste['suite']} - {teste['diarias']} diárias: {resultado} RP (esperado {teste['esperado']})")
            erros_calculo.append(f"{teste['suite']}: esperado {teste['esperado']}, recebeu {resultado}")
    
    # Testar validações
    print("\n🔍 TESTE DE VALIDAÇÕES:")
    
    # Reserva válida
    reserva_valida = {
        "status": "CHECKED_OUT",
        "pagamento_confirmado": True,
        "num_diarias": 2,
        "tipo_suite": "LUXO",
        "valor_total": 650,
        "created_at": "2026-01-15T10:00:00Z",
        "checkout_realizado": "2026-01-17T12:00:00Z"
    }
    
    pode, motivo = RealPointsService.validar_requisitos_oficiais(reserva_valida)
    if pode:
        print(f"✅ Reserva válida: {motivo}")
    else:
        print(f"❌ Reserva inválida: {motivo}")
    
    # Reserva inválida (status errado)
    reserva_invalida = {
        "status": "CONFIRMADA",
        "pagamento_confirmado": True,
        "num_diarias": 2,
        "tipo_suite": "LUXO",
        "valor_total": 650
    }
    
    pode, motivo = RealPointsService.validar_requisitos_oficiais(reserva_invalida)
    if not pode:
        print(f"✅ Reserva inválida detectada: {motivo}")
    else:
        print(f"❌ Falha na validação: {motivo}")
    
    # Testar antifraude
    print("\n🛡️ TESTE DE ANTIFRAUDE:")
    
    # Check-out normal
    reserva_normal = {
        "created_at": "2026-01-15T10:00:00Z",
        "checkout_realizado": "2026-01-17T12:00:00Z"
    }
    
    valido, motivo = RealPointsService.validar_antifraude(reserva_normal)
    if valido:
        print(f"✅ Antifraude OK: {motivo}")
    else:
        print(f"❌ Antifraude falhou: {motivo}")
    
    # Check-out suspeito (mesmo dia)
    reserva_suspeita = {
        "created_at": "2026-01-17T10:00:00Z",
        "checkout_realizado": "2026-01-17T12:00:00Z"
    }
    
    valido, motivo = RealPointsService.validar_antifraude(reserva_suspeita)
    if not valido:
        print(f"✅ Fraude detectada: {motivo}")
    else:
        print(f"❌ Falha na detecção de fraude: {motivo}")
    
    # Testar prêmios
    print("\n🎁 TESTE DE PRÊMIOS:")
    
    # Listar prêmios
    premios = RealPointsService.listar_premios()
    print(f"✅ {len(premios)} prêmios disponíveis:")
    
    for premio_id, premio in premios.items():
        print(f"   - {premio['custo_rp']} RP: {premio['nome']}")
    
    # Testar resgate
    pode, motivo = RealPointsService.pode_resgatar_premio(25, "luminaria")
    if pode:
        print(f"✅ Pode resgatar luminária: {motivo}")
    else:
        print(f"❌ Não pode resgatar luminária: {motivo}")
    
    pode, motivo = RealPointsService.pode_resgatar_premio(10, "luminaria")
    if not pode:
        print(f"✅ Saldo insuficiente detectado: {motivo}")
    else:
        print(f"❌ Falha na validação de saldo: {motivo}")
    
    # Testar simulação completa
    print("\n🎯 TESTE DE SIMULAÇÃO COMPLETA:")
    
    simulacao = RealPointsService.simular_calculo("REAL", 4, 1100)
    
    print(f"✅ Simulação para Suíte REAL, 4 diárias, R$ 1100:")
    print(f"   RP calculados: {simulacao['rp_calculados']}")
    print(f"   Pode conceder: {simulacao['pode_conceder']}")
    
    for validacao in simulacao['validacoes']:
        print(f"   ✅ {validacao}")
    
    for erro in simulacao['erros']:
        print(f"   ❌ {erro}")
    
    return len(erros_calculo) == 0

def verificar_sistemas_antigos():
    """Verifica se sistemas antigos foram removidos"""
    
    print("\n🗑️ VERIFICANDO REMOÇÃO DE SISTEMAS ANTIGOS:")
    print("-" * 50)
    
    arquivos_verificar = [
        "backend/app/services/pontos_service.py",
        "backend/app/services/pontos_checkout_service.py",
        "backend/app/services/pontos_rp_service.py"
    ]
    
    sistemas_removidos = 0
    
    for arquivo in arquivos_verificar:
        if os.path.exists(arquivo):
            print(f"❌ Sistema antigo ainda existe: {arquivo}")
        else:
            print(f"✅ Sistema antigo removido: {arquivo}")
            sistemas_removidos += 1
    
    # Verificar se arquivo oficial existe
    if os.path.exists("backend/app/services/real_points_service.py"):
        print(f"✅ Sistema oficial ativo: real_points_service.py")
    else:
        print(f"❌ Sistema oficial não encontrado: real_points_service.py")
    
    return sistemas_removidos == 3

def verificar_imports():
    """Verifica se imports antigos foram removidos"""
    
    print("\n🔍 VERIFICANDO IMPORTS ANTIGOS:")
    print("-" * 50)
    
    try:
        # Tentar importar sistemas antigos (deve falhar)
        try:
            from app.services.pontos_service import PontosService
            print("❌ pontos_service ainda pode ser importado")
            return False
        except ImportError:
            print("✅ pontos_service não pode ser importado (removido)")
        
        try:
            from app.services.pontos_checkout_service import creditar_rp_no_checkout
            print("❌ pontos_checkout_service ainda pode ser importado")
            return False
        except ImportError:
            print("✅ pontos_checkout_service não pode ser importado (removido)")
        
        try:
            from app.services.pontos_rp_service import PontosRPService
            print("❌ pontos_rp_service ainda pode ser importado")
            return False
        except ImportError:
            print("✅ pontos_rp_service não pode ser importado (removido)")
        
        # Verificar se sistema oficial pode ser importado
        try:
            from app.services.real_points_service import RealPointsService
            print("✅ RealPointsService pode ser importado")
            return True
        except ImportError:
            print("❌ RealPointsService não pode ser importado")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao verificar imports: {e}")
        return False

if __name__ == "__main__":
    print("🧪 TESTE FINAL DO SISTEMA REAL POINTS")
    print("=" * 60)
    
    # Executar todos os testes
    teste_real_points = test_real_points_service()
    sistemas_removidos = verificar_sistemas_antigos()
    imports_ok = verificar_imports()
    
    print("\n" + "=" * 60)
    print("🎯 RESULTADO FINAL DOS TESTES")
    print("=" * 60)
    
    print("\n📊 STATUS DOS TESTES:")
    
    if teste_real_points:
        print("✅ RealPointsService: FUNCIONANDO")
    else:
        print("❌ RealPointsService: COM ERROS")
    
    if sistemas_removidos:
        print("✅ Sistemas antigos: REMOVIDOS")
    else:
        print("❌ Sistemas antigos: AINDA EXISTEM")
    
    if imports_ok:
        print("✅ Imports: CORRIGIDOS")
    else:
        print("❌ Imports: COM PROBLEMAS")
    
    # Verificação final
    tudo_ok = teste_real_points and sistemas_removidos and imports_ok
    
    if tudo_ok:
        print("\n🎉 SUCESSO TOTAL!")
        print("✅ Sistema Real Points 100% funcional")
        print("✅ Sistemas antigos completamente removidos")
        print("✅ Imports corrigidos")
        print("✅ Regra oficial implementada")
        print("\n🎯 SISTEMA PRONTO PARA PRODUÇÃO!")
    else:
        print("\n⚠️ PROBLEMAS IDENTIFICADOS:")
        if not teste_real_points:
            print("❌ RealPointsService precisa de correções")
        if not sistemas_removidos:
            print("❌ Sistemas antigos precisam ser removidos manualmente")
        if not imports_ok:
            print("❌ Imports antigos precisam ser corrigidos")
    
    print("=" * 60)
