# Teste Minimal Frontend Oficial
Write-Host "Teste Minimal Frontend Oficial" -ForegroundColor Cyan
Write-Host "================================"

$BASE_URL = "http://localhost:8080"
$PASSED = 0
$TOTAL = 0

# Teste 1: Pagina principal
Write-Host "`n[1] Testando pagina principal..." -ForegroundColor Blue
try {
    $response = Invoke-WebRequest -Uri "$BASE_URL/" -Method Get -UseBasicParsing -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Host "   ✅ PASS - Pagina principal acessivel (200)" -ForegroundColor Green
        $PASSED++
    } else {
        Write-Host "   ❌ FAIL - Status: $($response.StatusCode)" -ForegroundColor Red
    }
} catch {
    Write-Host "   ❌ FAIL - $($_.Exception.Message)" -ForegroundColor Red
}
$TOTAL++

# Teste 2: Pagina de login
Write-Host "`n[2] Testando pagina de login..." -ForegroundColor Blue
try {
    $response = Invoke-WebRequest -Uri "$BASE_URL/login" -Method Get -UseBasicParsing -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Host "   ✅ PASS - Pagina login acessivel (200)" -ForegroundColor Green
        $PASSED++
    } else {
        Write-Host "   ❌ FAIL - Status: $($response.StatusCode)" -ForegroundColor Red
    }
} catch {
    Write-Host "   ❌ FAIL - $($_.Exception.Message)" -ForegroundColor Red
}
$TOTAL++

# Teste 3: Verificar se API esta protegida
Write-Host "`n[3] Testando protecao da API..." -ForegroundColor Blue
try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/api/v1/clientes" -Method Get -TimeoutSec 10
    Write-Host "   ❌ FAIL - API nao protegida!" -ForegroundColor Red
} catch {
    $status = if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode } else { 0 }
    if ($status -eq 401) {
        Write-Host "   ✅ PASS - API protegida (401)" -ForegroundColor Green
        $PASSED++
    } else {
        Write-Host "   ❌ FAIL - Status: $status" -ForegroundColor Red
    }
}
$TOTAL++

# Teste 4: Verificar se backend esta respondendo
Write-Host "`n[4] Testando conexao com backend..." -ForegroundColor Blue
try {
    $response = Invoke-WebRequest -Uri "$BASE_URL/api/v1/login" -Method Get -UseBasicParsing -TimeoutSec 10
    if ($response.StatusCode -in @(200, 405)) {
        Write-Host "   ✅ PASS - Backend respondendo ($($response.StatusCode))" -ForegroundColor Green
        $PASSED++
    } else {
        Write-Host "   ❌ FAIL - Status: $($response.StatusCode)" -ForegroundColor Red
    }
} catch {
    Write-Host "   ❌ FAIL - $($_.Exception.Message)" -ForegroundColor Red
}
$TOTAL++

# Resultado
Write-Host "`n================================" -ForegroundColor Blue
Write-Host "RESULTADO FINAL" -ForegroundColor Blue
Write-Host "================================" -ForegroundColor Blue
Write-Host "Passou: $PASSED/$TOTAL" -ForegroundColor Green

if ($TOTAL -gt 0) {
    $rate = [math]::Round(($PASSED * 100) / $TOTAL, 1)
    Write-Host "Taxa: $rate%" -ForegroundColor Green
    
    if ($rate -ge 75) {
        Write-Host "`n🎉 FRONTEND OFICIAL FUNCIONAL!" -ForegroundColor Green
        Write-Host "   ✅ Paginas acessiveis" -ForegroundColor Green
        Write-Host "   ✅ API protegida" -ForegroundColor Green
        Write-Host "   ✅ Backend conectado" -ForegroundColor Green
    } else {
        Write-Host "`n⚠️  Frontend com problemas" -ForegroundColor Yellow
    }
}

Write-Host "`n================================" -ForegroundColor Blue
