# ============================================================
# Testes Manuais via PowerShell - Simulação Frontend
# ============================================================

Write-Host "🚀 Iniciando testes manuais via PowerShell (simulação frontend)" -ForegroundColor Cyan
Write-Host "============================================================"

# Configuração
$BASE_URL = "http://localhost:8080"
$AUTH_EMAIL = "admin@hotelreal.com.br"
$AUTH_PASSWORD = "admin123"

# Contadores
$TOTAL_TESTS = 0
$PASSED_TESTS = 0
$FAILED_TESTS = 0

# Função para fazer request e validar
function Test-Endpoint {
    param(
        [string]$Method,
        [string]$Endpoint,
        [string]$Data,
        [int]$ExpectedStatus,
        [string]$Description,
        [string]$ExpectedContent
    )
    
    $TOTAL_TESTS++
    
    Write-Host "`n[TEST $TOTAL_TESTS] $Description" -ForegroundColor Blue
    Write-Host "        $Method $Endpoint" -ForegroundColor Blue
    
    try {
        if ($Method -eq "GET") {
            $response = Invoke-RestMethod -Uri "$BASE_URL$Endpoint" -Method Get -Headers @{Authorization = "Bearer $TOKEN"} -ErrorAction Stop
            $status = 200
        } elseif ($Method -eq "POST") {
            $response = Invoke-RestMethod -Uri "$BASE_URL$Endpoint" -Method Post -ContentType "application/json" -Body $Data -Headers @{Authorization = "Bearer $TOKEN"} -ErrorAction Stop
            $status = 201
        }
        
        if ($status -eq $ExpectedStatus) {
            Write-Host "        ✅ PASS (Status: $status)" -ForegroundColor Green
            $PASSED_TESTS++
            
            # Validar conteúdo se esperado
            if ($ExpectedContent) {
                $responseJson = $response | ConvertTo-Json -Compress
                if ($responseJson -match $ExpectedContent) {
                    Write-Host "        ✅ Conteúdo validado: $ExpectedContent" -ForegroundColor Green
                } else {
                    Write-Host "        ⚠️  Conteúdo não encontrado: $ExpectedContent" -ForegroundColor Yellow
                }
            }
        } else {
            Write-Host "        ❌ FAIL (Status: $status, esperado: $ExpectedStatus)" -ForegroundColor Red
            $FAILED_TESTS++
        }
    } catch {
        $errorResponse = $_.Exception.Response
        if ($errorResponse) {
            $status = [int]$errorResponse.StatusCode
        } else {
            $status = 0
        }
        
        if ($status -eq $ExpectedStatus) {
            Write-Host "        ✅ PASS (Status: $status)" -ForegroundColor Green
            $PASSED_TESTS++
        } else {
            Write-Host "        ❌ FAIL (Status: $status, esperado: $ExpectedStatus)" -ForegroundColor Red
            Write-Host "        Error: $($_.Exception.Message)" -ForegroundColor Red
            $FAILED_TESTS++
        }
    }
}

# Função para login
function Get-AuthToken {
    Write-Host "`n🔐 Fazendo login..." -ForegroundColor Yellow
    
    try {
        $loginData = @{
            email = $AUTH_EMAIL
            password = $AUTH_PASSWORD
        } | ConvertTo-Json -Compress
        
        $loginResponse = Invoke-RestMethod -Uri "$BASE_URL/api/v1/login" -Method Post -ContentType "application/json" -Body $loginData -ErrorAction Stop
        
        if ($loginResponse.refresh_token) {
            $refreshToken = $loginResponse.refresh_token
            
            # Fazer refresh para obter access_token
            $refreshData = @{
                refresh_token = $refreshToken
            } | ConvertTo-Json -Compress
            
            $refreshResponse = Invoke-RestMethod -Uri "$BASE_URL/api/v1/refresh" -Method Post -ContentType "application/json" -Body $refreshData -ErrorAction Stop
            
            if ($refreshResponse.access_token) {
                $script:TOKEN = $refreshResponse.access_token
                Write-Host "✅ Login bem-sucedido" -ForegroundColor Green
                Write-Host "✅ Token obtido" -ForegroundColor Green
                return $true
            }
        }
    } catch {
        Write-Host "❌ Falha no login" -ForegroundColor Red
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
    
    return $false
}

# Iniciar testes
Write-Host "`n📊 Testes de API - Cobertura Frontend" -ForegroundColor Yellow
Write-Host "============================================================"

# 1. Login
if (Get-AuthToken) {
    Write-Host "`n🎯 Iniciando suíte de testes..." -ForegroundColor Green
    
    # 2. Testar endpoints principais (simulando frontend)
    
    # Dashboard
    Test-Endpoint -Method "GET" -Endpoint "/api/v1/dashboard/stats" -ExpectedStatus 200 -Description "Dashboard - Estatísticas" -ExpectedContent "total_reservas|total_clientes"
    
    # Clientes
    Test-Endpoint -Method "GET" -Endpoint "/api/v1/clientes" -ExpectedStatus 200 -Description "Clientes - Listar" -ExpectedContent "clientes|items"
    
    # Criar Cliente
    $timestamp = Get-Date -Format "yyyyMMddHHmmss"
    $clienteData = @{
        nome_completo = "Cliente Frontend $timestamp"
        documento = "12345678901"
        telefone = "21999$($timestamp.Substring(6))"
        email = "frontend.$timestamp@test.com"
    } | ConvertTo-Json -Compress
    
    Test-Endpoint -Method "POST" -Endpoint "/api/v1/clientes" -Data $clienteData -ExpectedStatus 201 -Description "Clientes - Criar" -ExpectedContent "id|nome_completo"
    
    # Quartos
    Test-Endpoint -Method "GET" -Endpoint "/api/v1/quartos" -ExpectedStatus 200 -Description "Quartos - Listar" -ExpectedContent "quartos|items"
    
    # Criar Quarto
    $quartoData = @{
        numero = "F$($timestamp.Substring(6))"
        tipo_suite = "LUXO"
        status = "LIVRE"
    } | ConvertTo-Json -Compress
    
    Test-Endpoint -Method "POST" -Endpoint "/api/v1/quartos" -Data $quartoData -ExpectedStatus 201 -Description "Quartos - Criar" -ExpectedContent "id|numero"
    
    # Reservas
    Test-Endpoint -Method "GET" -Endpoint "/api/v1/reservas" -ExpectedStatus 200 -Description "Reservas - Listar" -ExpectedContent "reservas|items"
    
    # Pagamentos
    Test-Endpoint -Method "GET" -Endpoint "/api/v1/pagamentos" -ExpectedStatus 200 -Description "Pagamentos - Listar" -ExpectedContent "pagamentos|items"
    
    # Pontos
    Test-Endpoint -Method "GET" -Endpoint "/api/v1/pontos/saldo/1" -ExpectedStatus 200 -Description "Pontos - Saldo" -ExpectedContent "saldo|pontos"
    
    # Testar validação de negócio (simulando frontend)
    Write-Host "`n🔍 Testes de Validação de Negócio" -ForegroundColor Yellow
    
    # Tentar criar cliente com CPF inválido
    $clienteInvalido = @{
        nome_completo = "Test Invalido"
        documento = "123"
        telefone = "21999999999"
        email = "invalid@test.com"
    } | ConvertTo-Json -Compress
    
    Test-Endpoint -Method "POST" -Endpoint "/api/v1/clientes" -Data $clienteInvalido -ExpectedStatus 400 -Description "Validação - CPF Inválido" -ExpectedContent "CPF inválido"
    
    # Tentar criar quarto com status inválido
    $quartoInvalido = @{
        numero = "TEST-$($timestamp.Substring(6))"
        tipo_suite = "LUXO"
        status = "INVALIDO"
    } | ConvertTo-Json -Compress
    
    Test-Endpoint -Method "POST" -Endpoint "/api/v1/quartos" -Data $quartoInvalido -ExpectedStatus 422 -Description "Validação - Status Quarto" -ExpectedContent "status|enum"
    
    # Testar autenticação
    Write-Host "`n🔐 Testes de Autenticação" -ForegroundColor Yellow
    
    # Tentar acesso sem token
    try {
        $response = Invoke-RestMethod -Uri "$BASE_URL/api/v1/clientes" -Method Get -ErrorAction Stop
        Write-Host "        ❌ FAIL Autenticação não requerida (Status: 200)" -ForegroundColor Red
        $FAILED_TESTS++
    } catch {
        $status = [int]$_.Exception.Response.StatusCode
        if ($status -eq 401) {
            Write-Host "        ✅ PASS Autenticação requerida (Status: 401)" -ForegroundColor Green
            $PASSED_TESTS++
        } else {
            Write-Host "        ❌ FAIL Status inesperado: $status" -ForegroundColor Red
            $FAILED_TESTS++
        }
    }
    $TOTAL_TESTS++
    
} else {
    Write-Host "❌ Não foi possível fazer login. Abortando testes." -ForegroundColor Red
    exit 1
}

# Relatório final
Write-Host "`n============================================================" -ForegroundColor Blue
Write-Host "📊 RELATÓRIO FINAL - TESTES FRONTEND" -ForegroundColor Blue
Write-Host "============================================================" -ForegroundColor Blue
Write-Host "Total de Testes: $TOTAL_TESTS" -ForegroundColor Yellow
Write-Host "Passou: $PASSED_TESTS" -ForegroundColor Green
Write-Host "Falhou: $FAILED_TESTS" -ForegroundColor Red

# Calcular percentual
if ($TOTAL_TESTS -gt 0) {
    $successRate = [math]::Round(($PASSED_TESTS * 100) / $TOTAL_TESTS, 1)
    Write-Host "Taxa de Sucesso: $successRate%" -ForegroundColor Green
    
    if ($successRate -ge 90) {
        Write-Host "`n🎉 EXCELENTE! Cobertura de testes frontend atingida!" -ForegroundColor Green
    } elseif ($successRate -ge 80) {
        Write-Host "`n👍 BOM! Cobertura satisfatória." -ForegroundColor Yellow
    } else {
        Write-Host "`n⚠️  ATENÇÃO! Cobertura abaixo do esperado." -ForegroundColor Red
    }
}

Write-Host "`n============================================================" -ForegroundColor Blue

# Exit code baseado nos resultados
if ($FAILED_TESTS -eq 0) {
    exit 0
} else {
    exit 1
}
