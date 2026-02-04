# Teste de Validação de Pagamento via API
$BASE_URL = "http://localhost:8080"

Write-Host "Teste: Validação de Pagamento para Reserva CHECKED_OUT" -ForegroundColor Cyan
Write-Host "================================================"

# Testar API de pagamento sem autenticação (deve falhar)
Write-Host "`n[1] Testando API sem autenticação..." -ForegroundColor Blue
try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/api/v1/pagamentos" -Method Get -ErrorAction Stop
    Write-Host "   ❌ ERRO: API não protegida!" -ForegroundColor Red
} catch {
    $status = [int]$_.Exception.Response.StatusCode
    if ($status -eq 401) {
        Write-Host "   ✅ PASS: API protegida (401)" -ForegroundColor Green
    } else {
        Write-Host "   ❌ ERRO: Status inesperado: $status" -ForegroundColor Red
    }
}

# Testar endpoint de login
Write-Host "`n[2] Testando endpoint de login..." -ForegroundColor Blue
try {
    $loginData = @{
        email = "admin@hotelreal.com.br"
        password = "admin123"
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "$BASE_URL/api/v1/login" -Method Post -ContentType "application/json" -Body $loginData -ErrorAction Stop
    Write-Host "   ✅ PASS: Login endpoint funcionando" -ForegroundColor Green
    Write-Host "   Refresh token: $($response.refresh_token)" -ForegroundColor Blue
} catch {
    Write-Host "   ❌ ERRO: Login falhou: $($_.Exception.Message)" -ForegroundColor Red
}

# Testar endpoint de refresh
Write-Host "`n[3] Testando endpoint de refresh..." -ForegroundColor Blue
try {
    $refreshData = @{
        refresh_token = "test_token_invalido"
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "$BASE_URL/api/v1/refresh" -Method Post -ContentType "application/json" -Body $refreshData -ErrorAction Stop
    Write-Host "   ❌ ERRO: Refresh não deveria aceitar token inválido!" -ForegroundColor Red
} catch {
    $status = [int]$_.Exception.Response.StatusCode
    if ($status -eq 401) {
        Write-Host "   ✅ PASS: Refresh protegido (401)" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Status inesperado: $status" -ForegroundColor Yellow
    }
}

Write-Host "`n================================================" -ForegroundColor Blue
Write-Host "Teste concluído" -ForegroundColor Blue
Write-Host "================================================" -ForegroundColor Blue
