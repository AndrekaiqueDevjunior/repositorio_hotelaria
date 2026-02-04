#!/usr/bin/env python3
"""
Teste do fluxo completo de reservas
PENDENTE -> CONFIRMADA -> HOSPEDADO -> CHECKED_OUT
+ Validação de pontos
"""

import requests
import json
import time
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api/v1"
LOGIN_URL = "http://localhost:8000/api/v1/login"  # Rota correta sem /auth

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def log_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")

def log_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.END}")

def log_info(msg):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.END}")

def log_warning(msg):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")

def log_step(step_num, total, msg):
    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"PASSO {step_num}/{total}: {msg}")
    print(f"{'='*60}{Colors.END}\n")

# Variáveis globais
session = requests.Session()
reserva_id = None
cliente_id = None
saldo_pontos_inicial = 0
saldo_pontos_final = 0
auth_token = None

def test_0_login():
    """Fazer login e obter token JWT via cookie"""
    global auth_token
    log_step(0, 8, "Fazendo login (autenticação via cookie)")
    
    login_data = {
        "email": "admin@hotelreal.com.br",
        "password": "admin123"
    }
    
    try:
        response = session.post(LOGIN_URL, json=login_data)
        if response.status_code == 200:
            data = response.json()
            log_success("Login realizado com sucesso!")
            log_info(f"Usuário: {data.get('user', {}).get('nome')}")
            log_info(f"Perfil: {data.get('user', {}).get('perfil')}")
            
            # Token está em cookie HTTP-Only (mais seguro)
            # A session já guarda os cookies automaticamente
            if 'access_token' in session.cookies or 'session' in session.cookies:
                log_success("Cookie de autenticação obtido!")
                return True
            else:
                log_warning("Cookie não encontrado, mas login foi sucesso")
                log_info("Tentando continuar com a session...")
                return True
        else:
            log_error(f"Erro no login: {response.status_code}")
            log_error(response.text)
            return False
    except Exception as e:
        log_error(f"Exceção no login: {e}")
        return False

def test_1_criar_cliente():
    """Criar cliente de teste"""
    global cliente_id
    log_step(1, 7, "Criando cliente de teste")
    
    cliente_data = {
        "nome_completo": "João Teste Fluxo",
        "email": f"teste.fluxo.{int(time.time())}@teste.com",
        "telefone": "21987654321",
        "documento": f"{int(time.time() % 100000000000):011d}",
        "tipo_documento": "CPF"
    }
    
    try:
        response = session.post(f"{BASE_URL}/clientes", json=cliente_data)
        if response.status_code == 201:
            cliente = response.json()
            cliente_id = cliente.get("id")
            log_success(f"Cliente criado: ID {cliente_id}, Nome: {cliente.get('nome_completo')}")
            return True
        else:
            log_error(f"Erro ao criar cliente: {response.status_code}")
            log_error(response.text)
            return False
    except Exception as e:
        log_error(f"Exceção: {e}")
        return False

def test_2_criar_reserva():
    """Criar nova reserva (status PENDENTE)"""
    global reserva_id
    log_step(2, 7, "Criando nova reserva (PENDENTE)")
    
    checkin = datetime.now() + timedelta(days=1)
    checkout = checkin + timedelta(days=3)
    
    reserva_data = {
        "cliente_id": cliente_id,
        "quarto_numero": "101",
        "tipo_suite": "LUXO",
        "checkin_previsto": checkin.isoformat(),
        "checkout_previsto": checkout.isoformat(),
        "valor_diaria": 350.00,
        "num_diarias": 3
    }
    
    try:
        response = session.post(f"{BASE_URL}/reservas", json=reserva_data)
        if response.status_code == 201:
            reserva = response.json()
            reserva_id = reserva.get("id")
            status = reserva.get("status") or reserva.get("status_reserva")
            log_success(f"Reserva criada: ID {reserva_id}, Status: {status}")
            log_info(f"Código: {reserva.get('codigo_reserva')}")
            log_info(f"Valor total: R$ {reserva.get('valor_total')}")
            
            if status == "PENDENTE":
                log_success("✓ Status correto: PENDENTE")
                return True
            else:
                log_error(f"✗ Status incorreto! Esperado: PENDENTE, Recebido: {status}")
                return False
        else:
            log_error(f"Erro ao criar reserva: {response.status_code}")
            log_error(response.text)
            return False
    except Exception as e:
        log_error(f"Exceção: {e}")
        return False

def test_3_pagar_reserva():
    """Pagar reserva (PENDENTE → CONFIRMADA)"""
    log_step(3, 7, "Processando pagamento (PENDENTE → CONFIRMADA)")
    
    pagamento_data = {
        "reserva_id": reserva_id,
        "valor": 1050.00,
        "metodo": "CREDITO",
        "descricao": "Pagamento teste fluxo completo"
    }
    
    try:
        response = session.post(f"{BASE_URL}/pagamentos", json=pagamento_data)
        if response.status_code == 201:
            pagamento = response.json()
            log_success(f"Pagamento criado: ID {pagamento.get('id')}")
            log_info(f"Status pagamento: {pagamento.get('status')}")
            
            # Verificar status da reserva
            time.sleep(1)
            response = session.get(f"{BASE_URL}/reservas/{reserva_id}")
            if response.status_code == 200:
                reserva = response.json()
                status = reserva.get("status") or reserva.get("status_reserva")
                log_info(f"Status da reserva após pagamento: {status}")
                
                if status == "CONFIRMADA":
                    log_success("✓ Transição correta: PENDENTE → CONFIRMADA")
                    return True
                else:
                    log_error(f"✗ Status incorreto! Esperado: CONFIRMADA, Recebido: {status}")
                    return False
        else:
            log_error(f"Erro ao processar pagamento: {response.status_code}")
            log_error(response.text)
            return False
    except Exception as e:
        log_error(f"Exceção: {e}")
        return False

def test_4_checkin():
    """Fazer check-in (CONFIRMADA → HOSPEDADO)"""
    log_step(4, 7, "Realizando check-in (CONFIRMADA → HOSPEDADO)")
    
    checkin_data = {
        "hospede_titular_nome": "João Teste Fluxo",
        "hospede_titular_documento": "12345678901",
        "hospede_titular_documento_tipo": "CPF",
        "num_hospedes_real": 2,
        "num_criancas": 0,
        "veiculo_placa": "ABC1234",
        "caucao_cobrada": 200.00,
        "caucao_forma_pagamento": "DINHEIRO",
        "documentos_conferidos": True,
        "pagamento_validado": True,
        "termos_aceitos": True,
        "observacoes_checkin": "Teste automatizado"
    }
    
    try:
        response = session.post(f"{BASE_URL}/reservas/{reserva_id}/checkin", json=checkin_data)
        if response.status_code == 200:
            log_success("Check-in realizado com sucesso")
            
            # Verificar status da reserva
            time.sleep(1)
            response = session.get(f"{BASE_URL}/reservas/{reserva_id}")
            if response.status_code == 200:
                reserva = response.json()
                status = reserva.get("status") or reserva.get("status_reserva")
                log_info(f"Status da reserva após check-in: {status}")
                
                if status == "HOSPEDADO":
                    log_success("✓ Transição correta: CONFIRMADA → HOSPEDADO")
                    return True
                else:
                    log_error(f"✗ Status incorreto! Esperado: HOSPEDADO, Recebido: {status}")
                    return False
        else:
            log_error(f"Erro ao fazer check-in: {response.status_code}")
            log_error(response.text)
            return False
    except Exception as e:
        log_error(f"Exceção: {e}")
        return False

def test_5_verificar_pontos_antes():
    """Verificar saldo de pontos antes do checkout"""
    global saldo_pontos_inicial
    log_step(5, 7, "Verificando pontos ANTES do checkout")
    
    try:
        response = session.get(f"{BASE_URL}/pontos/cliente/{cliente_id}/saldo")
        if response.status_code == 200:
            data = response.json()
            saldo_pontos_inicial = data.get("saldo_total", 0)
            log_info(f"Saldo de pontos ANTES do checkout: {saldo_pontos_inicial}")
            return True
        else:
            log_warning(f"Não foi possível verificar pontos: {response.status_code}")
            return True  # Não bloqueia o teste
    except Exception as e:
        log_warning(f"Erro ao verificar pontos: {e}")
        return True  # Não bloqueia o teste

def test_6_checkout():
    """Fazer checkout (HOSPEDADO → CHECKED_OUT)"""
    log_step(6, 7, "Realizando checkout (HOSPEDADO → CHECKED_OUT)")
    
    checkout_data = {
        "vistoria_ok": True,
        "danos_encontrados": "",
        "valor_danos": 0,
        "consumo_frigobar": 50.00,
        "servicos_extras": 100.00,
        "taxa_late_checkout": 0,
        "caucao_devolvida": 200.00,
        "caucao_retida": 0,
        "motivo_retencao": "",
        "avaliacao_hospede": 5,
        "comentario_hospede": "Excelente estadia - teste automatizado",
        "forma_acerto": "DINHEIRO",
        "observacoes_checkout": "Teste automatizado"
    }
    
    try:
        response = session.post(f"{BASE_URL}/reservas/{reserva_id}/checkout", json=checkout_data)
        if response.status_code == 200:
            log_success("Checkout realizado com sucesso")
            
            # Verificar status da reserva
            time.sleep(1)
            response = session.get(f"{BASE_URL}/reservas/{reserva_id}")
            if response.status_code == 200:
                reserva = response.json()
                status = reserva.get("status") or reserva.get("status_reserva")
                log_info(f"Status da reserva após checkout: {status}")
                
                if status == "CHECKED_OUT":
                    log_success("✓ Transição correta: HOSPEDADO → CHECKED_OUT")
                    return True
                else:
                    log_error(f"✗ Status incorreto! Esperado: CHECKED_OUT, Recebido: {status}")
                    return False
        else:
            log_error(f"Erro ao fazer checkout: {response.status_code}")
            log_error(response.text)
            return False
    except Exception as e:
        log_error(f"Exceção: {e}")
        return False

def test_7_verificar_pontos_depois():
    """Verificar se pontos foram creditados"""
    global saldo_pontos_final
    log_step(7, 7, "Verificando pontos APÓS checkout")
    
    try:
        time.sleep(2)  # Aguardar processamento
        response = session.get(f"{BASE_URL}/pontos/cliente/{cliente_id}/saldo")
        if response.status_code == 200:
            data = response.json()
            saldo_pontos_final = data.get("saldo_total", 0)
            log_info(f"Saldo de pontos APÓS checkout: {saldo_pontos_final}")
            
            pontos_ganhos = saldo_pontos_final - saldo_pontos_inicial
            valor_total = 1050.00  # Valor base da reserva
            pontos_esperados = int(valor_total / 10)  # 1 ponto a cada R$ 10
            
            log_info(f"Pontos ganhos: {pontos_ganhos}")
            log_info(f"Pontos esperados: {pontos_esperados} (R$ 1050 / 10)")
            
            if pontos_ganhos >= pontos_esperados:
                log_success(f"✓ Pontos creditados corretamente: {pontos_ganhos} pontos")
                return True
            else:
                log_error(f"✗ Pontos incorretos! Esperado: {pontos_esperados}, Ganho: {pontos_ganhos}")
                return False
        else:
            log_warning(f"Não foi possível verificar pontos finais: {response.status_code}")
            return False
    except Exception as e:
        log_error(f"Erro ao verificar pontos finais: {e}")
        return False

def main():
    print(f"\n{Colors.BLUE}{'='*60}")
    print("🧪 TESTE DE FLUXO COMPLETO - SISTEMA HOTEL CABO FRIO")
    print(f"{'='*60}{Colors.END}\n")
    
    print(f"📋 Fluxo a ser testado:")
    print(f"   PENDENTE → CONFIRMADA → HOSPEDADO → CHECKED_OUT")
    print(f"   + Validação de pontos\n")
    
    tests = [
        ("Login (obter token JWT)", test_0_login),
        ("Criar cliente", test_1_criar_cliente),
        ("Criar reserva PENDENTE", test_2_criar_reserva),
        ("Pagar (PENDENTE → CONFIRMADA)", test_3_pagar_reserva),
        ("Check-in (CONFIRMADA → HOSPEDADO)", test_4_checkin),
        ("Verificar pontos antes", test_5_verificar_pontos_antes),
        ("Checkout (HOSPEDADO → CHECKED_OUT)", test_6_checkout),
        ("Verificar pontos creditados", test_7_verificar_pontos_depois),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
            if not result and "pontos" not in name.lower():
                log_error(f"Teste '{name}' falhou. Abortando sequência.")
                break
        except Exception as e:
            log_error(f"Erro crítico em '{name}': {e}")
            results.append((name, False))
            break
    
    # Relatório final
    print(f"\n{Colors.BLUE}{'='*60}")
    print("📊 RELATÓRIO FINAL")
    print(f"{'='*60}{Colors.END}\n")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = f"{Colors.GREEN}✅ PASSOU{Colors.END}" if result else f"{Colors.RED}❌ FALHOU{Colors.END}"
        print(f"{status} - {name}")
    
    print(f"\n{Colors.BLUE}Total: {passed}/{total} testes passaram{Colors.END}")
    
    if passed == total:
        print(f"\n{Colors.GREEN}{'='*60}")
        print("🎉 TODOS OS TESTES PASSARAM!")
        print(f"{'='*60}{Colors.END}\n")
    else:
        print(f"\n{Colors.RED}{'='*60}")
        print("⚠️  ALGUNS TESTES FALHARAM - VERIFICAR CORREÇÕES")
        print(f"{'='*60}{Colors.END}\n")

if __name__ == "__main__":
    main()
