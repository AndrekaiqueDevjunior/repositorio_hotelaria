# Testes Frontend Oficial via PowerShell
$BASE_URL = "http://localhost:8080"
$AUTH_EMAIL = "admin@hotelreal.com.br"
$AUTH_PASSWORD = "admin123"

$TOTAL_TESTS = 0
$PASSED_TESTS = 0
$FAILED_TESTS = 0
$COOKIES = ""

function Test-Endpoint {
    param($Method, $Path, $Data, $ExpectedStatus, $Description)
    
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
        } elseif ($Method -eq "POST") {
            $headers["Content-Type"] = "application/json"
            $response = Invoke-WebRequest -Uri "$BASE_URL$Path" -Method Post -Headers $headers -Body $Data -UseBasicParsing -ErrorAction Stop
        }
        
        $status = [int]$response.StatusCode
        
        if ($response.Headers["Set-Cookie"]) {
            $script:COOKIES = $response.Headers["Set-Cookie"]
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

Write-Host "Testando Frontend Oficial via PowerShell" -ForegroundColor Cyan
Write-Host "============================================================"

# Testar pagina principal
Test-Endpoint -Method "GET" -Path "/" -ExpectedStatus 200 -Description "Pagina Principal"

# Testar login
Test-Endpoint -Method "GET" -Path "/login" -ExpectedStatus 200 -Description "Pagina Login"

# Fazer login
Write-Host "`nFazendo login..." -ForegroundColor Yellow
try {
    $loginData = @{email = $AUTH_EMAIL; password = $AUTH_PASSWORD} | ConvertTo-Json
    $loginResponse = Invoke-WebRequest -Uri "$BASE_URL/api/v1/login" -Method Post -ContentType "application/json" -Body $loginData -UseBasicParsing -ErrorAction Stop
    
    if ($loginResponse.StatusCode -eq 200 -and $loginResponse.Headers["Set-Cookie"]) {
        $script:COOKIES = $loginResponse.Headers["Set-Cookie"]
        Write-Host "Login bem-sucedido" -ForegroundColor Green
    }
} catch {
    Write-Host "Falha no login" -ForegroundColor Red
}

# Testar paginas protegidas
Test-Endpoint -Method "GET" -Path "/dashboard" -ExpectedStatus 200 -Description "Dashboard"
Test-Endpoint -Method "GET" -Path "/dashboard/clientes" -ExpectedStatus 200 -Description "Clientes Dashboard"
Test-Endpoint -Method "GET" -Path "/dashboard/reservas" -ExpectedStatus 200 -Description "Reservas Dashboard"
Test-Endpoint -Method "GET" -Path "/dashboard/quartos" -ExpectedStatus 200 -Description "Quartos Dashboard"
Test-Endpoint -Method "GET" -Path "/dashboard/pagamentos" -ExpectedStatus 200 -Description "Pagamentos Dashboard"
Test-Endpoint -Method "GET" -Path "/dashboard/pontos" -ExpectedStatus 200 -Description "Pontos Dashboard"

# Testar APIs
Write-Host "`nTestando APIs..." -ForegroundColor Yellow
Test-Endpoint -Method "GET" -Path "/api/v1/dashboard/stats" -ExpectedStatus 200 -Description "API Dashboard Stats"
Test-Endpoint -Method "GET" -Path "/api/v1/clientes" -ExpectedStatus 200 -Description "API Clientes"
Test-Endpoint -Method "GET" -Path "/api/v1/quartos" -ExpectedStatus 200 -Description "API Quartos"
Test-Endpoint -Method "GET" -Path "/api/v1/reservas" -ExpectedStatus 200 -Description "API Reservas"
Test-Endpoint -Method "GET" -Path "/api/v1/pagamentos" -ExpectedStatus 200 -Description "API Pagamentos"
Test-Endpoint -Method "GET" -Path "/api/v1/pontos/saldo/1" -ExpectedStatus 200 -Description "API Pontos Saldo"

# Testar criacao
Write-Host "`nTestando Criacao..." -ForegroundColor Yellow
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

# Testar validacoes
Write-Host "`nTestando Validacoes..." -ForegroundColor Yellow
$clienteInvalido = @{
    nome_completo = "Test Invalido"
    documento = "123"
    telefone = "21999999999"
    email = "invalid@test.com"
} | ConvertTo-Json

Test-Endpoint -Method "POST" -Path "/api/v1/clientes" -Data $clienteInvalido -ExpectedStatus 400 -Description "Validacao CPF Invalido"

# Testar autenticacao
Write-Host "`nTestando Autenticacao..." -ForegroundColor Yellow
$script:COOKIES = ""

try {
    $response = Invoke-WebRequest -Uri "$BASE_URL/api/v1/clientes" -Method Get -UseBasicParsing -ErrorAction Stop
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

# Relatorio
Write-Host "`n============================================================" -ForegroundColor Blue
Write-Host "RELATORIO FINAL - TESTES FRONTEND OFICIAL" -ForegroundColor Blue
Write-Host "============================================================" -ForegroundColor Blue
Write-Host "Total de Testes: $TOTAL_TESTS" -ForegroundColor Yellow
Write-Host "Passou: $PASSED_TESTS" -ForegroundColor Green
Write-Host "Falhou: $FAILED_TESTS" -ForegroundColor Red

if ($TOTAL_TESTS -gt 0) {
    $successRate = [math]::Round(($PASSED_TESTS * 100) / $TOTAL_TESTS, 1)
    Write-Host "Taxa de Sucesso: $successRate%" -ForegroundColor Green
    
    if ($successRate -ge 95) {
        Write-Host "`nEXCELENTE! Frontend oficial 100% funcional!" -ForegroundColor Green
    } elseif ($successRate -ge 85) {
        Write-Host "`nBOM! Frontend oficial operacional." -ForegroundColor Yellow
    } else {
        Write-Host "`nATENCAO! Frontend com problemas." -ForegroundColor Red
    }
}

Write-Host "`n============================================================" -ForegroundColor Blue

if ($FAILED_TESTS -eq 0) {
    exit 0
} else {
    exit 1
}
