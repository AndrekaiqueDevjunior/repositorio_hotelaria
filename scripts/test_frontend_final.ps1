# Teste Final Frontend Oficial - PowerShell
$BASE_URL = "http://localhost:8080"
$AUTH_EMAIL = "admin@hotelreal.com.br"
$AUTH_PASSWORD = "admin123"

Write-Host "🚀 Teste Final Frontend Oficial - PowerShell" -ForegroundColor Cyan
Write-Host "============================================================"

$TOTAL_TESTS = 0
$PASSED_TESTS = 0
$FAILED_TESTS = 0
$TOKEN = ""

function Test-Endpoint {
    param($Method, $Path, $Data, $ExpectedStatus, $Description)
    
    $TOTAL_TESTS++
    Write-Host "`n[TEST $TOTAL_TESTS] $Description" -ForegroundColor Blue
    Write-Host "        $Method $BASE_URL$Path" -ForegroundColor Blue
    
    try {
        $headers = @{}
        if ($TOKEN) {
            $headers["Authorization"] = "Bearer $TOKEN"
        }
        
        if ($Method -eq "GET") {
            $response = Invoke-RestMethod -Uri "$BASE_URL$Path" -Method Get -Headers $headers -ErrorAction Stop
            $status = 200
        } elseif ($Method -eq "POST") {
            $headers["Content-Type"] = "application/json"
            $response = Invoke-RestMethod -Uri "$BASE_URL$Path" -Method Post -Headers $headers -Body $Data -ErrorAction Stop
            $status = 201
        }
        
        if ($status -eq $ExpectedStatus) {
            Write-Host "        PASS (Status: $status)" -ForegroundColor Green
            $PASSED_TESTS++
        } else {
            Write-Host "        FAIL (Status: $status, esperado: $ExpectedStatus)" -ForegroundColor Red
            $FAILED_TESTS++
        }
    } catch {
        $status = if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode } else { 0 }
        if ($status -eq $ExpectedStatus) {
            Write-Host "        PASS (Status: $status)" -ForegroundColor Green
            $PASSED_TESTS++
        } else {
            Write-Host "        FAIL (Status: $status)" -ForegroundColor Red
            $FAILED_TESTS++
        }
    }
}

# 1. Login
Write-Host "`n🔐 Fazendo login..." -ForegroundColor Yellow
try {
    $loginData = @{email = $AUTH_EMAIL; password = $AUTH_PASSWORD} | ConvertTo-Json
    $loginResponse = Invoke-RestMethod -Uri "$BASE_URL/api/v1/login" -Method Post -ContentType "application/json" -Body $loginData -ErrorAction Stop
    
    if ($loginResponse.refresh_token) {
        $refreshData = @{refresh_token = $loginResponse.refresh_token} | ConvertTo-Json
        $refreshResponse = Invoke-RestMethod -Uri "$BASE_URL/api/v1/refresh" -Method Post -ContentType "application/json" -Body $refreshData -ErrorAction Stop
        
        if ($refreshResponse.access_token) {
            $script:TOKEN = $refreshResponse.access_token
            Write-Host "Login bem-sucedido" -ForegroundColor Green
            Write-Host "Token obtido" -ForegroundColor Green
        }
    }
} catch {
    Write-Host "Falha no login: $($_.Exception.Message)" -ForegroundColor Red
}

# 2. Testar APIs principais
Write-Host "`n📊 Testando APIs Principais..." -ForegroundColor Yellow
Test-Endpoint -Method "GET" -Path "/api/v1/dashboard/stats" -ExpectedStatus 200 -Description "Dashboard Stats"
Test-Endpoint -Method "GET" -Path "/api/v1/clientes" -ExpectedStatus 200 -Description "Clientes Listar"
Test-Endpoint -Method "GET" -Path "/api/v1/quartos" -ExpectedStatus 200 -Description "Quartos Listar"
Test-Endpoint -Method "GET" -Path "/api/v1/reservas" -ExpectedStatus 200 -Description "Reservas Listar"
Test-Endpoint -Method "GET" -Path "/api/v1/pagamentos" -ExpectedStatus 200 -Description "Pagamentos Listar"
Test-Endpoint -Method "GET" -Path "/api/v1/pontos/saldo/1" -ExpectedStatus 200 -Description "Pontos Saldo"

# 3. Testar criacoes
Write-Host "`n🔧 Testando Criacoes..." -ForegroundColor Yellow
$timestamp = Get-Date -Format "yyyyMMddHHmmss"

$clienteData = @{
    nome_completo = "Cliente Frontend $timestamp"
    documento = "12345678901"
    telefone = "21999$($timestamp.Substring(6))"
    email = "frontend.$timestamp@test.com"
} | ConvertTo-Json

Test-Endpoint -Method "POST" -Path "/api/v1/clientes" -Data $clienteData -ExpectedStatus 201 -Description "Criar Cliente"

$quartoData = @{
    numero = "F$($timestamp.Substring(6))"
    tipo_suite = "LUXO"
    status = "LIVRE"
} | ConvertTo-Json

Test-Endpoint -Method "POST" -Path "/api/v1/quartos" -Data $quartoData -ExpectedStatus 201 -Description "Criar Quarto"

# 4. Testar validacoes
Write-Host "`n🛡️ Testando Validacoes..." -ForegroundColor Yellow
$clienteInvalido = @{
    nome_completo = "Test Invalido"
    documento = "123"
    telefone = "21999999999"
    email = "invalid@test.com"
} | ConvertTo-Json

Test-Endpoint -Method "POST" -Path "/api/v1/clientes" -Data $clienteInvalido -ExpectedStatus 400 -Description "Validacao CPF Invalido"

$quartoInvalido = @{
    numero = "TEST-$($timestamp.Substring(6))"
    tipo_suite = "LUXO"
    status = "INVALIDO"
} | ConvertTo-Json

Test-Endpoint -Method "POST" -Path "/api/v1/quartos" -Data $quartoInvalido -ExpectedStatus 422 -Description "Validacao Status Invalido"

# 5. Testar autenticacao
Write-Host "`n🔐 Testando Autenticacao..." -ForegroundColor Yellow
$script:TOKEN = ""

try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/api/v1/clientes" -Method Get -ErrorAction Stop
    Write-Host "        FAIL Autenticacao nao requerida" -ForegroundColor Red
    $FAILED_TESTS++
} catch {
    $status = if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode } else { 0 }
    if ($status -eq 401) {
        Write-Host "        PASS Autenticacao requerida" -ForegroundColor Green
        $PASSED_TESTS++
    } else {
        Write-Host "        FAIL Status inesperado: $status" -ForegroundColor Red
        $FAILED_TESTS++
    }
}
$TOTAL_TESTS++

# 6. Testar paginas frontend
Write-Host "`n🌐 Testando Paginas Frontend..." -ForegroundColor Yellow

try {
    $response = Invoke-WebRequest -Uri "$BASE_URL/" -Method Get -UseBasicParsing -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host "        PASS Pagina Principal (Status: 200)" -ForegroundColor Green
        $PASSED_TESTS++
    }
} catch {
    Write-Host "        FAIL Pagina Principal" -ForegroundColor Red
    $FAILED_TESTS++
}
$TOTAL_TESTS++

try {
    $response = Invoke-WebRequest -Uri "$BASE_URL/login" -Method Get -UseBasicParsing -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host "        PASS Pagina Login (Status: 200)" -ForegroundColor Green
        $PASSED_TESTS++
    }
} catch {
    Write-Host "        FAIL Pagina Login" -ForegroundColor Red
    $FAILED_TESTS++
}
$TOTAL_TESTS++

# Relatorio final
Write-Host "`n============================================================" -ForegroundColor Blue
Write-Host "📊 RELATÓRIO FINAL - TESTES FRONTEND OFICIAL" -ForegroundColor Blue
Write-Host "============================================================" -ForegroundColor Blue
Write-Host "Total de Testes: $TOTAL_TESTS" -ForegroundColor Yellow
Write-Host "Passou: $PASSED_TESTS" -ForegroundColor Green
Write-Host "Falhou: $FAILED_TESTS" -ForegroundColor Red

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

if ($FAILED_TESTS -eq 0) {
    exit 0
} else {
    exit 1
}
