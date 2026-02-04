# Script para corrigir erro 502 Bad Gateway do Cloudflare Tunnel

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "   Corrigir Erro 502 Bad Gateway" -ForegroundColor Red
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

# Verificar proxy
Write-Host "[1/4] Verificando Proxy (porta 8080)..." -ForegroundColor Cyan
$proxyRunning = $false
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8080/health" -TimeoutSec 2 -ErrorAction Stop
    Write-Host "   [OK] Proxy esta respondendo" -ForegroundColor Green
    $proxyRunning = $true
} catch {
    Write-Host "   [ERRO] Proxy NAO esta respondendo" -ForegroundColor Red
    Write-Host "   Erro: $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host ""

# Verificar backend
Write-Host "[2/4] Verificando Backend (porta 8000)..." -ForegroundColor Cyan
$backendRunning = $false
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 2 -ErrorAction Stop
    Write-Host "   [OK] Backend esta respondendo" -ForegroundColor Green
    $backendRunning = $true
} catch {
    Write-Host "   [ERRO] Backend NAO esta respondendo" -ForegroundColor Red
}

Write-Host ""

# Verificar frontend
Write-Host "[3/4] Verificando Frontend (porta 3000)..." -ForegroundColor Cyan
$frontendRunning = $false
try {
    $response = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 2 -ErrorAction Stop
    Write-Host "   [OK] Frontend esta respondendo" -ForegroundColor Green
    $frontendRunning = $true
} catch {
    Write-Host "   [ERRO] Frontend NAO esta respondendo" -ForegroundColor Red
}

Write-Host ""

# Soluções
Write-Host "[4/4] Aplicando correcoes..." -ForegroundColor Cyan
Write-Host ""

$needRestart = $false

# Se proxy não está rodando, iniciar
if (-not $proxyRunning) {
    Write-Host "[ACAO] Iniciando Proxy..." -ForegroundColor Yellow
    
    # Parar processos antigos na porta 8080
    $processes = Get-NetTCPConnection -LocalPort 8080 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
    if ($processes) {
        $processes | ForEach-Object {
            Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue
        }
        Start-Sleep -Seconds 2
    }
    
    # Iniciar proxy
    $proxyScript = @"
cd '$PWD'
node proxy-server.js
"@
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $proxyScript | Out-Null
    Write-Host "   [OK] Proxy iniciado" -ForegroundColor Green
    Start-Sleep -Seconds 3
    $needRestart = $true
}

# Se backend não está rodando, iniciar
if (-not $backendRunning) {
    Write-Host "[ACAO] Iniciando Backend..." -ForegroundColor Yellow
    
    $backendScript = @"
cd '$PWD\backend'
.\venv312\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
"@
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendScript | Out-Null
    Write-Host "   [OK] Backend iniciado" -ForegroundColor Green
    Start-Sleep -Seconds 5
    $needRestart = $true
}

# Se frontend não está rodando, iniciar
if (-not $frontendRunning) {
    Write-Host "[ACAO] Iniciando Frontend..." -ForegroundColor Yellow
    
    $frontendScript = @"
cd '$PWD\frontend'
npm run dev
"@
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendScript | Out-Null
    Write-Host "   [OK] Frontend iniciado" -ForegroundColor Green
    Start-Sleep -Seconds 5
    $needRestart = $true
}

Write-Host ""

# Aguardar serviços ficarem prontos
if ($needRestart) {
    Write-Host "Aguardando servicos ficarem prontos..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    
    # Verificar novamente
    Write-Host ""
    Write-Host "Verificando novamente..." -ForegroundColor Cyan
    
    $allOk = $true
    
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8080/health" -TimeoutSec 3 -ErrorAction Stop
        Write-Host "   [OK] Proxy respondendo" -ForegroundColor Green
    } catch {
        Write-Host "   [ERRO] Proxy ainda nao responde" -ForegroundColor Red
        $allOk = $false
    }
    
    if ($allOk) {
        Write-Host ""
        Write-Host "===============================================" -ForegroundColor Green
        Write-Host "   CORRECAO APLICADA!" -ForegroundColor Green
        Write-Host "===============================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "Aguarde mais alguns segundos e teste novamente a URL do Cloudflare Tunnel" -ForegroundColor Yellow
        Write-Host ""
    } else {
        Write-Host ""
        Write-Host "[AVISO] Alguns servicos ainda estao iniciando" -ForegroundColor Yellow
        Write-Host "Aguarde mais alguns segundos e teste novamente" -ForegroundColor White
        Write-Host ""
    }
} else {
    Write-Host "Todos os servicos estao rodando!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Se ainda receber erro 502:" -ForegroundColor Yellow
    Write-Host "  1. Verifique se o Cloudflare Tunnel esta apontando para localhost:8080" -ForegroundColor White
    Write-Host "  2. Tente reiniciar o Cloudflare Tunnel" -ForegroundColor White
    Write-Host "  3. Verifique firewall/antivirus bloqueando conexoes" -ForegroundColor White
    Write-Host ""
}

Write-Host "Teste o proxy localmente:" -ForegroundColor Cyan
Write-Host "   curl http://localhost:8080/health" -ForegroundColor White
Write-Host ""

