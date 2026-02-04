# =========================================
# ngrok FREE - 1 Tunel Unico (Limpo)
# =========================================

Write-Host "[CLEANUP] Limpando sistema completamente..." -ForegroundColor Yellow
Write-Host ""

# Parar tudo
docker-compose down --remove-orphans 2>$null
docker stop $(docker ps -aq) 2>$null
docker rm $(docker ps -aq) 2>$null

Write-Host "[BUILD] Reconstruindo imagens..." -ForegroundColor Cyan
docker-compose build --no-cache backend frontend

Write-Host ""
Write-Host "[START] Iniciando sistema basico..." -ForegroundColor Cyan
docker-compose up -d postgres redis

Write-Host "[WAIT] Aguardando banco..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host "[START] Iniciando backend e frontend..." -ForegroundColor Cyan
docker-compose up -d backend frontend

Write-Host "[WAIT] Aguardando aplicacoes..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

Write-Host "[START] Iniciando nginx proxy..." -ForegroundColor Cyan
docker-compose --profile ngrok up -d nginx-proxy

Write-Host "[WAIT] Aguardando proxy..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host "[START] Iniciando ngrok..." -ForegroundColor Cyan
docker-compose --profile ngrok up -d ngrok

Write-Host "[WAIT] Aguardando ngrok (30 segundos)..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Obter URL
Write-Host ""
Write-Host "[API] Buscando URL do ngrok..." -ForegroundColor Cyan

$maxRetries = 10
$ngrokUrl = $null

for ($i = 1; $i -le $maxRetries; $i++) {
    try {
        $api = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels" -ErrorAction Stop
        
        if ($api.tunnels.Count -gt 0) {
            $ngrokUrl = $api.tunnels[0].public_url
            break
        }
    } catch {
        Write-Host "[RETRY] Tentativa $i/$maxRetries..." -ForegroundColor Gray
    }
    Start-Sleep -Seconds 3
}

if (-not $ngrokUrl) {
    Write-Host ""
    Write-Host "[ERROR] Ngrok nao iniciou!" -ForegroundColor Red
    Write-Host "[CHECK] Verifique:" -ForegroundColor Yellow
    Write-Host "   docker-compose logs ngrok" -ForegroundColor Gray
    Write-Host "   http://localhost:4040" -ForegroundColor Gray
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "[OK] URL NGROK OBTIDA!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "   $ngrokUrl" -ForegroundColor White
Write-Host ""

# Configurar .env
Write-Host "[CONFIG] Configurando sistema..." -ForegroundColor Cyan

# Frontend
Set-Content -Path "frontend\.env.local" -Value "NEXT_PUBLIC_API_URL=$ngrokUrl/api/v1"

# Backend
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
Write-Host "[TEST] TESTANDO..." -ForegroundColor Green
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
    Write-Host "[OK] $($r.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "[ERRO] $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "[OK] SISTEMA PRONTO!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "[SHARE]" -ForegroundColor Cyan
Write-Host "   URL: $ngrokUrl" -ForegroundColor White
Write-Host "   Login: admin@hotelreal.com.br" -ForegroundColor White
Write-Host "   Senha: admin123" -ForegroundColor White
Write-Host ""
Write-Host "[INFO]" -ForegroundColor Yellow
Write-Host "   - 1 tunel ngrok (FREE)" -ForegroundColor Gray
Write-Host "   - Frontend: $ngrokUrl" -ForegroundColor Gray
Write-Host "   - Backend: $ngrokUrl/api/v1" -ForegroundColor Gray
Write-Host "   - Dashboard: http://localhost:4040" -ForegroundColor Gray
Write-Host ""
