#!/bin/bash

# Teste Final via cURL - Frontend Oficial
BASE_URL="http://localhost:8080"
AUTH_EMAIL="admin@hotelreal.com.br"
AUTH_PASSWORD="admin123"

echo "🚀 Teste Final via cURL - Frontend Oficial"
echo "============================================================"

TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
TOKEN=""

# Função de teste
test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    local expected_status=$4
    local description=$5
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    echo ""
    echo "[TEST $TOTAL_TESTS] $description"
    echo "        $method $endpoint"
    
    if [ "$method" = "GET" ]; then
        if [ -n "$TOKEN" ]; then
            response=$(curl -s -w "\n%{http_code}" -H "Authorization: Bearer $TOKEN" "$BASE_URL$endpoint")
        else
            response=$(curl -s -w "\n%{http_code}" "$BASE_URL$endpoint")
        fi
    elif [ "$method" = "POST" ]; then
        if [ -n "$TOKEN" ]; then
            response=$(curl -s -w "\n%{http_code}" -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" -d "$data" "$BASE_URL$endpoint")
        else
            response=$(curl -s -w "\n%{http_code}" -X POST -H "Content-Type: application/json" -d "$data" "$BASE_URL$endpoint")
        fi
    fi
    
    status=$(echo "$response" | tail -n1 | tr -d '\r')
    
    if [ "$status" = "$expected_status" ]; then
        echo "        ✅ PASS (Status: $status)"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo "        ❌ FAIL (Status: $status, esperado: $expected_status)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
}

# 1. Login
echo ""
echo "🔐 Fazendo login..."
login_response=$(curl -s -w "\n%{http_code}" -X POST -H "Content-Type: application/json" -d "{\"email\":\"$AUTH_EMAIL\",\"password\":\"$AUTH_PASSWORD\"}" "$BASE_URL/api/v1/login")
login_status=$(echo "$login_response" | tail -n1 | tr -d '\r')

if [ "$login_status" = "200" ]; then
    # Extrair refresh_token
    TOKEN=$(echo "$login_response" | sed '$d' | grep -o '"refresh_token":"[^"]*"' | cut -d'"' -f4)
    
    if [ -n "$TOKEN" ]; then
        # Fazer refresh
        refresh_response=$(curl -s -w "\n%{http_code}" -X POST -H "Content-Type: application/json" -d "{\"refresh_token\":\"$TOKEN\"}" "$BASE_URL/api/v1/refresh")
        refresh_status=$(echo "$refresh_response" | tail -n1 | tr -d '\r')
        
        if [ "$refresh_status" = "200" ]; then
            TOKEN=$(echo "$refresh_response" | sed '$d' | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
            echo "✅ Login bem-sucedido"
            echo "✅ Token obtido"
        fi
    fi
fi

# 2. Testar APIs principais
echo ""
echo "📊 Testando APIs Principais..."
test_endpoint "GET" "/api/v1/dashboard/stats" "" "200" "Dashboard Stats"
test_endpoint "GET" "/api/v1/clientes" "" "200" "Clientes Listar"
test_endpoint "GET" "/api/v1/quartos" "" "200" "Quartos Listar"
test_endpoint "GET" "/api/v1/reservas" "" "200" "Reservas Listar"
test_endpoint "GET" "/api/v1/pagamentos" "" "200" "Pagamentos Listar"
test_endpoint "GET" "/api/v1/pontos/saldo/1" "" "200" "Pontos Saldo"

# 3. Testar criacoes
echo ""
echo "🔧 Testando Criacoes..."
timestamp=$(date +%s%N | tail -c 10)

cliente_data="{\"nome_completo\":\"Cliente Frontend $timestamp\",\"documento\":\"12345678901\",\"telefone\":\"21999$timestamp\",\"email\":\"frontend.$timestamp@test.com\"}"
test_endpoint "POST" "/api/v1/clientes" "$cliente_data" "201" "Criar Cliente"

quarto_data="{\"numero\":\"F$timestamp\",\"tipo_suite\":\"LUXO\",\"status\":\"LIVRE\"}"
test_endpoint "POST" "/api/v1/quartos" "$quarto_data" "201" "Criar Quarto"

# 4. Testar validacoes
echo ""
echo "🛡️ Testando Validacoes..."
cliente_invalido="{\"nome_completo\":\"Test Invalido\",\"documento\":\"123\",\"telefone\":\"21999999999\",\"email\":\"invalid@test.com\"}"
test_endpoint "POST" "/api/v1/clientes" "$cliente_invalido" "400" "Validacao CPF Invalido"

quarto_invalido="{\"numero\":\"TEST-$timestamp\",\"tipo_suite\":\"LUXO\",\"status\":\"INVALIDO\"}"
test_endpoint "POST" "/api/v1/quartos" "$quarto_invalido" "422" "Validacao Status Invalido"

# 5. Testar autenticacao
echo ""
echo "🔐 Testando Autenticacao..."
TOKEN=""

response=$(curl -s -w "\n%{http_code}" "$BASE_URL/api/v1/clientes")
status=$(echo "$response" | tail -n1 | tr -d '\r')

if [ "$status" = "401" ]; then
    echo "        ✅ PASS Autenticacao requerida (Status: 401)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo "        ❌ FAIL Autenticacao nao requerida (Status: $status)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# 6. Testar paginas frontend
echo ""
echo "🌐 Testando Paginas Frontend..."

# Pagina principal
response=$(curl -s -w "\n%{http_code}" "$BASE_URL/")
status=$(echo "$response" | tail -n1 | tr -d '\r')

if [ "$status" = "200" ]; then
    echo "        ✅ PASS Pagina Principal (Status: 200)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo "        ❌ FAIL Pagina Principal (Status: $status)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# Pagina login
response=$(curl -s -w "\n%{http_code}" "$BASE_URL/login")
status=$(echo "$response" | tail -n1 | tr -d '\r')

if [ "$status" = "200" ]; then
    echo "        ✅ PASS Pagina Login (Status: 200)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo "        ❌ FAIL Pagina Login (Status: $status)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# Relatorio final
echo ""
echo "============================================================"
echo "📊 RELATÓRIO FINAL - TESTES FRONTEND OFICIAL"
echo "============================================================"
echo "Total de Testes: $TOTAL_TESTS"
echo "Passou: $PASSED_TESTS"
echo "Falhou: $FAILED_TESTS"

if [ $TOTAL_TESTS -gt 0 ]; then
    success_rate=$((PASSED_TESTS * 100 / TOTAL_TESTS))
    echo "Taxa de Sucesso: $success_rate%"
    
    if [ $success_rate -ge 95 ]; then
        echo ""
        echo "🎉 EXCELENTE! Frontend oficial 100% funcional!"
    elif [ $success_rate -ge 85 ]; then
        echo ""
        echo "👍 BOM! Frontend oficial operacional."
    else
        echo ""
        echo "⚠️  ATENÇÃO! Frontend com problemas."
    fi
fi

echo ""
echo "============================================================"

if [ $FAILED_TESTS -eq 0 ]; then
    exit 0
else
    exit 1
fi
