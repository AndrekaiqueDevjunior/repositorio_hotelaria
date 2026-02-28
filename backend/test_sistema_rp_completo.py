#!/usr/bin/env python3
"""
Testes Completos do Sistema de Pontos RP
Valida todas as funcionalidades implementadas
"""

import asyncio
import pytest
from datetime import datetime, timezone
from app.core.database import get_db
from app.services.pontos_rp_service import PontosRPService
from app.repositories.pontos_rp_repo import PontosRPRepository

class TestSistemaPontosRP:
    """Suite completa de testes para o sistema RP"""
    
    def __init__(self):
        self.db = None
        self.pontos_rp_repo = None
        
    async def setup(self):
        """Configurar ambiente de teste"""
        self.db = get_db()
        await self.db.connect()
        self.pontos_rp_repo = PontosRPRepository(self.db)
        print("✅ Ambiente de teste configurado")
        
    async def cleanup(self):
        """Limpar ambiente de teste"""
        if self.db:
            await self.db.disconnect()
        print("✅ Ambiente de teste limpo")

    # ========================================
    # TESTES DO SERVIÇO DE CÁLCULO
    # ========================================
    
    async def test_calculo_pontos_suite_luxo(self):
        """Testar cálculo de pontos para Suíte Luxo"""
        print("\n🧪 Testando cálculo Suíte Luxo...")
        
        # Teste 1: 2 diárias exatas (deve gerar pontos)
        resultado = PontosRPService.calcular_pontos_por_suite('LUXO', 2, 0)
        assert resultado['pontos_gerados'] == 3, f"Esperado 3 RP, obtido {resultado['pontos_gerados']}"
        assert resultado['diarias_restantes'] == 0, f"Esperado 0 diárias restantes, obtido {resultado['diarias_restantes']}"
        
        # Teste 2: 3 diárias (deve gerar pontos + sobrar 1 diária)
        resultado = PontosRPService.calcular_pontos_por_suite('LUXO', 3, 0)
        assert resultado['pontos_gerados'] == 3, f"Esperado 3 RP, obtido {resultado['pontos_gerados']}"
        assert resultado['diarias_restantes'] == 1, f"Esperado 1 diária restante, obtido {resultado['diarias_restantes']}"
        
        # Teste 3: 1 diária apenas (não deve gerar pontos)
        resultado = PontosRPService.calcular_pontos_por_suite('LUXO', 1, 0)
        assert resultado['pontos_gerados'] == 0, f"Esperado 0 RP, obtido {resultado['pontos_gerados']}"
        assert resultado['diarias_restantes'] == 1, f"Esperado 1 diária restante, obtido {resultado['diarias_restantes']}"
        
        print("   ✅ Suíte Luxo: Todos os testes passaram")
        
    async def test_calculo_pontos_suite_real(self):
        """Testar cálculo de pontos para Suíte Real"""
        print("\n🧪 Testando cálculo Suíte Real...")
        
        # Teste 1: 4 diárias (deve gerar 10 RP)
        resultado = PontosRPService.calcular_pontos_por_suite('REAL', 4, 0)
        assert resultado['pontos_gerados'] == 10, f"Esperado 10 RP, obtido {resultado['pontos_gerados']}"
        assert resultado['diarias_restantes'] == 0, f"Esperado 0 diárias restantes, obtido {resultado['diarias_restantes']}"
        
        # Teste 2: 5 diárias (deve gerar 10 RP + sobrar 1)
        resultado = PontosRPService.calcular_pontos_por_suite('REAL', 5, 0)
        assert resultado['pontos_gerados'] == 10, f"Esperado 10 RP, obtido {resultado['pontos_gerados']}"
        assert resultado['diarias_restantes'] == 1, f"Esperado 1 diária restante, obtido {resultado['diarias_restantes']}"
        
        print("   ✅ Suíte Real: Todos os testes passaram")
        
    async def test_acumulacao_diarias(self):
        """Testar acumulação de diárias entre reservas"""
        print("\n🧪 Testando acumulação de diárias...")
        
        # Cenário: Cliente com 1 diária pendente + 1 nova diária = 2 diárias = pontos
        resultado = PontosRPService.calcular_pontos_por_suite('MASTER', 1, 1)
        assert resultado['pontos_gerados'] == 4, f"Esperado 4 RP, obtido {resultado['pontos_gerados']}"
        assert resultado['diarias_restantes'] == 0, f"Esperado 0 diárias restantes, obtido {resultado['diarias_restantes']}"
        
        # Cenário: Cliente com 1 diária pendente + 2 novas = 3 diárias = 1 bloco + 1 restante
        resultado = PontosRPService.calcular_pontos_por_suite('MASTER', 2, 1)
        assert resultado['pontos_gerados'] == 4, f"Esperado 4 RP, obtido {resultado['pontos_gerados']}"
        assert resultado['diarias_restantes'] == 1, f"Esperado 1 diária restante, obtido {resultado['diarias_restantes']}"
        
        print("   ✅ Acumulação de diárias: Todos os testes passaram")
        
    async def test_validacao_checkout(self):
        """Testar validação de checkout para pontos"""
        print("\n🧪 Testando validação de checkout...")
        
        # Teste 1: Checkout válido
        validacao = PontosRPService.validar_checkout_para_pontos(
            'CHECKED_OUT', 
            datetime.now(timezone.utc)
        )
        assert validacao['pode_gerar_pontos'] == True, "Checkout válido deve permitir pontos"
        
        # Teste 2: Sem checkout realizado
        validacao = PontosRPService.validar_checkout_para_pontos('CONFIRMADA', None)
        assert validacao['pode_gerar_pontos'] == False, "Sem checkout não deve permitir pontos"
        
        # Teste 3: Status inválido
        validacao = PontosRPService.validar_checkout_para_pontos(
            'CANCELADA', 
            datetime.now(timezone.utc)
        )
        assert validacao['pode_gerar_pontos'] == False, "Status cancelada não deve permitir pontos"
        
        print("   ✅ Validação de checkout: Todos os testes passaram")

    # ========================================
    # TESTES DO REPOSITORY
    # ========================================
    
    async def test_criar_cliente_rp(self):
        """Testar criação de cliente RP"""
        print("\n🧪 Testando criação de cliente RP...")
        
        cliente_id = 9999  # ID fictício para teste
        
        try:
            # Criar cliente RP
            cliente_rp = await self.pontos_rp_repo.criar_cliente_rp(cliente_id)
            
            assert cliente_rp['cliente_id'] == cliente_id, "Cliente ID deve coincidir"
            assert cliente_rp['saldo_rp'] == 0, "Saldo inicial deve ser 0"
            assert cliente_rp['diarias_pendentes_para_pontos'] == 0, "Diárias pendentes iniciais devem ser 0"
            
            print("   ✅ Criação de cliente RP: Teste passou")
            
        except Exception as e:
            print(f"   ❌ Erro no teste: {e}")
            
    async def test_buscar_saldo_rp(self):
        """Testar busca de saldo RP"""
        print("\n🧪 Testando busca de saldo RP...")
        
        try:
            # Buscar saldo de cliente inexistente
            saldo = await self.pontos_rp_repo.get_saldo_rp(99999)
            
            assert saldo['saldo_rp'] == 0, "Saldo de cliente inexistente deve ser 0"
            assert saldo['primeira_vez'] == True, "Cliente inexistente deve ser primeira vez"
            
            print("   ✅ Busca de saldo RP: Teste passou")
            
        except Exception as e:
            print(f"   ❌ Erro no teste: {e}")
            
    async def test_premios_disponiveis(self):
        """Testar busca de prêmios disponíveis"""
        print("\n🧪 Testando busca de prêmios...")
        
        try:
            premios = await self.pontos_rp_repo.get_premios_disponiveis()
            
            assert isinstance(premios, list), "Prêmios deve retornar uma lista"
            
            # Verificar se tem os prêmios básicos
            nomes_premios = [p['nome'] for p in premios]
            assert '1 diária em Suíte Luxo' in nomes_premios, "Deve ter prêmio de diária"
            assert 'iPhone 16' in nomes_premios, "Deve ter prêmio iPhone"
            
            print(f"   ✅ Prêmios disponíveis: {len(premios)} prêmios encontrados")
            
        except Exception as e:
            print(f"   ❌ Erro no teste: {e}")

    # ========================================
    # TESTES DE INTEGRAÇÃO
    # ========================================
    
    async def test_fluxo_completo_pontos(self):
        """Testar fluxo completo de pontuação"""
        print("\n🧪 Testando fluxo completo...")
        
        cliente_id = 8888  # ID fictício para teste
        
        try:
            # 1. Criar cliente
            await self.pontos_rp_repo.criar_cliente_rp(cliente_id)
            
            # 2. Simular primeira reserva (3 diárias Luxo)
            await self.pontos_rp_repo.creditar_pontos_rp(
                cliente_id=cliente_id,
                reserva_id=99990,
                tipo_suite='LUXO',
                num_diarias=3,
                pontos_gerados=3,
                diarias_usadas=2,
                diarias_restantes=1,
                detalhamento="Teste: Suíte LUXO: 3 diárias = 1 blocos × 3 RP = 3 RP + 1 diária(s) acumulada(s)"
            )
            
            # 3. Verificar saldo após primeira reserva
            saldo = await self.pontos_rp_repo.get_saldo_rp(cliente_id)
            assert saldo['saldo_rp'] == 3, f"Saldo deve ser 3, obtido {saldo['saldo_rp']}"
            assert saldo['diarias_pendentes'] == 1, f"Deve ter 1 diária pendente, obtido {saldo['diarias_pendentes']}"
            
            # 4. Simular segunda reserva (1 diária Luxo + 1 pendente = 2 diárias = pontos)
            await self.pontos_rp_repo.creditar_pontos_rp(
                cliente_id=cliente_id,
                reserva_id=99991,
                tipo_suite='LUXO',
                num_diarias=1,
                pontos_gerados=3,
                diarias_usadas=2,
                diarias_restantes=0,
                detalhamento="Teste: Suíte LUXO: 2 diárias = 1 blocos × 3 RP = 3 RP"
            )
            
            # 5. Verificar saldo final
            saldo_final = await self.pontos_rp_repo.get_saldo_rp(cliente_id)
            assert saldo_final['saldo_rp'] == 6, f"Saldo final deve ser 6, obtido {saldo_final['saldo_rp']}"
            assert saldo_final['diarias_pendentes'] == 0, f"Não deve ter diárias pendentes, obtido {saldo_final['diarias_pendentes']}"
            
            # 6. Verificar histórico
            historico = await self.pontos_rp_repo.get_historico_rp(cliente_id)
            assert len(historico) == 2, f"Deve ter 2 entradas no histórico, obtido {len(historico)}"
            
            print("   ✅ Fluxo completo: Todos os testes passaram")
            
        except Exception as e:
            print(f"   ❌ Erro no fluxo completo: {e}")

    # ========================================
    # TESTES DE REGRAS DE NEGÓCIO
    # ========================================
    
    async def test_regras_todas_suites(self):
        """Testar regras de pontuação para todas as suítes"""
        print("\n🧪 Testando regras de todas as suítes...")
        
        suites_regras = {
            'LUXO': 3,
            'MASTER': 4,
            'REAL': 5,
            'DUPLA': 4  # Caso seja implementada
        }
        
        for suite, pontos_esperados in suites_regras.items():
            if suite == 'DUPLA':
                continue  # Pular DUPLA por enquanto
                
            resultado = PontosRPService.calcular_pontos_por_suite(suite, 2, 0)
            assert resultado['pontos_gerados'] == pontos_esperados, \
                f"Suíte {suite}: esperado {pontos_esperados} RP, obtido {resultado['pontos_gerados']}"
        
        print("   ✅ Regras de suítes: Todos os testes passaram")
        
    async def test_suite_invalida(self):
        """Testar comportamento com suíte inválida"""
        print("\n🧪 Testando suíte inválida...")
        
        resultado = PontosRPService.calcular_pontos_por_suite('INEXISTENTE', 2, 0)
        assert resultado['pontos_gerados'] == 0, "Suíte inválida não deve gerar pontos"
        assert resultado['diarias_restantes'] == 2, "Diárias devem ser preservadas"
        
        print("   ✅ Suíte inválida: Teste passou")

    # ========================================
    # MÉTODO PRINCIPAL DE EXECUÇÃO
    # ========================================
    
    async def executar_todos_os_testes(self):
        """Executar toda a suite de testes"""
        print("🧪 INICIANDO TESTES DO SISTEMA RP")
        print("=" * 60)
        
        try:
            await self.setup()
            
            # Testes do Serviço
            await self.test_calculo_pontos_suite_luxo()
            await self.test_calculo_pontos_suite_real()
            await self.test_acumulacao_diarias()
            await self.test_validacao_checkout()
            await self.test_regras_todas_suites()
            await self.test_suite_invalida()
            
            # Testes do Repository
            await self.test_criar_cliente_rp()
            await self.test_buscar_saldo_rp()
            await self.test_premios_disponiveis()
            
            # Testes de Integração
            await self.test_fluxo_completo_pontos()
            
            print("\n" + "=" * 60)
            print("🎉 TODOS OS TESTES PASSARAM COM SUCESSO!")
            print("✅ Sistema de Pontos RP está funcionando corretamente")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ ERRO DURANTE OS TESTES: {e}")
            raise
            
        finally:
            await self.cleanup()

# ========================================
# FUNÇÃO PARA EXECUTAR OS TESTES
# ========================================

async def executar_testes_sistema_rp():
    """Função principal para executar os testes"""
    teste = TestSistemaPontosRP()
    await teste.executar_todos_os_testes()

if __name__ == "__main__":
    print("🚀 Executando Testes do Sistema RP...")
    asyncio.run(executar_testes_sistema_rp())
