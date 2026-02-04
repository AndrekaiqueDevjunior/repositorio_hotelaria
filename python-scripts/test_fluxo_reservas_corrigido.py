#!/usr/bin/env python3
"""
TESTE CORRIGIDO DO FLUXO DE RESERVAS
====================================
Versão corrigida que testa o fluxo com persistência de estado
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
    """Mock do banco de dados com persistência"""
    
    def __init__(self):
        self.reservas = {}
        self.pagamentos = {}
        self.hospedagens = {}
        self.next_id = 1


class TestFluxoReservasCorrigido:
    """Teste corrigido com persistência de estado"""
    
    def __init__(self):
        self.db = MockDatabase()
        self.validator = UnifiedStateValidator()
        self.service = FluxoReservaService(self.db)
        self.test_results = []
        
        # Configurar service para usar nosso mock
        self.service.db = self.db
    
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
    
    def test_fluxo_completo_corrigido(self):
        """Testa fluxo completo com persistência real"""
        print("\n" + "="*50)
        print("TESTE: FLUXO COMPLETO CORRIGIDO")
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
            
            # Salvar no mock database
            self.db.reservas[reserva['id']] = reserva
            
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
            
            # Salvar pagamento no mock database
            self.db.pagamentos[pagamento['id']] = pagamento
            
            # Atualizar reserva se foi confirmada
            if 'reserva_atualizada' in pagamento:
                self.db.reservas[reserva_id] = pagamento['reserva_atualizada']
                reserva_atualizada = pagamento['reserva_atualizada']
            else:
                reserva_atualizada = self.db.reservas[reserva_id]
            
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
            
            # Salvar hospedagem no mock database
            self.db.hospedagens[checkin['id']] = checkin
            
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
            
            # Atualizar hospedagem no mock database
            self.db.hospedagens[checkout['id']] = checkout
            
            self.log_test(
                "Fazer Check-out",
                checkout['status'] == 'CHECKOUT_REALIZADO',
                f"Check-out realizado com status {checkout['status']}",
                {"status": checkout['status'], "reserva_id": reserva_id}
            )
            
        except Exception as e:
            self.log_test("Fazer Check-out", False, f"Erro: {str(e)}")
            return
    
    def test_validacao_checkin_corrigida(self):
        """Testa validação de check-in com estado correto"""
        print("\n" + "="*50)
        print("TESTE: VALIDAÇÃO CHECK-IN CORRIGIDA")
        print("="*50)
        
        # Criar cenário com reserva confirmada e pagamento aprovado
        reserva_mock = {
            'id': 2,
            'status': StatusReserva.CONFIRMADA.value,
            'created_at': '2026-01-17T10:00:00Z'
        }
        
        pagamentos_mock = [{
            'id': 2,
            'status': StatusPagamento.CONFIRMADO.value,
            'created_at': '2026-01-17T11:00:00Z'
        }]
        
        pode_checkin, motivo = self.validator.pode_fazer_checkin(reserva_mock, pagamentos_mock)
        
        self.log_test(
            "Pode Check-in com Reserva CONFIRMADA",
            pode_checkin,
            motivo,
            {
                "status_reserva": reserva_mock['status'],
                "status_pagamento": pagamentos_mock[0]['status']
            }
        )
    
    def test_diagnostico_com_estado_real(self):
        """Testa diagnóstico com estado real do mock database"""
        print("\n" + "="*50)
        print("TESTE: DIAGNÓSTICO COM ESTADO REAL")
        print("="*50)
        
        # Se temos dados no mock database, usar eles
        if self.db.reservas:
            reserva_id = list(self.db.reservas.keys())[0]
            
            # Override dos métodos para usar dados reais
            async def mock_buscar_reserva(id):
                return self.db.reservas.get(id, {})
            
            async def mock_buscar_pagamentos(id):
                return [p for p in self.db.pagamentos.values() if p.get('reserva_id') == id]
            
            async def mock_buscar_hospedagem(id):
                hospedagens = [h for h in self.db.hospedagens.values() if h.get('reserva_id') == id]
                return hospedagens[0] if hospedagens else None
            
            self.service._buscar_reserva = mock_buscar_reserva
            self.service._buscar_pagamentos = mock_buscar_pagamentos
            self.service._buscar_hospedagem = mock_buscar_hospedagem
            
            # Executar diagnóstico
            diagnostico = asyncio.run(self.service.diagnosticar_fluxo(reserva_id))
            
            self.log_test(
                "Diagnóstico com Estado Real",
                'fluxo_atual' in diagnostico,
                f"Fluxo atual: {diagnostico.get('fluxo_atual', 'N/A')}",
                {
                    "fluxo_atual": diagnostico.get('fluxo_atual'),
                    "proximas_acoes": diagnostico.get('proximas_acoes', []),
                    "problemas": diagnostico.get('problemas', [])
                }
            )
        else:
            self.log_test(
                "Diagnóstico com Estado Real",
                False,
                "Nenhum dado no mock database"
            )
    
    def test_sequencia_fluxo_real(self):
        """Testa sequência baseada no fluxo real executado"""
        print("\n" + "="*50)
        print("TESTE: SEQUÊNCIA FLUXO REAL")
        print("="*50)
        
        # Montar sequência baseada nos testes que passaram
        sequencia_real = []
        
        if self.db.reservas:
            sequencia_real.append('CRIADA')
        
        if any(p['status'] == StatusPagamento.CONFIRMADO.value for p in self.db.pagamentos.values()):
            sequencia_real.append('PAGAMENTO_PROCESSADO')
        
        if any(r['status'] == StatusReserva.CONFIRMADA.value for r in self.db.reservas.values()):
            sequencia_real.append('RESERVA_CONFIRMADA')
        
        if any(h['status'] == 'CHECKIN_REALIZADO' for h in self.db.hospedagens.values()):
            sequencia_real.append('CHECKIN_REALIZADO')
            sequencia_real.append('HOSPEDAGEM_EM_ANDAMENTO')
        
        if any(h['status'] == 'CHECKOUT_REALIZADO' for h in self.db.hospedagens.values()):
            sequencia_real.append('CHECKOUT_REALIZADO')
            sequencia_real.append('HOSPEDAGEM_FINALIZADA')
        
        if sequencia_real:
            valido, mensagem = FluxoReservaService.validar_sequencia_fluxo(sequencia_real)
            
            self.log_test(
                "Sequência Fluxo Real",
                valido,
                mensagem,
                {"sequencia": sequencia_real}
            )
        else:
            self.log_test(
                "Sequência Fluxo Real",
                False,
                "Nenhuma sequência gerada"
            )
    
    def run_all_tests(self):
        """Executa todos os testes corrigidos"""
        print("🚀 INICIANDO TESTE CORRIGIDO DO FLUXO DE RESERVAS")
        print("="*60)
        
        try:
            self.test_fluxo_completo_corrigido()
            self.test_validacao_checkin_corrigida()
            self.test_diagnostico_com_estado_real()
            self.test_sequencia_fluxo_real()
            
            # Resumo final
            self.print_summary()
            
        except Exception as e:
            print(f"❌ ERRO GERAL NOS TESTES: {str(e)}")
    
    def print_summary(self):
        """Imprime resumo dos testes"""
        print("\n" + "="*60)
        print("📊 RESUMO DOS TESTES CORRIGIDOS")
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
            print("🎉 TODOS OS TESTES PASSARAM! FLUXO CORRIGIDO!")
        else:
            print("⚠️  ALGUNS TESTES AINDA FALHAM.")
        
        print("="*60)


if __name__ == "__main__":
    # Executar testes corrigidos
    tester = TestFluxoReservasCorrigido()
    tester.run_all_tests()
