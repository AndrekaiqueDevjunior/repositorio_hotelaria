# =========================================
# ngrok com Proxy Reverso - 1 Tunel Unico
# =========================================
# Solucao para ngrok FREE (1 tunel)
# Frontend + Backend em 1 URL

Write-Host "[INICIO] Iniciando sistema com ngrok (1 tunel)..." -ForegroundColor Cyan
Write-Host ""

# Parar containers existentes
Write-Host "[CLEANUP] Parando containers existentes..." -ForegroundColor Yellow
docker-compose down

# Iniciar com perfil ngrok
Write-Host "[DOCKER] Iniciando containers com nginx proxy..." -ForegroundColor Cyan
docker-compose --profile ngrok up -d

Write-Host ""
Write-Host "[WAIT] Aguardando containers iniciarem (30 segundos)..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Obter URL do ngrok
Write-Host "[API] Obtendo URL do ngrok..." -ForegroundColor Cyan
Start-Sleep -Seconds 5

$maxRetries = 10
$retry = 0
$ngrokUrl = $null

while ($retry -lt $maxRetries) {
    try {
        $api = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels" -ErrorAction Stop
        
        if ($api.tunnels.Count -gt 0) {
            $ngrokUrl = $api.tunnels[0].public_url
            break
        }
        
        Write-Host "[RETRY] Aguardando ngrok... ($($retry + 1)/$maxRetries)" -ForegroundColor Yellow
        Start-Sleep -Seconds 3
        $retry++
        
    } catch {
        Write-Host "[RETRY] API ngrok nao disponivel... ($($retry + 1)/$maxRetries)" -ForegroundColor Yellow
        Start-Sleep -Seconds 3
        $retry++
    }
}

if (-not $ngrokUrl) {
    Write-Host ""
    Write-Host "[ERROR] Nao foi possivel obter URL do ngrok!" -ForegroundColor Red
    Write-Host "[INFO] Verifique: http://localhost:4040" -ForegroundColor Yellow
    Write-Host "[INFO] Logs: docker-compose logs ngrok" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "[OK] SISTEMA CONFIGURADO!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "[URL UNICA]" -ForegroundColor Cyan
Write-Host "   $ngrokUrl" -ForegroundColor White
Write-Host ""
Write-Host "[IMPORTANTE]" -ForegroundColor Yellow
Write-Host "   Frontend: $ngrokUrl" -ForegroundColor Gray
Write-Host "   Backend API: $ngrokUrl/api/v1" -ForegroundColor Gray
Write-Host "   Backend Health: $ngrokUrl/health" -ForegroundColor Gray
Write-Host ""

# Configurar .env do frontend
Write-Host "[CONFIG] Atualizando configuracao frontend..." -ForegroundColor Cyan

$frontendEnvFile = "$PSScriptRoot\frontend\.env.local"
Set-Content -Path $frontendEnvFile -Value "NEXT_PUBLIC_API_URL=$ngrokUrl/api/v1"

Write-Host "[OK] Frontend configurado" -ForegroundColor Green
Write-Host ""

# Configurar .env do backend
Write-Host "[CONFIG] Atualizando configuracao backend..." -ForegroundColor Cyan

$backendEnvFile = "$PSScriptRoot\backend\.env.docker"
$backendEnv = Get-Content $backendEnvFile -Raw

$corsOrigins = "$ngrokUrl,http://localhost:3000"
if ($backendEnv -match "CORS_ORIGINS=.*") {
    $backendEnv = $backendEnv -replace "CORS_ORIGINS=.*", "CORS_ORIGINS=$corsOrigins"
} else {
    $backendEnv += "`nCORS_ORIGINS=$corsOrigins"
}

if ($backendEnv -match "FRONTEND_URL=.*") {
    $backendEnv = $backendEnv -replace "FRONTEND_URL=.*", "FRONTEND_URL=$ngrokUrl"
} else {
    $backendEnv += "`nFRONTEND_URL=$ngrokUrl"
}

$backendEnv = $backendEnv -replace "COOKIE_SECURE=.*", "COOKIE_SECURE=True"
$backendEnv = $backendEnv -replace "COOKIE_SAMESITE=.*", "COOKIE_SAMESITE=none"
$backendEnv = $backendEnv -replace "COOKIE_DOMAIN=.*", "COOKIE_DOMAIN="

Set-Content -Path $backendEnvFile -Value $backendEnv

Write-Host "[OK] Backend configurado" -ForegroundColor Green
Write-Host ""

# Reiniciar backend e frontend
Write-Host "[RESTART] Aplicando configuracoes..." -ForegroundColor Cyan
docker-compose restart backend frontend
Start-Sleep -Seconds 15

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "[TEST] TESTANDO SISTEMA..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Teste 1: Frontend
Write-Host "[TEST 1/4] Frontend..." -ForegroundColor Cyan
try {
    $test1 = Invoke-WebRequest -Uri $ngrokUrl -UseBasicParsing -TimeoutSec 20 -ErrorAction Stop
    Write-Host "[OK] Frontend: $($test1.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Frontend: $($_.Exception.Message)" -ForegroundColor Red
}

# Teste 2: Backend Health
Write-Host "[TEST 2/4] Backend Health..." -ForegroundColor Cyan
try {
    $test2 = Invoke-WebRequest -Uri "$ngrokUrl/health" -UseBasicParsing -TimeoutSec 20 -ErrorAction Stop
    Write-Host "[OK] Backend Health: $($test2.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Backend Health: $($_.Exception.Message)" -ForegroundColor Red
}

# Teste 3: Backend API
Write-Host "[TEST 3/4] Backend API..." -ForegroundColor Cyan
try {
    $loginBody = @{
        email = "admin@hotelreal.com.br"
        password = "admin123"
    } | ConvertTo-Json

    $test3 = Invoke-WebRequest -Uri "$ngrokUrl/api/v1/auth/login" -Method POST -Body $loginBody -ContentType "application/json" -UseBasicParsing -TimeoutSec 20 -ErrorAction Stop
    Write-Host "[OK] Login API: $($test3.StatusCode)" -ForegroundColor Green
    
    $loginData = $test3.Content | ConvertFrom-Json
    if ($loginData.access_token) {
        Write-Host "[OK] JWT Token gerado!" -ForegroundColor Green
    }
} catch {
    Write-Host "[ERROR] Login API: $($_.Exception.Message)" -ForegroundColor Red
}

# Teste 4: Nginx Proxy
Write-Host "[TEST 4/4] Nginx Proxy Local..." -ForegroundColor Cyan
try {
    $test4 = Invoke-WebRequest -Uri "http://localhost:8080/health" -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
    Write-Host "[OK] Nginx Proxy: $($test4.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Nginx Proxy: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "[OK] SISTEMA PRONTO!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "[SHARE] Compartilhe esta URL:" -ForegroundColor Cyan
Write-Host ""
Write-Host "   $ngrokUrl" -ForegroundColor White
Write-Host ""
Write-Host "[LOGIN]" -ForegroundColor Yellow
Write-Host "   Email: admin@hotelreal.com.br" -ForegroundColor White
Write-Host "   Senha: admin123" -ForegroundColor White
Write-Host ""
Write-Host "[DASHBOARD]" -ForegroundColor Cyan
Write-Host "   ngrok: http://localhost:4040" -ForegroundColor Gray
Write-Host "   Proxy local: http://localhost:8080" -ForegroundColor Gray
Write-Host ""
Write-Host "[LOGS]" -ForegroundColor Cyan
Write-Host "   docker-compose logs -f" -ForegroundColor Gray
Write-Host "   docker-compose logs -f ngrok" -ForegroundColor Gray
Write-Host "   docker-compose logs -f nginx-proxy" -ForegroundColor Gray
Write-Host ""
Write-Host "[IMPORTANTE]" -ForegroundColor Yellow
Write-Host "   - 1 tunel ngrok unificado (FREE)" -ForegroundColor Gray
Write-Host "   - Frontend e Backend na mesma URL" -ForegroundColor Gray
Write-Host "   - HTTPS automatico via ngrok" -ForegroundColor Gray
Write-Host "   - Nginx faz proxy reverso interno" -ForegroundColor Gray
Write-Host ""
Write-Host "Pressione Enter para sair..." -ForegroundColor Yellow
Read-Host
