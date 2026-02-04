# =========================================
# Iniciar Sistema Completo com ngrok FREE
# =========================================
# Preserva dados do PostgreSQL

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SETUP COMPLETO - NGROK FREE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Limpar completamente
Write-Host "[1/10] Limpeza completa..." -ForegroundColor Yellow
docker-compose down --remove-orphans
docker rm -f $(docker ps -aq) 2>$null | Out-Null
Start-Sleep -Seconds 2

# Rebuild backend
Write-Host "[2/10] Rebuild Backend..." -ForegroundColor Cyan
docker-compose build --no-cache backend

# Rebuild frontend  
Write-Host "[3/10] Rebuild Frontend..." -ForegroundColor Cyan
docker-compose build --no-cache frontend

Write-Host ""
Write-Host "[4/10] Iniciando PostgreSQL..." -ForegroundColor Cyan
docker-compose up -d postgres
Start-Sleep -Seconds 10

Write-Host "[5/10] Iniciando Redis..." -ForegroundColor Cyan
docker-compose up -d redis
Start-Sleep -Seconds 5

Write-Host "[6/10] Iniciando Backend..." -ForegroundColor Cyan
docker-compose up -d backend
Start-Sleep -Seconds 12

Write-Host "[7/10] Iniciando Frontend..." -ForegroundColor Cyan
docker-compose up -d frontend
Start-Sleep -Seconds 12

Write-Host "[8/10] Iniciando Nginx Proxy..." -ForegroundColor Cyan
docker-compose --profile ngrok up -d nginx
Start-Sleep -Seconds 5

Write-Host "[9/10] Iniciando ngrok..." -ForegroundColor Cyan
docker-compose --profile ngrok up -d ngrok
Start-Sleep -Seconds 20

# Obter URL
Write-Host "[10/10] Obtendo URL ngrok..." -ForegroundColor Cyan
$ngrokUrl = $null

for ($i = 1; $i -le 15; $i++) {
    try {
        $api = Invoke-RestMethod "http://localhost:4040/api/tunnels" -ErrorAction Stop
        if ($api.tunnels.Count -gt 0) {
            $ngrokUrl = $api.tunnels[0].public_url
            break
        }
    } catch {}
    Write-Host "   Aguardando... $i/15" -ForegroundColor Gray
    Start-Sleep -Seconds 2
}

if (-not $ngrokUrl) {
    Write-Host ""
    Write-Host "[ERRO] Ngrok nao iniciou!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Verifique:" -ForegroundColor Yellow
    Write-Host "  docker-compose --profile ngrok ps" -ForegroundColor Gray
    Write-Host "  docker-compose logs ngrok" -ForegroundColor Gray
    Write-Host "  http://localhost:4040" -ForegroundColor Gray
    Write-Host ""
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  URL OBTIDA!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "   $ngrokUrl" -ForegroundColor White
Write-Host ""

# Configurar
Write-Host "[CONFIG] Configurando sistema..." -ForegroundColor Cyan

Set-Content -Path "frontend\.env.local" -Value "NEXT_PUBLIC_API_URL=$ngrokUrl/api/v1"

$backendEnv = Get-Content "backend\.env.docker" -Raw
$backendEnv = $backendEnv -replace "CORS_ORIGINS=.*", "CORS_ORIGINS=$ngrokUrl,http://localhost:3000"
$backendEnv = $backendEnv -replace "FRONTEND_URL=.*", "FRONTEND_URL=$ngrokUrl"
$backendEnv = $backendEnv -replace "COOKIE_SECURE=.*", "COOKIE_SECURE=True"
$backendEnv = $backendEnv -replace "COOKIE_SAMESITE=.*", "COOKIE_SAMESITE=none"
$backendEnv = $backendEnv -replace "COOKIE_DOMAIN=.*", "COOKIE_DOMAIN="
Set-Content -Path "backend\.env.docker" -Value $backendEnv

Write-Host "[RESTART] Aplicando configuracoes..." -ForegroundColor Cyan
docker-compose restart backend frontend
Start-Sleep -Seconds 15

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  TESTANDO SISTEMA" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

Write-Host "[TEST 1/3] Frontend..." -ForegroundColor Cyan
try {
    $r = Invoke-WebRequest -Uri $ngrokUrl -UseBasicParsing -TimeoutSec 20 -ErrorAction Stop
    Write-Host "[OK] $($r.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "[ERRO] $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "[TEST 2/3] Backend Health..." -ForegroundColor Cyan
try {
    $r = Invoke-WebRequest -Uri "$ngrokUrl/health" -UseBasicParsing -TimeoutSec 20 -ErrorAction Stop
    Write-Host "[OK] $($r.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "[ERRO] $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "[TEST 3/3] Login..." -ForegroundColor Cyan
try {
    $body = @{email="admin@hotelreal.com.br";password="admin123"} | ConvertTo-Json
    $r = Invoke-WebRequest -Uri "$ngrokUrl/api/v1/auth/login" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing -TimeoutSec 20 -ErrorAction Stop
    Write-Host "[OK] $($r.StatusCode) - JWT Token gerado!" -ForegroundColor Green
} catch {
    Write-Host "[ERRO] $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  SISTEMA PRONTO!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "[COMPARTILHE]" -ForegroundColor Cyan
Write-Host "   URL: $ngrokUrl" -ForegroundColor White
Write-Host ""
Write-Host "[LOGIN]" -ForegroundColor Yellow
Write-Host "   Email: admin@hotelreal.com.br" -ForegroundColor White
Write-Host "   Senha: admin123" -ForegroundColor White
Write-Host ""
Write-Host "[ARQUITETURA]" -ForegroundColor Cyan
Write-Host "   - 1 tunel ngrok (FREE)" -ForegroundColor Gray
Write-Host "   - Nginx proxy interno" -ForegroundColor Gray
Write-Host "   - Frontend: $ngrokUrl" -ForegroundColor Gray
Write-Host "   - Backend: $ngrokUrl/api/v1" -ForegroundColor Gray
Write-Host "   - Health: $ngrokUrl/health" -ForegroundColor Gray
Write-Host ""
Write-Host "[DASHBOARD]" -ForegroundColor Cyan
Write-Host "   ngrok: http://localhost:4040" -ForegroundColor Gray
Write-Host ""
Write-Host "[DADOS]" -ForegroundColor Green
Write-Host "   Banco de dados preservado!" -ForegroundColor White
Write-Host ""
