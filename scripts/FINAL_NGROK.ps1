# =========================================
# FINAL - ngrok FREE (1 tunel unico)
# =========================================

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  INICIANDO SISTEMA NGROK FREE" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/6] Rebuild completo..." -ForegroundColor Cyan
docker-compose build --no-cache backend frontend

Write-Host ""
Write-Host "[2/6] Iniciando todos os servicos..." -ForegroundColor Cyan
docker-compose --profile ngrok up -d --force-recreate --remove-orphans

Write-Host ""
Write-Host "[3/6] Aguardando inicializacao (45 segundos)..." -ForegroundColor Yellow
Start-Sleep -Seconds 45

Write-Host ""
Write-Host "[4/6] Obtendo URL do ngrok..." -ForegroundColor Cyan
$url = $null

for ($i = 1; $i -le 20; $i++) {
    try {
        $api = Invoke-RestMethod "http://localhost:4040/api/tunnels" -ErrorAction Stop
        if ($api.tunnels -and $api.tunnels.Count -gt 0) {
            $url = $api.tunnels[0].public_url
            break
        }
    } catch {}
    
    Write-Host "   Tentativa $i/20..." -ForegroundColor Gray
    Start-Sleep -Seconds 3
}

if (-not $url) {
    Write-Host ""
    Write-Host "[ERRO] Ngrok nao iniciou!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Diagnostico:" -ForegroundColor Yellow
    Write-Host "  docker-compose --profile ngrok ps" -ForegroundColor Gray
    Write-Host "  docker-compose logs ngrok" -ForegroundColor Gray
    Write-Host "  docker-compose logs nginx-proxy" -ForegroundColor Gray
    Write-Host ""
    exit 1
}

Write-Host ""
Write-Host "[OK] URL: $url" -ForegroundColor Green
Write-Host ""

Write-Host "[5/6] Configurando sistema..." -ForegroundColor Cyan

Set-Content "frontend\.env.local" "NEXT_PUBLIC_API_URL=$url/api/v1"

$be = Get-Content "backend\.env.docker" -Raw
$be = $be -replace "CORS_ORIGINS=.*", "CORS_ORIGINS=$url,http://localhost:3000"
$be = $be -replace "FRONTEND_URL=.*", "FRONTEND_URL=$url"
$be = $be -replace "COOKIE_SECURE=.*", "COOKIE_SECURE=True"
$be = $be -replace "COOKIE_SAMESITE=.*", "COOKIE_SAMESITE=none"
$be = $be -replace "COOKIE_DOMAIN=.*", "COOKIE_DOMAIN="
Set-Content "backend\.env.docker" $be

Write-Host "[RESTART] Aplicando configuracoes..." -ForegroundColor Cyan
docker-compose restart backend frontend
Start-Sleep -Seconds 15

Write-Host ""
Write-Host "[6/6] Testando sistema..." -ForegroundColor Cyan
Write-Host ""

Write-Host "[TEST 1/3] Frontend..." -ForegroundColor Cyan
try {
    $r = Invoke-WebRequest $url -UseBasicParsing -TimeoutSec 25 -ErrorAction Stop
    Write-Host "[OK] Status $($r.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "[ERRO] $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "[TEST 2/3] Backend Health..." -ForegroundColor Cyan
try {
    $r = Invoke-WebRequest "$url/health" -UseBasicParsing -TimeoutSec 25 -ErrorAction Stop
    Write-Host "[OK] Status $($r.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "[ERRO] $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "[TEST 3/3] Login API..." -ForegroundColor Cyan
try {
    $body = @{email="admin@hotelreal.com.br";password="admin123"} | ConvertTo-Json
    $r = Invoke-WebRequest "$url/api/v1/auth/login" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing -TimeoutSec 25 -ErrorAction Stop
    Write-Host "[OK] Status $($r.StatusCode) - JWT OK!" -ForegroundColor Green
} catch {
    Write-Host "[ERRO] $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "======================================" -ForegroundColor Green
Write-Host "  SISTEMA PRONTO!" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green
Write-Host ""
Write-Host "[URL PUBLICA]" -ForegroundColor Cyan
Write-Host "  $url" -ForegroundColor White
Write-Host ""
Write-Host "[LOGIN]" -ForegroundColor Yellow
Write-Host "  Email: admin@hotelreal.com.br" -ForegroundColor White
Write-Host "  Senha: admin123" -ForegroundColor White
Write-Host ""
Write-Host "[ARQUITETURA]" -ForegroundColor Cyan
Write-Host "  - 1 tunel ngrok (FREE)" -ForegroundColor Gray
Write-Host "  - Nginx proxy reverso" -ForegroundColor Gray
Write-Host "  - Frontend: $url" -ForegroundColor Gray
Write-Host "  - Backend: $url/api/v1" -ForegroundColor Gray
Write-Host "  - Health: $url/health" -ForegroundColor Gray
Write-Host ""
Write-Host "[DASHBOARD]" -ForegroundColor Cyan
Write-Host "  ngrok: http://localhost:4040" -ForegroundColor Gray
Write-Host "  Proxy: http://localhost:8080" -ForegroundColor Gray
Write-Host ""
Write-Host "[DADOS]" -ForegroundColor Green
Write-Host "  Banco de dados preservado!" -ForegroundColor White
Write-Host ""
Write-Host "[LOGS]" -ForegroundColor Cyan
Write-Host "  docker-compose logs -f" -ForegroundColor Gray
Write-Host ""
