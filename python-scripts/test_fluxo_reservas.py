#!/usr/bin/env python3
"""
TESTE COMPLETO DO FLUXO DE RESERVAS
==================================
Verifica se o fluxo implementado funciona corretamente
Simula todas as etapas: Criar → Pagar → Check-in → Checkout
"""

import asyncio
import sys
import os

# Adicionar backend ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.unified_state_validator import UnifiedStateValidator
from app.services.fluxo_reserva_service import FluxoReservaService
from app.schemas.status_enums import StatusReserva, StatusPagamento


class MockDatabase:
    """Mock do banco de dados para testes"""
    
    def __init__(self):
        self.reservas = {}
        self.pagamentos = {}
        self.hospedagens = {}
        self.next_id = 1
    
    def query(self, table):
        return MockQuery(self, table)


class MockQuery:
    """Mock de query para simulação"""
    
    def __init__(self, db, table):
        self.db = db
        self.table = table
    
    def filter(self, **kwargs):
        # Simulação de filtro
        return self
    
    def first(self):
        # Simulação de primeiro resultado
        return None


class TestFluxoReservas:
    """Teste completo do fluxo de reservas"""
    
    def __init__(self):
        self.db = MockDatabase()
        self.validator = UnifiedStateValidator()
        self.service = FluxoReservaService(self.db)
        self.test_results = []
    
    def log_test(self, test_name, success, message, data=None):
        """Registra resultado do teste"""
        result = {
            'test': test_name,
            'success': success,
            'message': message,
            'data': data
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}: {message}")
        
        if data:
            print(f"    Data: {data}")
    
    def test_unified_validator(self):
        """Testa validador unificado"""
        print("\n" + "="*50)
        print("TESTE 1: VALIDADOR UNIFICADO")
        print("="*50)
        
        # Testar estados
        estados_reserva = self.validator.get_estados_reserva()
        self.log_test(
            "Estados de Reserva",
            StatusReserva.PENDENTE.value in estados_reserva,
            f"Estados disponíveis: {list(estados_reserva.keys())}"
        )
        
        # Testar validação de pagamento
        reserva_mock = {'status': StatusReserva.PENDENTE.value}
        pode_pagar, motivo = self.validator.pode_pagar(reserva_mock)
        self.log_test(
            "Pode Pagar Reserva PENDENTE",
            pode_pagar,
            motivo,
            {"status": reserva_mock['status']}
        )
        
        # Testar validação de check-in
        pagamentos_mock = [{'status': StatusPagamento.CONFIRMADO.value}]
        pode_checkin, motivo = self.validator.pode_fazer_checkin(reserva_mock, pagamentos_mock)
        self.log_test(
            "Pode Check-in com Pagamento Confirmado",
            pode_checkin,
            motivo,
            {"status_reserva": reserva_mock['status'], "status_pagamento": pagamentos_mock[0]['status']}
        )
    
    def test_fluxo_completo(self):
        """Testa fluxo completo de reservas"""
        print("\n" + "="*50)
        print("TESTE 2: FLUXO COMPLETO")
        print("="*50)
        
        # 1. Criar Reserva
        try:
            dados_reserva = {
                'cliente_id': 1,
                'quarto_id': 101,
                'checkin_previsto': '2026-01-20T14:00:00Z',
                'checkout_previsto': '2026-01-22T12:00:00Z',
                'valor_diaria': 200.0,
                'num_diarias': 2
            }
            
            reserva = asyncio.run(self.service.criar_reserva(dados_reserva))
            self.log_test(
                "Criar Reserva",
                reserva['status'] == StatusReserva.PENDENTE.value,
                f"Reserva criada com status {reserva['status']}",
                {"id": reserva['id'], "status": reserva['status']}
            )
            
            reserva_id = reserva['id']
            
        except Exception as e:
            self.log_test("Criar Reserva", False, f"Erro: {str(e)}")
            return
        
        # 2. Processar Pagamento
        try:
            dados_pagamento = {
                'metodo': 'credit_card',
                'valor': 400.0,
                'cartao_numero': '4111111111111111',
                'cartao_validade': '12/25',
                'cartao_cvv': '123',
                'cartao_nome': 'JOAO SILVA'
            }
            
            pagamento = asyncio.run(self.service.processar_pagamento(reserva_id, dados_pagamento))
            
            # Verificar se pagamento foi criado e reserva confirmada
            reserva_atualizada = asyncio.run(self.service._buscar_reserva(reserva_id))
            
            sucesso_pagamento = pagamento['status'] == StatusPagamento.CONFIRMADO.value
            sucesso_reserva = reserva_atualizada['status'] == StatusReserva.CONFIRMADA.value
            
            self.log_test(
                "Processar Pagamento",
                sucesso_pagamento and sucesso_reserva,
                f"Pagamento: {pagamento['status']}, Reserva: {reserva_atualizada['status']}",
                {
                    "pagamento_status": pagamento['status'],
                    "reserva_status": reserva_atualizada['status']
                }
            )
            
        except Exception as e:
            self.log_test("Processar Pagamento", False, f"Erro: {str(e)}")
            return
        
        # 3. Fazer Check-in
        try:
            dados_checkin = {
                'funcionario_id': 1,
                'observacoes': 'Check-in normal'
            }
            
            checkin = asyncio.run(self.service.fazer_checkin(reserva_id, dados_checkin))
            
            self.log_test(
                "Fazer Check-in",
                checkin['status'] == 'CHECKIN_REALIZADO',
                f"Check-in realizado com status {checkin['status']}",
                {"status": checkin['status'], "reserva_id": reserva_id}
            )
            
        except Exception as e:
            self.log_test("Fazer Check-in", False, f"Erro: {str(e)}")
            return
        
        # 4. Fazer Check-out
        try:
            dados_checkout = {
                'observacoes': 'Check-out normal'
            }
            
            checkout = asyncio.run(self.service.fazer_checkout(reserva_id, dados_checkout))
            
            self.log_test(
                "Fazer Check-out",
                checkout['status'] == 'CHECKOUT_REALIZADO',
                f"Check-out realizado com status {checkout['status']}",
                {"status": checkout['status'], "reserva_id": reserva_id}
            )
            
        except Exception as e:
            self.log_test("Fazer Check-out", False, f"Erro: {str(e)}")
            return
    
    def test_diagnostico_fluxo(self):
        """Testa diagnóstico do fluxo"""
        print("\n" + "="*50)
        print("TESTE 3: DIAGNÓSTICO DE FLUXO")
        print("="*50)
        
        try:
            # Criar cenário de teste
            reserva_mock = {
                'id': 1,
                'status': StatusReserva.CONFIRMADA.value,
                'created_at': '2026-01-17T10:00:00Z'
            }
            
            pagamentos_mock = [{
                'id': 1,
                'status': StatusPagamento.CONFIRMADO.value,
                'created_at': '2026-01-17T11:00:00Z'
            }]
            
            hospedagem_mock = {
                'id': 1,
                'status': 'CHECKIN_REALIZADO',
                'reserva_id': 1
            }
            
            # Mock dos métodos do service
            async def mock_buscar_reserva(id):
                return reserva_mock
            
            async def mock_buscar_pagamentos(id):
                return pagamentos_mock
            
            async def mock_buscar_hospedagem(id):
                return hospedagem_mock
            
            self.service._buscar_reserva = mock_buscar_reserva
            self.service._buscar_pagamentos = mock_buscar_pagamentos
            self.service._buscar_hospedagem = mock_buscar_hospedagem
            
            # Executar diagnóstico
            diagnostico = asyncio.run(self.service.diagnosticar_fluxo(1))
            
            # Validar diagnóstico
            fluxo_correto = diagnostico['fluxo_atual'] == 'HOSPEDAGEM_EM_ANDAMENTO'
            acoes_disponiveis = 'FAZER_CHECKOUT' in diagnostico['proximas_acoes']
            sem_problemas = len(diagnostico['problemas']) == 0
            
            self.log_test(
                "Diagnóstico de Fluxo",
                fluxo_correto and acoes_disponiveis and sem_problemas,
                f"Fluxo: {diagnostico['fluxo_atual']}, Ações: {diagnostico['proximas_acoes']}",
                {
                    "fluxo_atual": diagnostico['fluxo_atual'],
                    "proximas_acoes": diagnostico['proximas_acoes'],
                    "problemas": diagnostico['problemas']
                }
            )
            
        except Exception as e:
            self.log_test("Diagnóstico de Fluxo", False, f"Erro: {str(e)}")
    
    def test_validacao_sequencia(self):
        """Testa validação de sequência"""
        print("\n" + "="*50)
        print("TESTE 4: VALIDAÇÃO DE SEQUÊNCIA")
        print("="*50)
        
        # Sequência correta
        sequencia_correta = [
            'CRIADA',
            'PAGAMENTO_PROCESSADO',
            'RESERVA_CONFIRMADA',
            'CHECKIN_REALIZADO',
            'HOSPEDAGEM_EM_ANDAMENTO',
            'CHECKOUT_REALIZADO',
            'HOSPEDAGEM_FINALIZADA'
        ]
        
        valido, mensagem = FluxoReservaService.validar_sequencia_fluxo(sequencia_correta)
        self.log_test(
            "Sequência Correta",
            valido,
            mensagem,
            {"sequencia": sequencia_correta}
        )
        
        # Sequência incorreta
        sequencia_incorreta = [
            'CRIADA',
            'CHECKIN_REALIZADO',  # Pulou pagamento
            'RESERVA_CONFIRMADA'
        ]
        
        valido, mensagem = FluxoReservaService.validar_sequencia_fluxo(sequencia_incorreta)
        self.log_test(
            "Sequência Incorreta",
            not valido,
            mensagem,
            {"sequencia": sequencia_incorreta}
        )
    
    def test_cores_e_labels(self):
        """Testa cores e labels"""
        print("\n" + "="*50)
        print("TESTE 5: CORES E LABELS")
        print("="*50)
        
        # Testar cores
        cor_pendente = self.validator.get_cor_status(StatusReserva.PENDENTE.value, 'reserva')
        cor_confirmada = self.validator.get_cor_status(StatusReserva.CONFIRMADA.value, 'reserva')
        
        self.log_test(
            "Cores de Status",
            'yellow' in cor_pendente and 'blue' in cor_confirmada,
            f"Pendente: {cor_pendente}, Confirmada: {cor_confirmada}",
            {"pendente": cor_pendente, "confirmada": cor_confirmada}
        )
        
        # Testar labels
        label_pendente = self.validator.get_label_status(StatusReserva.PENDENTE.value, 'reserva')
        label_confirmada = self.validator.get_label_status(StatusReserva.CONFIRMADA.value, 'reserva')
        
        self.log_test(
            "Labels de Status",
            label_pendente and label_confirmada,
            f"Pendente: {label_pendente}, Confirmada: {label_confirmada}",
            {"pendente": label_pendente, "confirmada": label_confirmada}
        )
    
    def run_all_tests(self):
        """Executa todos os testes"""
        print("🚀 INICIANDO TESTE COMPLETO DO FLUXO DE RESERVAS")
        print("="*60)
        
        try:
            self.test_unified_validator()
            self.test_fluxo_completo()
            self.test_diagnostico_fluxo()
            self.test_validacao_sequencia()
            self.test_cores_e_labels()
            
            # Resumo final
            self.print_summary()
            
        except Exception as e:
            print(f"❌ ERRO GERAL NOS TESTES: {str(e)}")
    
    def print_summary(self):
        """Imprime resumo dos testes"""
        print("\n" + "="*60)
        print("📊 RESUMO DOS TESTES")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total: {total_tests}")
        print(f"✅ Passou: {passed_tests}")
        print(f"❌ Falhou: {failed_tests}")
        print(f"📈 Taxa de Sucesso: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ TESTES FALHADOS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
        
        print("\n" + "="*60)
        
        if failed_tests == 0:
            print("🎉 TODOS OS TESTES PASSARAM! FLUXO IMPLEMENTADO CORRETAMENTE!")
        else:
            print("⚠️  ALGUNS TESTES FALHARAM. VERIFICAR IMPLEMENTAÇÃO.")
        
        print("="*60)


if __name__ == "__main__":
    # Executar testes
    tester = TestFluxoReservas()
    tester.run_all_tests()
