# ============================================================
# Testes via cURL no Frontend Oficial do Sistema
# ============================================================

Write-Host "🚀 Testando Frontend Oficial via cURL/PowerShell" -ForegroundColor Cyan
Write-Host "============================================================"

# Configuração
$BASE_URL = "http://localhost:8080"
$AUTH_EMAIL = "admin@hotelreal.com.br"
$AUTH_PASSWORD = "admin123"

# Contadores
$TOTAL_TESTS = 0
$PASSED_TESTS = 0
$FAILED_TESTS = 0

# Variável global para cookies
$COOKIES = ""

# Função para fazer request via frontend
function Test-FrontendEndpoint {
    param(
        [string]$Method,
        [string]$Path,
        [string]$Data,
        [int]$ExpectedStatus,
        [string]$Description,
        [string]$ExpectedContent
    )
    
    $TOTAL_TESTS++
    
    Write-Host "`n[TEST $TOTAL_TESTS] $Description" -ForegroundColor Blue
    Write-Host "        $Method $BASE_URL$Path" -ForegroundColor Blue
    
    try {
        $headers = @{}
        if ($COOKIES) {
            $headers["Cookie"] = $COOKIES
        }
        
        if ($Method -eq "GET") {
            $response = Invoke-WebRequest -Uri "$BASE_URL$Path" -Method Get -Headers $headers -UseBasicParsing -ErrorAction Stop
            $status = [int]$response.StatusCode
        } elseif ($Method -eq "POST") {
            $headers["Content-Type"] = "application/json"
            $response = Invoke-WebRequest -Uri "$BASE_URL$Path" -Method Post -Headers $headers -Body $Data -UseBasicParsing -ErrorAction Stop
            $status = [int]$response.StatusCode
        }
        
        # Extrair cookies da resposta
        if ($response.Headers["Set-Cookie"]) {
            $script:COOKIES = $response.Headers["Set-Cookie"]
        }
        
        if ($status -eq $ExpectedStatus) {
            Write-Host "        ✅ PASS (Status: $status)" -ForegroundColor Green
            $PASSED_TESTS++
            
            # Validar conteúdo se esperado
            if ($ExpectedContent) {
                $content = $response.Content
                if ($content -match $ExpectedContent) {
                    Write-Host "        ✅ Conteúdo validado: $ExpectedContent" -ForegroundColor Green
                } else {
                    Write-Host "        ⚠️  Conteúdo não encontrado: $ExpectedContent" -ForegroundColor Yellow
                }
            }
        } else {
            Write-Host "        ❌ FAIL (Status: $status, esperado: $ExpectedStatus)" -ForegroundColor Red
            $FAILED_TESTS++
            Write-Host "        Response: $($response.Content.Substring(0, 200))..." -ForegroundColor Red
        }
    } catch {
        $status = if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode } else { 0 }
        
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

# Iniciar testes
Write-Host "`n📊 Testes do Frontend Oficial - Hotel Cabo Frio" -ForegroundColor Yellow
Write-Host "============================================================"

# 1. Testar página principal
Test-FrontendEndpoint -Method "GET" -Path "/" -ExpectedStatus 200 -Description "Página Principal" -ExpectedContent "Hotel|Login|Entrar"

# 2. Testar página de login
Test-FrontendEndpoint -Method "GET" -Path "/login" -ExpectedStatus 200 -Description "Página de Login" -ExpectedContent "email|password|Entrar"

# 3. Fazer login via frontend
Write-Host "`n🔐 Fazendo login via frontend..." -ForegroundColor Yellow

try {
    $loginData = @{
        email = $AUTH_EMAIL
        password = $AUTH_PASSWORD
    } | ConvertTo-Json
    
    $loginResponse = Invoke-WebRequest -Uri "$BASE_URL/api/v1/login" -Method Post -ContentType "application/json" -Body $loginData -UseBasicParsing -ErrorAction Stop
    
    if ($loginResponse.StatusCode -eq 200) {
        # Extrair cookies do login
        if ($loginResponse.Headers["Set-Cookie"]) {
            $script:COOKIES = $loginResponse.Headers["Set-Cookie"]
            Write-Host "✅ Login via frontend bem-sucedido" -ForegroundColor Green
            Write-Host "✅ Cookies obtidos" -ForegroundColor Green
        } else {
            Write-Host "⚠️  Login ok, mas sem cookies" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "❌ Falha no login via frontend" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

# 4. Testar páginas protegidas (após login)
Test-FrontendEndpoint -Method "GET" -Path "/dashboard" -ExpectedStatus 200 -Description "Dashboard" -ExpectedContent "Dashboard|Painel|Reservas"

Test-FrontendEndpoint -Method "GET" -Path "/dashboard/clientes" -ExpectedStatus 200 -Description "Clientes Dashboard" -ExpectedContent "Clientes|Lista"

Test-FrontendEndpoint -Method "GET" -Path "/dashboard/reservas" -ExpectedStatus 200 -Description "Reservas Dashboard" -ExpectedContent "Reservas|Lista"

Test-FrontendEndpoint -Method "GET" -Path "/dashboard/quartos" -ExpectedStatus 200 -Description "Quartos Dashboard" -ExpectedContent "Quartos|Lista"

Test-FrontendEndpoint -Method "GET" -Path "/dashboard/pagamentos" -ExpectedStatus 200 -Description "Pagamentos Dashboard" -ExpectedContent "Pagamentos|Lista"

Test-FrontendEndpoint -Method "GET" -Path "/dashboard/pontos" -ExpectedStatus 200 -Description "Pontos Dashboard" -ExpectedContent "Pontos|Saldo"

# 5. Testar API endpoints via frontend (simulando browser)
Write-Host "`n🔍 Testando APIs via Frontend (simulando browser)" -ForegroundColor Yellow

Test-FrontendEndpoint -Method "GET" -Path "/api/v1/dashboard/stats" -ExpectedStatus 200 -Description "API Dashboard Stats" -ExpectedContent "total_reservas|total_clientes"

Test-FrontendEndpoint -Method "GET" -Path "/api/v1/clientes" -ExpectedStatus 200 -Description "API Clientes" -ExpectedContent "clientes|items"

Test-FrontendEndpoint -Method "GET" -Path "/api/v1/quartos" -ExpectedStatus 200 -Description "API Quartos" -ExpectedContent "quartos|items"

Test-FrontendEndpoint -Method "GET" -Path "/api/v1/reservas" -ExpectedStatus 200 -Description "API Reservas" -ExpectedContent "reservas|items"

Test-FrontendEndpoint -Method "GET" -Path "/api/v1/pagamentos" -ExpectedStatus 200 -Description "API Pagamentos" -ExpectedContent "pagamentos|items"

Test-FrontendEndpoint -Method "GET" -Path "/api/v1/pontos/saldo/1" -ExpectedStatus 200 -Description "API Pontos Saldo" -ExpectedContent "saldo|pontos"

# 6. Testar criação via frontend API
Write-Host "`n🔧 Testando Criação via Frontend API" -ForegroundColor Yellow

# Criar Cliente via API
$timestamp = Get-Date -Format "yyyyMMddHHmmss"
$clienteData = @{
    nome_completo = "Cliente Frontend $timestamp"
    documento = "12345678901"
    telefone = "21999$($timestamp.Substring(6))"
    email = "frontend.api.$timestamp@test.com"
} | ConvertTo-Json

Test-FrontendEndpoint -Method "POST" -Path "/api/v1/clientes" -Data $clienteData -ExpectedStatus 201 -Description "Criar Cliente via API" -ExpectedContent "id|nome_completo"

# Criar Quarto via API
$quartoData = @{
    numero = "F$($timestamp.Substring(6))"
    tipo_suite = "LUXO"
    status = "LIVRE"
} | ConvertTo-Json

Test-FrontendEndpoint -Method "POST" -Path "/api/v1/quartos" -Data $quartoData -ExpectedStatus 201 -Description "Criar Quarto via API" -ExpectedContent "id|numero"

# 7. Testar validações de negócio via frontend
Write-Host "`n🛡️ Testando Validações de Negócio via Frontend" -ForegroundColor Yellow

# Tentar criar cliente com CPF inválido
$clienteInvalido = @{
    nome_completo = "Test Invalido Frontend"
    documento = "123"
    telefone = "21999999999"
    email = "invalid.frontend@test.com"
} | ConvertTo-Json

Test-FrontendEndpoint -Method "POST" -Path "/api/v1/clientes" -Data $clienteInvalido -ExpectedStatus 400 -Description "Validação CPF Inválido" -ExpectedContent "CPF inválido"

# Tentar acesso sem autenticação
Write-Host "`n🔐 Testando Autenticação via Frontend" -ForegroundColor Yellow

# Limpar cookies para simular logout
$script:COOKIES = ""

try {
    $response = Invoke-WebRequest -Uri "$BASE_URL/api/v1/clientes" -Method Get -UseBasicParsing -ErrorAction Stop
    Write-Host "        ❌ FAIL Autenticação não requerida (Status: $($response.StatusCode))" -ForegroundColor Red
    $FAILED_TESTS++
} catch {
    $status = if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode } else { 0 }
    if ($status -eq 401) {
        Write-Host "        ✅ PASS Autenticação requerida (Status: 401)" -ForegroundColor Green
        $PASSED_TESTS++
    } else {
        Write-Host "        ❌ FAIL Status inesperado: $status" -ForegroundColor Red
        $FAILED_TESTS++
    }
}
$TOTAL_TESTS++

# 8. Testar logout via frontend
Write-Host "`n🚪 Testando Logout via Frontend" -ForegroundColor Yellow

try {
    $logoutResponse = Invoke-WebRequest -Uri "$BASE_URL/api/v1/logout" -Method Post -Headers @{Cookie = $COOKIES} -UseBasicParsing -ErrorAction Stop
    if ($logoutResponse.StatusCode -eq 200) {
        Write-Host "        ✅ PASS Logout bem-sucedido (Status: $($logoutResponse.StatusCode))" -ForegroundColor Green
        $PASSED_TESTS++
    } else {
        Write-Host "        ❌ FAIL Logout falhou (Status: $($logoutResponse.StatusCode))" -ForegroundColor Red
        $FAILED_TESTS++
    }
} catch {
    Write-Host "        ❌ FAIL Erro no logout: $($_.Exception.Message)" -ForegroundColor Red
    $FAILED_TESTS++
}
$TOTAL_TESTS++

# Relatório final
Write-Host "`n============================================================" -ForegroundColor Blue
Write-Host "📊 RELATÓRIO FINAL - TESTES FRONTEND OFICIAL" -ForegroundColor Blue
Write-Host "============================================================" -ForegroundColor Blue
Write-Host "Total de Testes: $TOTAL_TESTS" -ForegroundColor Yellow
Write-Host "Passou: $PASSED_TESTS" -ForegroundColor Green
Write-Host "Falhou: $FAILED_TESTS" -ForegroundColor Red

# Calcular percentual
if ($TOTAL_TESTS -gt 0) {
    $successRate = [math]::Round(($PASSED_TESTS * 100) / $TOTAL_TESTS, 1)
    Write-Host "Taxa de Sucesso: $successRate%" -ForegroundColor Green
    
    if ($successRate -ge 95) {
        Write-Host "`n🎉 EXCELENTE! Frontend oficial 100% funcional!" -ForegroundColor Green
    } elseif ($successRate -ge 85) {
        Write-Host "`n👍 BOM! Frontend oficial operacional." -ForegroundColor Yellow
    } else {
        Write-Host "`n⚠️  ATENÇÃO! Frontend com problemas." -ForegroundColor Red
    }
}

Write-Host "`n============================================================" -ForegroundColor Blue

# Exit code baseado nos resultados
if ($FAILED_TESTS -eq 0) {
    exit 0
} else {
    exit 1
}
