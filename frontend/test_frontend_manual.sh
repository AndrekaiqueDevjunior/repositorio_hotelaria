#!/bin/bash

# ============================================================
# Testes Manuais via cURL - Simulação Frontend
# ============================================================

echo "🚀 Iniciando testes manuais via cURL (simulação frontend)"
echo "============================================================"

# Configuração
BASE_URL="http://localhost:8080"
AUTH_EMAIL="admin@hotelreal.com.br"
AUTH_PASSWORD="admin123"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Contador
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Função para fazer request e validar
test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    local expected_status=$4
    local description=$5
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    echo -e "\n${BLUE}[TEST $TOTAL_TESTS]${NC} $description"
    echo -e "${BLUE}        $method $endpoint${NC}"
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" -H "Authorization: Bearer $TOKEN" "$BASE_URL$endpoint")
    elif [ "$method" = "POST" ]; then
        response=$(curl -s -w "\n%{http_code}" -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" -d "$data" "$BASE_URL$endpoint")
    fi
    
    # Extrair status code (última linha)
    status_code=$(echo "$response" | tail -n1 | tr -d '\r')
    # Extrair body (todas as linhas exceto a última)
    body=$(echo "$response" | sed '$d')
    
    if [ "$status_code" = "$expected_status" ]; then
        echo -e "        ${GREEN}✅ PASS${NC} (Status: $status_code)"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        
        # Validar conteúdo do body se esperado
        if [ -n "$6" ]; then
            if echo "$body" | grep -q "$6"; then
                echo -e "        ${GREEN}✅ Conteúdo validado: $6${NC}"
            else
                echo -e "        ${YELLOW}⚠️  Conteúdo não encontrado: $6${NC}"
            fi
        fi
    else
        echo -e "        ${RED}❌ FAIL${NC} (Status: $status_code, esperado: $expected_status)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        echo -e "        ${RED}Response: $body${NC}"
    fi
}

# Função para login
login() {
    echo -e "\n${YELLOW}🔐 Fazendo login...${NC}"
    
    login_response=$(curl -s -w "\n%{http_code}" -X POST \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"$AUTH_EMAIL\",\"password\":\"$AUTH_PASSWORD\"}" \
        "$BASE_URL/api/v1/login")
    
    login_status=$(echo "$login_response" | tail -n1 | tr -d '\r')
    login_body=$(echo "$login_response" | sed '$d')
    
    if [ "$login_status" = "200" ]; then
        # Extrair refresh_token
        TOKEN=$(echo "$login_body" | grep -o '"refresh_token":"[^"]*"' | cut -d'"' -f4)
        
        if [ -n "$TOKEN" ]; then
            # Fazer refresh para obter access_token
            refresh_response=$(curl -s -w "\n%{http_code}" -X POST \
                -H "Content-Type: application/json" \
                -d "{\"refresh_token\":\"$TOKEN\"}" \
                "$BASE_URL/api/v1/refresh")
            
            refresh_status=$(echo "$refresh_response" | tail -n1 | tr -d '\r')
            refresh_body=$(echo "$refresh_response" | sed '$d')
            
            if [ "$refresh_status" = "200" ]; then
                TOKEN=$(echo "$refresh_body" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
                echo -e "${GREEN}✅ Login bem-sucedido${NC}"
                echo -e "${GREEN}✅ Token obtido${NC}"
                return 0
            fi
        fi
    fi
    
    echo -e "${RED}❌ Falha no login${NC}"
    echo -e "${RED}Response: $login_body${NC}"
    return 1
}

# Iniciar testes
echo -e "\n${YELLOW}📊 Testes de API - Cobertura Frontend${NC}"
echo "============================================================"

# 1. Login
if login; then
    echo -e "\n${GREEN}🎯 Iniciando suíte de testes...${NC}"
    
    # 2. Testar endpoints principais (simulando frontend)
    
    # Dashboard
    test_endpoint "GET" "/api/v1/dashboard/stats" "" "200" "Dashboard - Estatísticas" "total_reservas\|total_clientes"
    
    # Clientes
    test_endpoint "GET" "/api/v1/clientes" "" "200" "Clientes - Listar" "clientes\|items"
    
    # Criar Cliente
    timestamp=$(date +%s%N | tail -c 10)
    cliente_data="{\"nome_completo\":\"Cliente Frontend $timestamp\",\"documento\":\"12345678901\",\"telefone\":\"21999$timestamp\",\"email\":\"frontend.$timestamp@test.com\"}"
    test_endpoint "POST" "/api/v1/clientes" "$cliente_data" "201" "Clientes - Criar" "id\|nome_completo"
    
    # Quartos
    test_endpoint "GET" "/api/v1/quartos" "" "200" "Quartos - Listar" "quartos\|items"
    
    # Criar Quarto
    quarto_data="{\"numero\":\"F$timestamp\",\"tipo_suite\":\"LUXO\",\"status\":\"LIVRE\"}"
    test_endpoint "POST" "/api/v1/quartos" "$quarto_data" "201" "Quartos - Criar" "id\|numero"
    
    # Reservas
    test_endpoint "GET" "/api/v1/reservas" "" "200" "Reservas - Listar" "reservas\|items"
    
    # Pagamentos
    test_endpoint "GET" "/api/v1/pagamentos" "" "200" "Pagamentos - Listar" "pagamentos\|items"
    
    # Pontos
    test_endpoint "GET" "/api/v1/pontos/saldo/1" "" "200" "Pontos - Saldo" "saldo\|pontos"
    
    # Testar validação de negócio (simulando frontend)
    echo -e "\n${YELLOW}🔍 Testes de Validação de Negócio${NC}"
    
    # Tentar criar cliente com CPF inválido
    cliente_invalido="{\"nome_completo\":\"Test Invalido\",\"documento\":\"123\",\"telefone\":\"21999999999\",\"email\":\"invalid@test.com\"}"
    test_endpoint "POST" "/api/v1/clientes" "$cliente_invalido" "400" "Validação - CPF Inválido" "CPF inválido"
    
    # Tentar criar quarto com status inválido
    quarto_invalido="{\"numero\":\"TEST-$timestamp\",\"tipo_suite\":\"LUXO\",\"status\":\"INVALIDO\"}"
    test_endpoint "POST" "/api/v1/quartos" "$quarto_invalido" "422" "Validação - Status Quarto" "status\|enum"
    
    # Testar autenticação
    echo -e "\n${YELLOW}🔐 Testes de Autenticação${NC}"
    
    # Tentar acesso sem token
    response=$(curl -s -w "\n%{http_code}" "$BASE_URL/api/v1/clientes")
    status=$(echo "$response" | tail -n1 | tr -d '\r')
    
    if [ "$status" = "401" ]; then
        echo -e "        ${GREEN}✅ PASS${NC} Autenticação requerida (Status: 401)"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "        ${RED}❌ FAIL${NC} Autenticação não requerida (Status: $status)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
else
    echo -e "${RED}❌ Não foi possível fazer login. Abortando testes.${NC}"
    exit 1
fi

# Relatório final
echo -e "\n${BLUE}============================================================${NC}"
echo -e "${BLUE}📊 RELATÓRIO FINAL - TESTES FRONTEND${NC}"
echo -e "${BLUE}============================================================${NC}"
echo -e "Total de Testes: ${YELLOW}$TOTAL_TESTS${NC}"
echo -e "Passou: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Falhou: ${RED}$FAILED_TESTS${NC}"

# Calcular percentual
if [ $TOTAL_TESTS -gt 0 ]; then
    success_rate=$((PASSED_TESTS * 100 / TOTAL_TESTS))
    echo -e "Taxa de Sucesso: ${GREEN}$success_rate%${NC}"
    
    if [ $success_rate -ge 90 ]; then
        echo -e "\n${GREEN}🎉 EXCELENTE! Cobertura de testes frontend atingida!${NC}"
    elif [ $success_rate -ge 80 ]; then
        echo -e "\n${YELLOW}👍 BOM! Cobertura satisfatória.${NC}"
    else
        echo -e "\n${RED}⚠️  ATENÇÃO! Cobertura abaixo do esperado.${NC}"
    fi
fi

echo -e "\n${BLUE}============================================================${NC}"

# Exit code baseado nos resultados
if [ $FAILED_TESTS -eq 0 ]; then
    exit 0
else
    exit 1
fi
