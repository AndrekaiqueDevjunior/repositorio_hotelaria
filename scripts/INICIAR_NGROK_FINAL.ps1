# =========================================
# ngrok - Script Final Testado
# =========================================

Write-Host "[INICIO] Iniciando ngrok..." -ForegroundColor Cyan
Write-Host ""

# Matar processos existentes
Get-Process | Where-Object { $_.ProcessName -like "*ngrok*" } | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Iniciar ngrok frontend
Write-Host "[TUNNEL 1/2] Iniciando frontend (porta 3000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "ngrok http 3000 --log=stdout"
Start-Sleep -Seconds 7

# Iniciar ngrok backend
Write-Host "[TUNNEL 2/2] Iniciando backend (porta 8000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "ngrok http 8000 --log=stdout"
Start-Sleep -Seconds 7

# Obter URLs
Write-Host "[API] Buscando URLs..." -ForegroundColor Cyan
Start-Sleep -Seconds 3

$maxRetries = 5
$retry = 0
$frontendUrl = $null
$backendUrl = $null

while ($retry -lt $maxRetries) {
    try {
        $api = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels" -ErrorAction Stop
        
        foreach ($tunnel in $api.tunnels) {
            if ($tunnel.config.addr -like "*3000") {
                $frontendUrl = $tunnel.public_url
            }
            if ($tunnel.config.addr -like "*8000") {
                $backendUrl = $tunnel.public_url
            }
        }
        
        if ($frontendUrl -and $backendUrl) {
            break
        }
        
        Write-Host "[RETRY] Aguardando tunnels... ($($retry + 1)/$maxRetries)" -ForegroundColor Yellow
        Start-Sleep -Seconds 3
        $retry++
        
    } catch {
        Write-Host "[RETRY] Erro na API... ($($retry + 1)/$maxRetries)" -ForegroundColor Yellow
        Start-Sleep -Seconds 3
        $retry++
    }
}

if (-not $frontendUrl -or -not $backendUrl) {
    Write-Host ""
    Write-Host "[ERROR] Nao foi possivel obter URLs!" -ForegroundColor Red
    Write-Host "[INFO] Abra: http://localhost:4040" -ForegroundColor Yellow
    Write-Host "[INFO] Copie as URLs manualmente" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Pressione Enter para continuar..." -ForegroundColor Yellow
    Read-Host
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "[OK] NGROK CONFIGURADO!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "[URLS]" -ForegroundColor Cyan
Write-Host "   Frontend: $frontendUrl" -ForegroundColor White
Write-Host "   Backend:  $backendUrl" -ForegroundColor White
Write-Host ""

# Configurar .env
Write-Host "[CONFIG] Atualizando .env..." -ForegroundColor Cyan

$backendEnvFile = "$PSScriptRoot\backend\.env.docker"
$backendEnv = Get-Content $backendEnvFile -Raw

$corsOrigins = "$backendUrl,$frontendUrl,http://localhost:3000"
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

$frontendEnvFile = "$PSScriptRoot\frontend\.env.local"
Set-Content -Path $frontendEnvFile -Value "NEXT_PUBLIC_API_URL=$backendUrl/api/v1"

Write-Host "[OK] .env atualizado" -ForegroundColor Green
Write-Host ""

# Reiniciar containers
Write-Host "[RESTART] Reiniciando containers..." -ForegroundColor Cyan
docker-compose restart backend frontend
Start-Sleep -Seconds 12

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "[TEST] TESTANDO SISTEMA..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Testar frontend
Write-Host "[TEST 1/3] Testando frontend..." -ForegroundColor Cyan
try {
    $test1 = Invoke-WebRequest -Uri $frontendUrl -UseBasicParsing -TimeoutSec 15 -ErrorAction Stop
    Write-Host "[OK] Frontend: $($test1.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Frontend: $($_.Exception.Message)" -ForegroundColor Red
}

# Testar backend health
Write-Host "[TEST 2/3] Testando backend health..." -ForegroundColor Cyan
try {
    $test2 = Invoke-WebRequest -Uri "$backendUrl/health" -UseBasicParsing -TimeoutSec 15 -ErrorAction Stop
    Write-Host "[OK] Backend health: $($test2.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Backend health: $($_.Exception.Message)" -ForegroundColor Red
}

# Testar login
Write-Host "[TEST 3/3] Testando login..." -ForegroundColor Cyan
try {
    $loginBody = @{
        email = "admin@hotelreal.com.br"
        password = "admin123"
    } | ConvertTo-Json

    $test3 = Invoke-WebRequest -Uri "$backendUrl/api/v1/auth/login" -Method POST -Body $loginBody -ContentType "application/json" -UseBasicParsing -TimeoutSec 15 -ErrorAction Stop
    Write-Host "[OK] Login: $($test3.StatusCode)" -ForegroundColor Green
    
    $loginData = $test3.Content | ConvertFrom-Json
    if ($loginData.access_token) {
        Write-Host "[OK] JWT token gerado!" -ForegroundColor Green
    }
} catch {
    Write-Host "[ERROR] Login: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "[OK] SISTEMA PRONTO!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "[SHARE] Compartilhe:" -ForegroundColor Cyan
Write-Host ""
Write-Host "   URL: $frontendUrl" -ForegroundColor White
Write-Host "   Login: admin@hotelreal.com.br" -ForegroundColor White
Write-Host "   Senha: admin123" -ForegroundColor White
Write-Host ""
Write-Host "[DASHBOARD] http://localhost:4040" -ForegroundColor Cyan
Write-Host ""
Write-Host "[IMPORTANTE]" -ForegroundColor Yellow
Write-Host "   - Mantenha as janelas ngrok abertas" -ForegroundColor Gray
Write-Host "   - URLs funcionam de qualquer lugar" -ForegroundColor Gray
Write-Host "   - HTTPS seguro automatico" -ForegroundColor Gray
Write-Host ""
Write-Host "Pressione Enter para sair..." -ForegroundColor Yellow
Read-Host
