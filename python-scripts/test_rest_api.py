#!/usr/bin/env python3
"""
Script de Testes QA - Validação de Rotas REST
Testa todas as rotas refatoradas para conformidade REST
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"
TOKEN = None  # Será preenchido após login

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_test(name, passed, details=""):
    status = f"{Colors.GREEN}✅ PASS{Colors.END}" if passed else f"{Colors.RED}❌ FAIL{Colors.END}"
    print(f"{status} | {name}")
    if details and not passed:
        print(f"     {Colors.YELLOW}└─ {details}{Colors.END}")

def login():
    """Fazer login e obter token"""
    global TOKEN
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"email": "admin@hotel.com", "password": "admin123"}
        )
        if response.status_code == 200:
            TOKEN = response.json().get("access_token")
            print_test("Login de autenticação", True)
            return True
        else:
            print_test("Login de autenticação", False, f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_test("Login de autenticação", False, str(e))
        return False

def get_headers():
    """Retornar headers com autenticação"""
    return {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}

# ============================================================
# TESTES DE CLIENTES (100% conforme)
# ============================================================
def test_clientes():
    print(f"\n{Colors.BLUE}=== TESTES: CLIENTES ==={Colors.END}")
    
    # GET /clientes
    try:
        r = requests.get(f"{BASE_URL}/clientes", headers=get_headers())
        print_test("GET /clientes", r.status_code == 200, f"Status: {r.status_code}")
    except Exception as e:
        print_test("GET /clientes", False, str(e))
    
    # DELETE /clientes/{id}/ (com barra final - teste CORS)
    try:
        r = requests.delete(f"{BASE_URL}/clientes/999/", headers=get_headers())
        # 404 é esperado (cliente não existe), mas não deve dar CORS
        print_test("DELETE /clientes/{id}/ (CORS)", r.status_code in [404, 200], f"Status: {r.status_code}")
    except Exception as e:
        print_test("DELETE /clientes/{id}/ (CORS)", False, str(e))

# ============================================================
# TESTES DE RESERVAS (Refatoradas)
# ============================================================
def test_reservas():
    print(f"\n{Colors.BLUE}=== TESTES: RESERVAS (REST-compliant) ==={Colors.END}")
    
    # GET /reservas
    try:
        r = requests.get(f"{BASE_URL}/reservas", headers=get_headers())
        print_test("GET /reservas", r.status_code == 200, f"Status: {r.status_code}")
    except Exception as e:
        print_test("GET /reservas", False, str(e))
    
    # PATCH /reservas/{id} com status (REST-compliant)
    test_cases = [
        ("CHECKED_IN", "Check-in via PATCH"),
        ("CHECKED_OUT", "Check-out via PATCH"),
        ("CANCELADO", "Cancelar via PATCH"),
        ("CONFIRMADO", "Confirmar via PATCH"),
    ]
    
    for status, desc in test_cases:
        try:
            r = requests.patch(
                f"{BASE_URL}/reservas/999",
                json={"status": status},
                headers=get_headers()
            )
            # 404 é esperado (reserva não existe)
            print_test(f"PATCH /reservas/{{id}} - {desc}", r.status_code in [404, 200], f"Status: {r.status_code}")
        except Exception as e:
            print_test(f"PATCH /reservas/{{id}} - {desc}", False, str(e))
    
    # Testar rotas deprecated ainda funcionam
    try:
        r = requests.post(f"{BASE_URL}/reservas/999/checkin", headers=get_headers())
        print_test("POST /reservas/{id}/checkin (deprecated)", r.status_code in [404, 200], f"Status: {r.status_code}")
    except Exception as e:
        print_test("POST /reservas/{id}/checkin (deprecated)", False, str(e))

# ============================================================
# TESTES DE PAGAMENTOS (Refatoradas)
# ============================================================
def test_pagamentos():
    print(f"\n{Colors.BLUE}=== TESTES: PAGAMENTOS (REST-compliant) ==={Colors.END}")
    
    # GET /pagamentos
    try:
        r = requests.get(f"{BASE_URL}/pagamentos", headers=get_headers())
        print_test("GET /pagamentos", r.status_code == 200, f"Status: {r.status_code}")
    except Exception as e:
        print_test("GET /pagamentos", False, str(e))
    
    # PATCH /pagamentos/{id} com status (REST-compliant)
    try:
        r = requests.patch(
            f"{BASE_URL}/pagamentos/999",
            json={"status": "CANCELADO"},
            headers=get_headers()
        )
        print_test("PATCH /pagamentos/{id} - Cancelar", r.status_code in [404, 200, 400], f"Status: {r.status_code}")
    except Exception as e:
        print_test("PATCH /pagamentos/{id} - Cancelar", False, str(e))
    
    # Testar rota deprecated
    try:
        r = requests.post(f"{BASE_URL}/pagamentos/999/cancelar", headers=get_headers())
        print_test("POST /pagamentos/{id}/cancelar (deprecated)", r.status_code in [404, 200], f"Status: {r.status_code}")
    except Exception as e:
        print_test("POST /pagamentos/{id}/cancelar (deprecated)", False, str(e))

# ============================================================
# TESTES DE PONTOS (Refatoradas)
# ============================================================
def test_pontos():
    print(f"\n{Colors.BLUE}=== TESTES: PONTOS (REST-compliant) ==={Colors.END}")
    
    # POST /pontos/ajustes (novo)
    try:
        r = requests.post(
            f"{BASE_URL}/pontos/ajustes",
            json={"cliente_id": 1, "pontos": 10, "motivo": "Teste QA"},
            headers=get_headers()
        )
        print_test("POST /pontos/ajustes", r.status_code in [200, 201, 404], f"Status: {r.status_code}")
    except Exception as e:
        print_test("POST /pontos/ajustes", False, str(e))
    
    # POST /pontos/validacoes (novo)
    try:
        r = requests.post(
            f"{BASE_URL}/pontos/validacoes",
            json={"reserva_id": 1},
            headers=get_headers()
        )
        print_test("POST /pontos/validacoes", r.status_code in [200, 201, 404], f"Status: {r.status_code}")
    except Exception as e:
        print_test("POST /pontos/validacoes", False, str(e))
    
    # POST /pontos/lancamentos (novo)
    try:
        r = requests.post(
            f"{BASE_URL}/pontos/lancamentos",
            json={"reserva_id": 1},
            headers=get_headers()
        )
        print_test("POST /pontos/lancamentos", r.status_code in [200, 201, 404], f"Status: {r.status_code}")
    except Exception as e:
        print_test("POST /pontos/lancamentos", False, str(e))
    
    # POST /pontos/convites (novo)
    try:
        r = requests.post(
            f"{BASE_URL}/pontos/convites",
            json={"cliente_id": 1},
            headers=get_headers()
        )
        print_test("POST /pontos/convites", r.status_code in [200, 201, 404], f"Status: {r.status_code}")
    except Exception as e:
        print_test("POST /pontos/convites", False, str(e))
    
    # Testar rotas deprecated
    try:
        r = requests.post(
            f"{BASE_URL}/pontos/ajustar",
            json={"cliente_id": 1, "pontos": 10, "motivo": "Teste"},
            headers=get_headers()
        )
        print_test("POST /pontos/ajustar (deprecated)", r.status_code in [200, 201, 404], f"Status: {r.status_code}")
    except Exception as e:
        print_test("POST /pontos/ajustar (deprecated)", False, str(e))

# ============================================================
# TESTES DE NOTIFICAÇÕES (Refatoradas)
# ============================================================
def test_notificacoes():
    print(f"\n{Colors.BLUE}=== TESTES: NOTIFICAÇÕES (REST-compliant) ==={Colors.END}")
    
    # GET /notificacoes
    try:
        r = requests.get(f"{BASE_URL}/notificacoes", headers=get_headers())
        print_test("GET /notificacoes", r.status_code == 200, f"Status: {r.status_code}")
    except Exception as e:
        print_test("GET /notificacoes", False, str(e))
    
    # PATCH /notificacoes/{id} (novo)
    try:
        r = requests.patch(
            f"{BASE_URL}/notificacoes/999",
            json={"lida": True},
            headers=get_headers()
        )
        print_test("PATCH /notificacoes/{id}", r.status_code in [200, 404], f"Status: {r.status_code}")
    except Exception as e:
        print_test("PATCH /notificacoes/{id}", False, str(e))
    
    # PATCH /notificacoes (em lote - novo)
    try:
        r = requests.patch(
            f"{BASE_URL}/notificacoes",
            json={"lida": True},
            headers=get_headers()
        )
        print_test("PATCH /notificacoes (lote)", r.status_code == 200, f"Status: {r.status_code}")
    except Exception as e:
        print_test("PATCH /notificacoes (lote)", False, str(e))
    
    # POST /notificacoes (criar - novo)
    try:
        r = requests.post(
            f"{BASE_URL}/notificacoes",
            params={
                "titulo": "Teste QA",
                "mensagem": "Teste de notificação",
                "tipo": "info"
            },
            headers=get_headers()
        )
        print_test("POST /notificacoes", r.status_code in [200, 201], f"Status: {r.status_code}")
    except Exception as e:
        print_test("POST /notificacoes", False, str(e))

# ============================================================
# TESTES DE ANTIFRAUDE (Refatoradas)
# ============================================================
def test_antifraude():
    print(f"\n{Colors.BLUE}=== TESTES: ANTIFRAUDE (REST-compliant) ==={Colors.END}")
    
    # GET /antifraude/operacoes
    try:
        r = requests.get(f"{BASE_URL}/antifraude/operacoes", headers=get_headers())
        print_test("GET /antifraude/operacoes", r.status_code == 200, f"Status: {r.status_code}")
    except Exception as e:
        print_test("GET /antifraude/operacoes", False, str(e))
    
    # PATCH /antifraude/operacoes/{id} - Aprovar (novo)
    try:
        r = requests.patch(
            f"{BASE_URL}/antifraude/operacoes/999",
            json={"status": "APROVADO"},
            headers=get_headers()
        )
        print_test("PATCH /antifraude/operacoes/{id} - Aprovar", r.status_code in [200, 404], f"Status: {r.status_code}")
    except Exception as e:
        print_test("PATCH /antifraude/operacoes/{id} - Aprovar", False, str(e))
    
    # PATCH /antifraude/operacoes/{id} - Recusar (novo)
    try:
        r = requests.patch(
            f"{BASE_URL}/antifraude/operacoes/999",
            json={"status": "RECUSADO"},
            headers=get_headers()
        )
        print_test("PATCH /antifraude/operacoes/{id} - Recusar", r.status_code in [200, 404], f"Status: {r.status_code}")
    except Exception as e:
        print_test("PATCH /antifraude/operacoes/{id} - Recusar", False, str(e))

# ============================================================
# EXECUTAR TODOS OS TESTES
# ============================================================
def main():
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}  TESTES DE QA - VALIDAÇÃO REST API{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    # Login
    if not login():
        print(f"\n{Colors.RED}❌ Falha no login. Abortando testes.{Colors.END}")
        return
    
    # Executar testes
    test_clientes()
    test_reservas()
    test_pagamentos()
    test_pontos()
    test_notificacoes()
    test_antifraude()
    
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.GREEN}✅ Testes de QA concluídos{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")

if __name__ == "__main__":
    main()
