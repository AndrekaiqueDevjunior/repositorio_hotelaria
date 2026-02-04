# Teste Simples Frontend Oficial via PowerShell
Write-Host "Teste Frontend Oficial - PowerShell" -ForegroundColor Cyan
Write-Host "========================================"

$BASE_URL = "http://localhost:8080"
$TOTAL_TESTS = 0
$PASSED_TESTS = 0

# Teste 1: Pagina principal
Write-Host "`n[TEST 1] Pagina Principal" -ForegroundColor Blue
try {
    $response = Invoke-WebRequest -Uri "$BASE_URL/" -Method Get -UseBasicParsing -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host "        PASS (Status: 200)" -ForegroundColor Green
        $PASSED_TESTS++
    } else {
        Write-Host "        FAIL (Status: $($response.StatusCode))" -ForegroundColor Red
    }
} catch {
    Write-Host "        FAIL: $($_.Exception.Message)" -ForegroundColor Red
}
$TOTAL_TESTS++

# Teste 2: Pagina de login
Write-Host "`n[TEST 2] Pagina Login" -ForegroundColor Blue
try {
    $response = Invoke-WebRequest -Uri "$BASE_URL/login" -Method Get -UseBasicParsing -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host "        PASS (Status: 200)" -ForegroundColor Green
        $PASSED_TESTS++
    } else {
        Write-Host "        FAIL (Status: $($response.StatusCode))" -ForegroundColor Red
    }
} catch {
    Write-Host "        FAIL: $($_.Exception.Message)" -ForegroundColor Red
}
$TOTAL_TESTS++

# Teste 3: API sem autenticacao
Write-Host "`n[TEST 3] API sem autenticacao" -ForegroundColor Blue
try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/api/v1/clientes" -Method Get -ErrorAction Stop
    Write-Host "        FAIL (API nao protegida)" -ForegroundColor Red
} catch {
    $status = if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode } else { 0 }
    if ($status -eq 401) {
        Write-Host "        PASS (Status: 401 - Autenticacao requerida)" -ForegroundColor Green
        $PASSED_TESTS++
    } else {
        Write-Host "        FAIL (Status: $status)" -ForegroundColor Red
    }
}
$TOTAL_TESTS++

# Teste 4: Login via API
Write-Host "`n[TEST 4] Login via API" -ForegroundColor Blue
try {
    $loginData = @{
        email = "admin@hotelreal.com.br"
        password = "admin123"
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "$BASE_URL/api/v1/login" -Method Post -ContentType "application/json" -Body $loginData -ErrorAction Stop
    
    if ($response.refresh_token) {
        Write-Host "        PASS (Login bem-sucedido)" -ForegroundColor Green
        $PASSED_TESTS++
        
        # Teste 5: API com autenticacao
        Write-Host "`n[TEST 5] API com autenticacao" -ForegroundColor Blue
        try {
            $refreshData = @{refresh_token = $response.refresh_token} | ConvertTo-Json
            $refreshResponse = Invoke-RestMethod -Uri "$BASE_URL/api/v1/refresh" -Method Post -ContentType "application/json" -Body $refreshData -ErrorAction Stop
            
            if ($refreshResponse.access_token) {
                $token = $refreshResponse.access_token
                $headers = @{Authorization = "Bearer $token"}
                
                $apiResponse = Invoke-RestMethod -Uri "$BASE_URL/api/v1/dashboard/stats" -Method Get -Headers $headers -ErrorAction Stop
                Write-Host "        PASS (API autenticada funcionando)" -ForegroundColor Green
                $PASSED_TESTS++
            }
        } catch {
            Write-Host "        FAIL (API autenticada): $($_.Exception.Message)" -ForegroundColor Red
        }
        $TOTAL_TESTS++
    } else {
        Write-Host "        FAIL (Sem refresh_token)" -ForegroundColor Red
    }
} catch {
    Write-Host "        FAIL: $($_.Exception.Message)" -ForegroundColor Red
}
$TOTAL_TESTS++

# Relatorio final
Write-Host "`n========================================" -ForegroundColor Blue
Write-Host "RELATORIO FINAL" -ForegroundColor Blue
Write-Host "========================================" -ForegroundColor Blue
Write-Host "Total de Testes: $TOTAL_TESTS" -ForegroundColor Yellow
Write-Host "Passou: $PASSED_TESTS" -ForegroundColor Green
Write-Host "Falhou: $($TOTAL_TESTS - $PASSED_TESTS)" -ForegroundColor Red

if ($TOTAL_TESTS -gt 0) {
    $successRate = [math]::Round(($PASSED_TESTS * 100) / $TOTAL_TESTS, 1)
    Write-Host "Taxa de Sucesso: $successRate%" -ForegroundColor Green
    
    if ($successRate -ge 80) {
        Write-Host "`nFRONTEND OFICIAL FUNCIONAL!" -ForegroundColor Green
    }
}

Write-Host "`n========================================" -ForegroundColor Blue
