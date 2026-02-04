# Script de teste para verificar o proxy

Write-Host "=== TESTE DO PROXY ===" -ForegroundColor Cyan
Write-Host ""

# Verificar se backend está rodando
Write-Host "1. Verificando Backend (porta 8000)..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 2 -ErrorAction Stop
    Write-Host "   [OK] Backend está rodando" -ForegroundColor Green
} catch {
    Write-Host "   [ERRO] Backend NÃO está rodando" -ForegroundColor Red
    Write-Host "   Execute: cd backend; .\venv312\Scripts\Activate.ps1; python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload" -ForegroundColor Yellow
}

Write-Host ""

# Verificar se frontend está rodando
Write-Host "2. Verificando Frontend (porta 3000)..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 2 -ErrorAction Stop
    Write-Host "   [OK] Frontend está rodando" -ForegroundColor Green
} catch {
    Write-Host "   [ERRO] Frontend NÃO está rodando" -ForegroundColor Red
    Write-Host "   Execute: cd frontend; npm run dev" -ForegroundColor Yellow
}

Write-Host ""

# Verificar se proxy está rodando
Write-Host "3. Verificando Proxy (porta 8080)..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8080/health" -TimeoutSec 2 -ErrorAction Stop
    Write-Host "   [OK] Proxy está rodando" -ForegroundColor Green
    Write-Host "   Status: $($response.StatusCode)" -ForegroundColor Cyan
} catch {
    Write-Host "   [ERRO] Proxy NÃO está rodando" -ForegroundColor Red
    Write-Host "   Execute: node proxy-server.js" -ForegroundColor Yellow
    Write-Host "   Erro: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Verificar ngrok
Write-Host "4. Verificando ngrok..." -ForegroundColor Yellow
try {
    $tunnels = Invoke-RestMethod -Uri "http://127.0.0.1:4040/api/tunnels" -ErrorAction Stop
    Write-Host "   [OK] ngrok está rodando" -ForegroundColor Green
    $tunnels.tunnels | ForEach-Object {
        Write-Host "   URL: $($_.public_url) -> $($_.config.addr)" -ForegroundColor Cyan
    }
} catch {
    Write-Host "   [ERRO] ngrok NÃO está rodando" -ForegroundColor Red
    Write-Host "   Execute: ngrok http 8080" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== FIM DO TESTE ===" -ForegroundColor Cyan

