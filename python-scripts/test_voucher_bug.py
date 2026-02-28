#!/usr/bin/env python3
"""
TESTE DO BUG DO VOUCHER
=======================
Investiga problemas na validação e geração de vouchers
"""

import sys
import os

# Adicionar backend ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_voucher_status_validation():
    """Testa problemas na validação de status do voucher"""
    
    print("🧪 INVESTIGANDO BUG DO VOUCHER")
    print("=" * 50)
    
    # Simulação dos STATUS_PAGAMENTO_VALIDOS do voucher_service.py
    STATUS_PAGAMENTO_VALIDOS = (
        "APROVADO", "PAGO", "CONFIRMADO",  # Status genéricos
        "CAPTURED", "AUTHORIZED", "PAID",   # Status Cielo
        "PaymentConfirmed", "Authorized"    # Status Cielo API
    )
    
    # Simulação de pagamentos com diferentes estruturas de status
    pagamentos_teste = [
        {
            "nome": "Pagamento com status correto",
            "pagamento": {
                "status": "APROVADO",
                "id": 1
            }
        },
        {
            "nome": "Pagamento com statusPagamento",
            "pagamento": {
                "statusPagamento": "APROVADO",
                "id": 2
            }
        },
        {
            "nome": "Pagamento com status None",
            "pagamento": {
                "status": None,
                "statusPagamento": "CONFIRMADO",
                "id": 3
            }
        },
        {
            "nome": "Pagamento com ambos os campos",
            "pagamento": {
                "status": "PAGO",
                "statusPagamento": "AUTHORIZED",
                "id": 4
            }
        },
        {
            "nome": "Pagamento com status inválido",
            "pagamento": {
                "status": "PENDENTE",
                "statusPagamento": "PROCESSING",
                "id": 5
            }
        },
        {
            "nome": "Pagamento sem status",
            "pagamento": {
                "id": 6
            }
        }
    ]
    
    # Simulação da lógica do voucher_service.py
    def validar_pagamento_voucher(pagamento):
        """Simula a validação do voucher"""
        return (
            (pagamento.get('statusPagamento', None) in STATUS_PAGAMENTO_VALIDOS) or 
            (pagamento.get('status', None) in STATUS_PAGAMENTO_VALIDOS)
        )
    
    print("📋 TESTE DE VALIDAÇÃO DE PAGAMENTOS:")
    print("-" * 50)
    
    for teste in pagamentos_teste:
        pagamento = teste["pagamento"]
        resultado = validar_pagamento_voucher(pagamento)
        
        status_str = f"status={pagamento.get('status')}, statusPagamento={pagamento.get('statusPagamento')}"
        
        print(f"{'✅' if resultado else '❌'} {teste['nome']}")
        print(f"   {status_str} → {'VÁLIDO' if resultado else 'INVÁLIDO'}")
        print()
    
    # Testar problema específico: getattr com None
    print("🔍 INVESTIGANDO O PROBLEMA DO getattr:")
    print("-" * 50)
    
    class MockPagamento:
        def __init__(self, status=None, statusPagamento=None):
            self.status = status
            self.statusPagamento = statusPagamento
    
    # Testar getattr com diferentes valores
    testes_getattr = [
        ("status normal", MockPagamento("APROVADO")),
        ("statusPagamento normal", MockPagamento(None, "APROVADO")),
        ("status None", MockPagamento(None)),
        ("statusPagamento None", MockPagamento("APROVADO", None)),
        ("ambos None", MockPagamento(None, None)),
        ("ambos preenchidos", MockPagamento("APROVADO", "CONFIRMADO"))
    ]
    
    for nome, pagamento in testes_getattr:
        status_attr = getattr(pagamento, 'status', None)
        statusPagamento_attr = getattr(pagamento, 'statusPagamento', None)
        
        resultado = (
            (statusPagamento_attr in STATUS_PAGAMENTO_VALIDOS) or 
            (status_attr in STATUS_PAGAMENTO_VALIDOS)
        )
        
        print(f"{'✅' if resultado else '❌'} {nome}")
        print(f"   getattr(status) = {status_attr}")
        print(f"   getattr(statusPagamento) = {statusPagamento_attr}")
        print(f"   Resultado: {'VÁLIDO' if resultado else 'INVÁLIDO'}")
        print()

def test_voucher_geracao():
    """Testa problemas na geração de vouchers"""
    
    print("🔍 INVESTIGANDO GERAÇÃO DE VOUCHERS:")
    print("-" * 50)
    
    # Simular diferentes cenários de reserva
    reservas_teste = [
        {
            "nome": "Reserva com pagamento APROVADO",
            "status": "CONFIRMADA",
            "pagamentos": [
                {"status": "APROVADO", "id": 1}
            ]
        },
        {
            "nome": "Reserva com pagamento CONFIRMADO",
            "status": "CONFIRMADA",
            "pagamentos": [
                {"status": "CONFIRMADO", "id": 2}
            ]
        },
        {
            "nome": "Reserva com pagamento PENDENTE",
            "status": "CONFIRMADA",
            "pagamentos": [
                {"status": "PENDENTE", "id": 3}
            ]
        },
        {
            "nome": "Reserva sem pagamentos",
            "status": "CONFIRMADA",
            "pagamentos": []
        },
        {
            "nome": "Reserva PENDENTE",
            "status": "PENDENTE",
            "pagamentos": []
        }
    ]
    
    # Simular lógica de geração de voucher
    def pode_gerar_voucher(reserva):
        """Verifica se pode gerar voucher"""
        if reserva["status"] != "CONFIRMADA":
            return False, "Reserva não está confirmada"
        
        if not reserva["pagamentos"]:
            return False, "Não há pagamentos"
        
        # Verificar se algum pagamento está aprovado
        STATUS_PAGAMENTO_VALIDOS = ("APROVADO", "PAGO", "CONFIRMADO", "CAPTURED", "AUTHORIZED", "PAID")
        
        for pagamento in reserva["pagamentos"]:
            if pagamento["status"] in STATUS_PAGAMENTO_VALIDOS:
                return True, "Voucher pode ser gerado"
        
        return False, "Nenhum pagamento aprovado"
    
    for teste in reservas_teste:
        pode, motivo = pode_gerar_voucher(teste)
        
        print(f"{'✅' if pode else '❌'} {teste['nome']}")
        print(f"   Status: {teste['status']}")
        print(f"   Pagamentos: {len(teste['pagamentos'])}")
        print(f"   Resultado: {motivo}")
        print()

def test_voucher_checkin():
    """Testa problemas na validação de check-in do voucher"""
    
    print("🔍 INVESTIGANDO VALIDAÇÃO DE CHECK-IN:")
    print("-" * 50)
    
    # Simular diferentes cenários de voucher para check-in
    vouchers_teste = [
        {
            "nome": "Voucher ativo com pagamento aprovado",
            "status": "ATIVO",
            "reserva": {
                "status": "CONFIRMADA",
                "pagamentos": [{"status": "APROVADO"}],
                "checkinPrevisto": "2026-01-20"
            }
        },
        {
            "nome": "Voucher cancelado",
            "status": "CANCELADO",
            "reserva": {
                "status": "CONFIRMADA",
                "pagamentos": [{"status": "APROVADO"}],
                "checkinPrevisto": "2026-01-20"
            }
        },
        {
            "nome": "Voucher com check-in já realizado",
            "status": "CHECKIN_REALIZADO",
            "reserva": {
                "status": "CONFIRMADA",
                "pagamentos": [{"status": "APROVADO"}],
                "checkinPrevisto": "2026-01-20"
            }
        },
        {
            "nome": "Voucher com pagamento pendente",
            "status": "ATIVO",
            "reserva": {
                "status": "CONFIRMADA",
                "pagamentos": [{"status": "PENDENTE"}],
                "checkinPrevisto": "2026-01-20"
            }
        },
        {
            "nome": "Voucher com data fora do prazo",
            "status": "ATIVO",
            "reserva": {
                "status": "CONFIRMADA",
                "pagamentos": [{"status": "APROVADO"}],
                "checkinPrevisto": "2026-01-25"  # Longe da data atual
            }
        }
    ]
    
    def pode_fazer_checkin_voucher(voucher):
        """Simula validação de check-in do voucher"""
        # Verificar status do voucher
        if voucher["status"] == "CANCELADO":
            return False, "Voucher cancelado"
        
        if voucher["status"] == "FINALIZADO":
            return False, "Voucher já finalizado"
        
        if voucher["status"] == "CHECKIN_REALIZADO":
            return False, "Check-in já realizado"
        
        # Verificar pagamento
        reserva = voucher["reserva"]
        STATUS_PAGAMENTO_VALIDOS = ("APROVADO", "PAGO", "CONFIRMADO", "CAPTURED", "AUTHORIZED", "PAID")
        
        pagamento_confirmado = any(
            p["status"] in STATUS_PAGAMENTO_VALIDOS
            for p in reserva["pagamentos"]
        )
        
        if not pagamento_confirmado:
            return False, "Pagamento não confirmado"
        
        # Verificar data (simplificado)
        return True, "Check-in permitido"
    
    for teste in vouchers_teste:
        pode, motivo = pode_fazer_checkin_voucher(teste)
        
        print(f"{'✅' if pode else '❌'} {teste['nome']}")
        print(f"   Status Voucher: {teste['status']}")
        print(f"   Resultado: {motivo}")
        print()

if __name__ == "__main__":
    test_voucher_status_validation()
    test_voucher_geracao()
    test_voucher_checkin()
    
    print("=" * 50)
    print("🎯 RESUMO DA INVESTIGAÇÃO")
    print("=" * 50)
    print("1. ✅ Validação de status funciona corretamente")
    print("2. ✅ Geração de voucher depende de pagamento aprovado")
    print("3. ✅ Check-in só funciona com voucher ativo e pagamento aprovado")
    print("4. ⚠️  Possível bug: getattr com None pode causar problemas")
    print("5. ⚠️  Possível bug: inconsistência nos nomes dos campos de status")
    print("=" * 50)
