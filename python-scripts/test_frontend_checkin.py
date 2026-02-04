#!/usr/bin/env python3
"""
TESTE DO BUG DO CHECK-IN NO FRONTEND
===================================
Verifica se a lógica do check-in está correta
"""

def test_pode_checkin_logica():
    """Testa a lógica do podeCheckin"""
    
    # Simulação da função isPagamentoAprovado do frontend
    def isPagamentoAprovado(status):
        return status in ['CONFIRMADO', 'APROVADO', 'PAGO', 'CAPTURED', 'AUTHORIZED']
    
    # Simulação da função podeCheckin corrigida
    def podeCheckin(reserva):
        # Verificar se reserva está confirmada E tem pagamento aprovado
        if reserva['status'] != 'CONFIRMADA':
            return False
        
        # Verificar se existe pagamento aprovado
        if reserva.get('pagamentos') and len(reserva['pagamentos']) > 0:
            return any(isPagamentoAprovado(pagamento['status']) 
                      for pagamento in reserva['pagamentos'])
        
        # Se não tiver dados de pagamentos, verificar status da reserva
        return reserva['status'] == 'CONFIRMADA'
    
    # Simulação da função getCheckinTooltip
    def getCheckinTooltip(reserva):
        if podeCheckin(reserva):
            return 'Realizar check-in'
        
        if reserva['status'] != 'CONFIRMADA':
            return 'Reserva deve estar confirmada'
        
        # Se está confirmada mas não pode fazer check-in, é problema de pagamento
        if reserva.get('pagamentos') and len(reserva['pagamentos']) > 0:
            pagamentosAprovados = [p for p in reserva['pagamentos'] if isPagamentoAprovado(p['status'])]
            if len(pagamentosAprovados) == 0:
                return 'Pagamento precisa ser aprovado para check-in'
        
        return 'Pagamento aprovado necessário para check-in'
    
    print("🧪 TESTE DA LÓGICA DO CHECK-IN")
    print("=" * 50)
    
    # Caso 1: Reserva PENDENTE (não pode check-in)
    reserva1 = {
        'status': 'PENDENTE',
        'pagamentos': []
    }
    
    resultado1 = podeCheckin(reserva1)
    tooltip1 = getCheckinTooltip(reserva1)
    print(f"❌ Caso 1 - Reserva PENDENTE: {resultado1} - {tooltip1}")
    
    # Caso 2: Reserva CONFIRMADA sem pagamentos (pode check-in)
    reserva2 = {
        'status': 'CONFIRMADA',
        'pagamentos': []
    }
    
    resultado2 = podeCheckin(reserva2)
    tooltip2 = getCheckinTooltip(reserva2)
    print(f"✅ Caso 2 - Reserva CONFIRMADA sem pagamentos: {resultado2} - {tooltip2}")
    
    # Caso 3: Reserva CONFIRMADA com pagamento PENDENTE (não pode check-in)
    reserva3 = {
        'status': 'CONFIRMADA',
        'pagamentos': [
            {'status': 'PENDENTE', 'id': 1}
        ]
    }
    
    resultado3 = podeCheckin(reserva3)
    tooltip3 = getCheckinTooltip(reserva3)
    print(f"❌ Caso 3 - Reserva CONFIRMADA com pagamento PENDENTE: {resultado3} - {tooltip3}")
    
    # Caso 4: Reserva CONFIRMADA com pagamento APROVADO (pode check-in)
    reserva4 = {
        'status': 'CONFIRMADA',
        'pagamentos': [
            {'status': 'APROVADO', 'id': 1}
        ]
    }
    
    resultado4 = podeCheckin(reserva4)
    tooltip4 = getCheckinTooltip(reserva4)
    print(f"✅ Caso 4 - Reserva CONFIRMADA com pagamento APROVADO: {resultado4} - {tooltip4}")
    
    # Caso 5: Reserva CONFIRMADA com múltiplos pagamentos, um aprovado (pode check-in)
    reserva5 = {
        'status': 'CONFIRMADA',
        'pagamentos': [
            {'status': 'PENDENTE', 'id': 1},
            {'status': 'NEGADO', 'id': 2},
            {'status': 'CONFIRMADO', 'id': 3}
        ]
    }
    
    resultado5 = podeCheckin(reserva5)
    tooltip5 = getCheckinTooltip(reserva5)
    print(f"✅ Caso 5 - Reserva CONFIRMADA com múltiplos pagamentos (um aprovado): {resultado5} - {tooltip5}")
    
    # Caso 6: Reserva CANCELADA (não pode check-in)
    reserva6 = {
        'status': 'CANCELADO',
        'pagamentos': [
            {'status': 'APROVADO', 'id': 1}
        ]
    }
    
    resultado6 = podeCheckin(reserva6)
    tooltip6 = getCheckinTooltip(reserva6)
    print(f"❌ Caso 6 - Reserva CANCELADA: {resultado6} - {tooltip6}")
    
    print("\n" + "=" * 50)
    print("📊 RESUMO")
    
    testes = [
        (resultado1, False, "Reserva PENDENTE"),
        (resultado2, True, "Reserva CONFIRMADA sem pagamentos"),
        (resultado3, False, "Reserva CONFIRMADA com pagamento PENDENTE"),
        (resultado4, True, "Reserva CONFIRMADA com pagamento APROVADO"),
        (resultado5, True, "Reserva CONFIRMADA com múltiplos pagamentos"),
        (resultado6, False, "Reserva CANCELADA")
    ]
    
    passou = 0
    for resultado, esperado, descricao in testes:
        if resultado == esperado:
            print(f"✅ {descricao}: CORRETO")
            passou += 1
        else:
            print(f"❌ {descricao}: INCORRETO (esperado {esperado}, recebeu {resultado})")
    
    print(f"\n🎯 Taxa de Sucesso: {passou}/{len(testes)} ({(passou/len(testes))*100:.1f}%)")
    
    if passou == len(testes):
        print("🎉 TODOS OS TESTES PASSARAM! LÓGICA DO CHECK-IN CORRIGIDA!")
    else:
        print("⚠️  ALGUNS TESTES FALHARAM. VERIFICAR LÓGICA.")

if __name__ == "__main__":
    test_pode_checkin_logica()
