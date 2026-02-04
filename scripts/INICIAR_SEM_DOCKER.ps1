# SCRIPT SEM DOCKER - Inicia Backend + Frontend + ngrok
# Use se o Docker estiver com problemas
# Execute: .\INICIAR_SEM_DOCKER.ps1

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "   HOTEL CABO FRIO - SEM DOCKER + NGROK" -ForegroundColor Green  
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "[INFO] Este script nao usa Docker" -ForegroundColor Cyan
Write-Host "[INFO] Requer PostgreSQL instalado localmente" -ForegroundColor Cyan
Write-Host ""

# Verificar se ngrok esta instalado
try {
    $ngrokVersion = ngrok version 2>&1
    Write-Host "[OK] ngrok: $ngrokVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERRO] ngrok nao encontrado!" -ForegroundColor Red
    Write-Host "       Instale em: https://ngrok.com/download" -ForegroundColor Yellow
    exit 1
}

# Verificar venv do backend
if (-not (Test-Path "backend\venv312\Scripts\Activate.ps1")) {
    Write-Host "[ERRO] Backend venv312 nao encontrado!" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Backend venv encontrado" -ForegroundColor Green

# Verificar node_modules do frontend
if (-not (Test-Path "frontend\node_modules")) {
    Write-Host "[AVISO] Instalando dependencias do frontend..." -ForegroundColor Yellow
    Set-Location frontend
    npm install
    Set-Location ..
}
Write-Host "[OK] Frontend node_modules OK" -ForegroundColor Green

Write-Host ""
Write-Host "Iniciando servicos..." -ForegroundColor Yellow
Write-Host ""

# 1. Iniciar Backend
Write-Host "[1/4] Iniciando Backend (porta 8000)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$PWD\backend'; Write-Host '=== BACKEND API ===' -ForegroundColor Green; Write-Host 'Porta: 8000' -ForegroundColor Gray; Write-Host ''; .\venv312\Scripts\Activate.ps1; python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
)
Start-Sleep -Seconds 8

# 2. Testar Backend
Write-Host "[2/4] Testando Backend..." -ForegroundColor Cyan
$backendOk = $false
for ($i = 1; $i -le 10; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 2 -ErrorAction Stop
        $backendOk = $true
        Write-Host "      [OK] Backend respondendo!" -ForegroundColor Green
        break
    } catch {
        Write-Host "      Aguardando... ($i/10)" -ForegroundColor Gray
        Start-Sleep -Seconds 2
    }
}

if (-not $backendOk) {
    Write-Host "      [AVISO] Backend pode ainda estar iniciando" -ForegroundColor Yellow
}

# 3. Iniciar ngrok
Write-Host "[3/4] Iniciando ngrok para Backend..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList @(
    "-NoExit", 
    "-Command",
    "Write-Host '=== NGROK TUNNEL ===' -ForegroundColor Cyan; Write-Host 'Expondo porta 8000' -ForegroundColor Gray; Write-Host ''; ngrok http 8000"
)
Start-Sleep -Seconds 5

# 4. Obter URL e configurar
Write-Host "[4/4] Obtendo URL do ngrok..." -ForegroundColor Cyan
Start-Sleep -Seconds 3

$ngrokUrl = $null
try {
    $tunnels = Invoke-RestMethod -Uri "http://127.0.0.1:4040/api/tunnels" -ErrorAction Stop
    $ngrokUrl = ($tunnels.tunnels | Where-Object { $_.proto -eq "https" } | Select-Object -First 1).public_url
    
    if ($ngrokUrl) {
        Write-Host "      [OK] URL: $ngrokUrl" -ForegroundColor Green
        
        # Criar/Atualizar frontend/.env.local
        $envPath = "frontend\.env.local"
        $envContent = "NEXT_PUBLIC_API_URL=$ngrokUrl"
        Set-Content -Path $envPath -Value $envContent
        Write-Host "      [OK] Configurado: $envPath" -ForegroundColor Green
    }
} catch {
    Write-Host "      [INFO] Acesse http://127.0.0.1:4040 para obter URL" -ForegroundColor Yellow
}

# 5. Iniciar Frontend
Write-Host ""
Write-Host "[5/4] Iniciando Frontend (porta 3000)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$PWD\frontend'; Write-Host '=== FRONTEND ===' -ForegroundColor Magenta; Write-Host 'Porta: 3000' -ForegroundColor Gray; Write-Host ''; npm run dev"
)

# RESUMO
Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "         SISTEMA INICIADO!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "ACESSO LOCAL:" -ForegroundColor Yellow
Write-Host "   Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "   API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "   Frontend: http://localhost:3000" -ForegroundColor White
Write-Host ""
Write-Host "ACESSO EXTERNO (ngrok):" -ForegroundColor Yellow
if ($ngrokUrl) {
    Write-Host "   Backend:  $ngrokUrl" -ForegroundColor Cyan
    Write-Host "   API Docs: $ngrokUrl/docs" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "PARA WEBHOOK CIELO:" -ForegroundColor Yellow
    Write-Host "   $ngrokUrl/api/v1/pagamentos/webhook/cielo" -ForegroundColor Cyan
} else {
    Write-Host "   Dashboard: http://127.0.0.1:4040" -ForegroundColor White
}
Write-Host ""
Write-Host "TERMINAIS ABERTOS:" -ForegroundColor Yellow
Write-Host "   1. Backend (API)" -ForegroundColor White
Write-Host "   2. ngrok (Tunnel)" -ForegroundColor White  
Write-Host "   3. Frontend (Next.js)" -ForegroundColor White
Write-Host ""
Write-Host "[INFO] Feche os terminais para parar os servicos" -ForegroundColor Gray
Write-Host ""

