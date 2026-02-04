# SCRIPT SIMPLIFICADO - Inicia Backend + Frontend + ngrok
# Execute: .\INICIAR_TUDO.ps1

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "     HOTEL CABO FRIO - INICIO COMPLETO" -ForegroundColor Green  
Write-Host "============================================" -ForegroundColor Green
Write-Host ""

# 1. Parar processos antigos
Write-Host "[1/5] Limpando processos anteriores..." -ForegroundColor Yellow
docker-compose down 2>$null
Stop-Process -Name "ngrok" -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# 2. Iniciar apenas containers essenciais (postgres + redis)
Write-Host "[2/5] Iniciando banco de dados..." -ForegroundColor Yellow
docker-compose up -d postgres redis
Write-Host "      Aguardando banco ficar pronto (30s)..." -ForegroundColor Gray
Start-Sleep -Seconds 30

# 3. Iniciar Backend local (mais confiavel)
Write-Host "[3/5] Iniciando Backend..." -ForegroundColor Yellow
$backendJob = Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$PWD\backend'; Write-Host 'BACKEND API' -ForegroundColor Green; .\venv312\Scripts\Activate.ps1; python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
) -PassThru
Start-Sleep -Seconds 10

# Testar se backend esta rodando
$backendOk = $false
for ($i = 1; $i -le 5; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 3 -ErrorAction Stop
        $backendOk = $true
        Write-Host "      [OK] Backend rodando!" -ForegroundColor Green
        break
    } catch {
        Write-Host "      Tentativa $i/5..." -ForegroundColor Gray
        Start-Sleep -Seconds 3
    }
}

if (-not $backendOk) {
    Write-Host "      [AVISO] Backend ainda iniciando..." -ForegroundColor Yellow
}

# 4. Iniciar ngrok
Write-Host "[4/5] Iniciando ngrok..." -ForegroundColor Yellow
$ngrokJob = Start-Process powershell -ArgumentList @(
    "-NoExit", 
    "-Command",
    "Write-Host 'NGROK TUNNEL' -ForegroundColor Cyan; ngrok http 8000"
) -PassThru
Start-Sleep -Seconds 5

# 5. Obter URL do ngrok e configurar .env
Write-Host "[5/5] Configurando URLs..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

$ngrokUrl = $null
try {
    $tunnels = Invoke-RestMethod -Uri "http://127.0.0.1:4040/api/tunnels" -ErrorAction Stop
    $ngrokUrl = ($tunnels.tunnels | Where-Object { $_.proto -eq "https" } | Select-Object -First 1).public_url
    
    if ($ngrokUrl) {
        Write-Host "      [OK] URL ngrok: $ngrokUrl" -ForegroundColor Green
        
        # Atualizar frontend/.env.local
        $envContent = "NEXT_PUBLIC_API_URL=$ngrokUrl"
        Set-Content -Path "frontend\.env.local" -Value $envContent
        Write-Host "      [OK] frontend/.env.local atualizado" -ForegroundColor Green
    }
} catch {
    Write-Host "      [INFO] Acesse http://127.0.0.1:4040 para ver URL" -ForegroundColor Cyan
}

# 6. Iniciar Frontend
Write-Host ""
Write-Host "[EXTRA] Iniciando Frontend..." -ForegroundColor Yellow
$frontendJob = Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$PWD\frontend'; Write-Host 'FRONTEND' -ForegroundColor Magenta; npm run dev"
) -PassThru

# RESUMO FINAL
Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "           SISTEMA INICIADO!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "URLs LOCAIS:" -ForegroundColor Yellow
Write-Host "   Backend:     http://localhost:8000" -ForegroundColor White
Write-Host "   API Docs:    http://localhost:8000/docs" -ForegroundColor White
Write-Host "   Frontend:    http://localhost:3000" -ForegroundColor White
Write-Host ""
Write-Host "ACESSO EXTERNO (ngrok):" -ForegroundColor Yellow
if ($ngrokUrl) {
    Write-Host "   Backend:     $ngrokUrl" -ForegroundColor Cyan
    Write-Host "   API Docs:    $ngrokUrl/docs" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "WEBHOOK CIELO:" -ForegroundColor Yellow
    Write-Host "   $ngrokUrl/api/v1/pagamentos/webhook/cielo" -ForegroundColor Cyan
} else {
    Write-Host "   Dashboard:   http://127.0.0.1:4040" -ForegroundColor White
    Write-Host "   (Veja a URL publica no dashboard)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "   Abra os terminais para ver os logs" -ForegroundColor White
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
