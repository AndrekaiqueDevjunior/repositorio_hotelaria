# =========================================
# ngrok Completo - Acesso Externo
# =========================================

Write-Host "[INICIO] Iniciando ngrok..." -ForegroundColor Cyan
Write-Host ""

# Verificar containers
Write-Host "[INFO] Verificando containers..." -ForegroundColor Yellow
docker-compose ps --filter "status=running"

Write-Host ""
Write-Host "[SETUP] Iniciando ngrok..." -ForegroundColor Cyan

# Matar processos ngrok existentes
Get-Process | Where-Object { $_.ProcessName -like "*ngrok*" } | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Iniciar ngrok para frontend em uma nova janela
Write-Host "[TUNNEL] Iniciando tunnel frontend (porta 3000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "ngrok http 3000"

Start-Sleep -Seconds 5

# Iniciar ngrok para backend em outra janela
Write-Host "[TUNNEL] Iniciando tunnel backend (porta 8000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "ngrok http 8000"

Start-Sleep -Seconds 5

# Obter URLs da API
Write-Host ""
Write-Host "[API] Obtendo URLs..." -ForegroundColor Cyan
Start-Sleep -Seconds 3

try {
    $api = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels" -ErrorAction Stop
    
    $frontendTunnel = $api.tunnels | Where-Object { $_.config.addr -like "*3000" } | Select-Object -First 1
    $backendTunnel = $api.tunnels | Where-Object { $_.config.addr -like "*8000" } | Select-Object -First 1
    
    $frontendUrl = $frontendTunnel.public_url
    $backendUrl = $backendTunnel.public_url
    
    if (-not $frontendUrl) {
        Write-Host "[ERROR] Tunnel frontend nao encontrado!" -ForegroundColor Red
        Write-Host "[INFO] Verifique: http://localhost:4040" -ForegroundColor Yellow
        exit 1
    }
    
    if (-not $backendUrl) {
        Write-Host "[ERROR] Tunnel backend nao encontrado!" -ForegroundColor Red
        Write-Host "[INFO] Verifique: http://localhost:4040" -ForegroundColor Yellow
        exit 1
    }
    
} catch {
    Write-Host "[ERROR] Erro ao obter URLs do ngrok" -ForegroundColor Red
    Write-Host "[INFO] Erro: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "[INFO] Verifique: http://localhost:4040" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "[OK] NGROK INICIADO!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "[URLS] URLs Publicas:" -ForegroundColor Cyan
Write-Host "   Frontend: $frontendUrl" -ForegroundColor White
Write-Host "   Backend:  $backendUrl" -ForegroundColor White
Write-Host ""

# Configurar .env
Write-Host "[CONFIG] Atualizando configuracao..." -ForegroundColor Cyan

# Backend .env
$backendEnvFile = "$PSScriptRoot\backend\.env.docker"
$backendEnv = Get-Content $backendEnvFile -Raw

$corsOrigins = "$backendUrl,$frontendUrl,http://localhost:3000,http://localhost:8000"
if ($backendEnv -match "CORS_ORIGINS=.*") {
    $backendEnv = $backendEnv -replace "CORS_ORIGINS=.*", "CORS_ORIGINS=$corsOrigins"
} else {
    $backendEnv += "`nCORS_ORIGINS=$corsOrigins"
}

if ($backendEnv -match "FRONTEND_URL=.*") {
    $backendEnv = $backendEnv -replace "FRONTEND_URL=.*", "FRONTEND_URL=$frontendUrl"
} else {
    $backendEnv += "`nFRONTEND_URL=$frontendUrl"
}

$backendEnv = $backendEnv -replace "COOKIE_SECURE=.*", "COOKIE_SECURE=True"
$backendEnv = $backendEnv -replace "COOKIE_SAMESITE=.*", "COOKIE_SAMESITE=none"
$backendEnv = $backendEnv -replace "COOKIE_DOMAIN=.*", "COOKIE_DOMAIN="

Set-Content -Path $backendEnvFile -Value $backendEnv

# Frontend .env
$frontendEnvFile = "$PSScriptRoot\frontend\.env.local"
Set-Content -Path $frontendEnvFile -Value "NEXT_PUBLIC_API_URL=$backendUrl/api/v1"

Write-Host "[OK] Configuracao atualizada" -ForegroundColor Green
Write-Host ""

# Reiniciar containers
Write-Host "[RESTART] Reiniciando containers..." -ForegroundColor Cyan
docker-compose restart backend frontend
Start-Sleep -Seconds 10

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "[OK] SISTEMA PRONTO!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "[SHARE] Compartilhe:" -ForegroundColor Cyan
Write-Host ""
Write-Host "   Aplicacao: $frontendUrl" -ForegroundColor White
Write-Host "   API:       $backendUrl" -ForegroundColor White
Write-Host ""
Write-Host "[LOGIN]" -ForegroundColor Yellow
Write-Host "   Email: admin@hotelreal.com.br" -ForegroundColor White
Write-Host "   Senha: admin123" -ForegroundColor White
Write-Host ""
Write-Host "[DASHBOARD] http://localhost:4040" -ForegroundColor Cyan
Write-Host ""

# Testar URLs
Write-Host "[TEST] Testando URLs..." -ForegroundColor Cyan

try {
    $frontendTest = Invoke-WebRequest -Uri $frontendUrl -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
    Write-Host "[OK] Frontend: Status $($frontendTest.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Frontend: $($_.Exception.Message)" -ForegroundColor Red
}

try {
    $backendTest = Invoke-WebRequest -Uri "$backendUrl/health" -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
    Write-Host "[OK] Backend: Status $($backendTest.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Backend: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "[OK] Testes concluidos!" -ForegroundColor Green
Write-Host ""
Write-Host "Pressione Enter para sair..." -ForegroundColor Yellow
Read-Host
