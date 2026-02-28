# Script Rápido para Corrigir 502 - Foca no essencial

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "===============================================" -ForegroundColor Red
Write-Host "   CORRIGIR ERRO 502 - RAPIDO" -ForegroundColor Yellow
Write-Host "===============================================" -ForegroundColor Red
Write-Host ""

# 1. Verificar Proxy
Write-Host "[1/4] Verificando Proxy..." -ForegroundColor Cyan
$proxyOk = $false
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8080/health" -TimeoutSec 3 -ErrorAction Stop
    Write-Host "   [OK] Proxy esta respondendo" -ForegroundColor Green
    $proxyOk = $true
} catch {
    Write-Host "   [ERRO] Proxy NAO esta respondendo!" -ForegroundColor Red
    Write-Host "   Iniciando proxy..." -ForegroundColor Yellow
    
    # Parar processos antigos na porta 8080
    $processes = Get-NetTCPConnection -LocalPort 8080 -ErrorAction SilentlyContinue | 
        Where-Object { $_.State -eq "Listen" } |
        Select-Object -ExpandProperty OwningProcess -Unique
    if ($processes) {
        $processes | ForEach-Object {
            Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue
        }
        Start-Sleep -Seconds 2
    }
    
    # Iniciar proxy
    $proxyScript = @"
cd '$PWD'
Write-Host '=== PROXY SERVER (Porta 8080) ===' -ForegroundColor Green
node proxy-server.js
"@
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $proxyScript | Out-Null
    Write-Host "   [OK] Proxy iniciado, aguardando..." -ForegroundColor Green
    Start-Sleep -Seconds 5
    
    # Verificar novamente
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8080/health" -TimeoutSec 3 -ErrorAction Stop
        Write-Host "   [OK] Proxy agora esta respondendo!" -ForegroundColor Green
        $proxyOk = $true
    } catch {
        Write-Host "   [AVISO] Proxy ainda iniciando, aguarde mais alguns segundos" -ForegroundColor Yellow
    }
}

Write-Host ""

# 2. Verificar Backend
Write-Host "[2/4] Verificando Backend..." -ForegroundColor Cyan
$backendOk = $false
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 3 -ErrorAction Stop
    Write-Host "   [OK] Backend esta respondendo" -ForegroundColor Green
    $backendOk = $true
} catch {
    Write-Host "   [ERRO] Backend NAO esta respondendo!" -ForegroundColor Red
    Write-Host "   Iniciando backend..." -ForegroundColor Yellow
    
    $backendScript = @"
cd '$PWD\backend'
.\venv312\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
"@
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendScript | Out-Null
    Write-Host "   [OK] Backend iniciado, aguardando..." -ForegroundColor Green
    Start-Sleep -Seconds 5
    
    # Verificar novamente
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 3 -ErrorAction Stop
        Write-Host "   [OK] Backend agora esta respondendo!" -ForegroundColor Green
        $backendOk = $true
    } catch {
        Write-Host "   [AVISO] Backend ainda iniciando, aguarde mais alguns segundos" -ForegroundColor Yellow
    }
}

Write-Host ""

# 3. Verificar Frontend
Write-Host "[3/4] Verificando Frontend..." -ForegroundColor Cyan
$frontendOk = $false
try {
    $response = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 3 -ErrorAction Stop
    Write-Host "   [OK] Frontend esta respondendo" -ForegroundColor Green
    $frontendOk = $true
} catch {
    Write-Host "   [AVISO] Frontend nao esta respondendo" -ForegroundColor Yellow
    Write-Host "   (Pode nao ser critico se o proxy estiver funcionando)" -ForegroundColor Gray
}

Write-Host ""

# 4. Verificar Cloudflare Tunnel
Write-Host "[4/4] Verificando Cloudflare Tunnel..." -ForegroundColor Cyan
$cloudflared = Get-Process -Name "cloudflared" -ErrorAction SilentlyContinue
if ($cloudflared) {
    $count = $cloudflared.Count
    if ($count -eq 1) {
        Write-Host "   [OK] 1 processo Cloudflare encontrado" -ForegroundColor Green
    } else {
        Write-Host "   [AVISO] $count processos encontrados (deveria ser 1)" -ForegroundColor Yellow
        Write-Host "   Parando processos extras..." -ForegroundColor Yellow
        $cloudflared | Select-Object -Skip 1 | ForEach-Object {
            Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
        }
        Write-Host "   [OK] Processos extras parados" -ForegroundColor Green
    }
} else {
    Write-Host "   [ERRO] Nenhum processo Cloudflare encontrado!" -ForegroundColor Red
    Write-Host "   Iniciando Cloudflare Tunnel..." -ForegroundColor Yellow
    
    $tunnelScript = @"
cd '$PWD'
Write-Host '=== CLOUDFLARE TUNNEL ===' -ForegroundColor Green
Write-Host 'Aguardando proxy na porta 8080...' -ForegroundColor Yellow
Start-Sleep -Seconds 5
cloudflared tunnel --url http://localhost:8080
"@
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $tunnelScript | Out-Null
    Write-Host "   [OK] Cloudflare Tunnel iniciado" -ForegroundColor Green
}

Write-Host ""

# Resumo
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "   RESUMO" -ForegroundColor Yellow
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

if ($proxyOk) {
    Write-Host "[OK] Proxy esta funcionando" -ForegroundColor Green
} else {
    Write-Host "[ERRO] Proxy precisa ser corrigido" -ForegroundColor Red
}

if ($backendOk) {
    Write-Host "[OK] Backend esta funcionando" -ForegroundColor Green
} else {
    Write-Host "[ERRO] Backend precisa ser corrigido" -ForegroundColor Red
}

if ($frontendOk) {
    Write-Host "[OK] Frontend esta funcionando" -ForegroundColor Green
} else {
    Write-Host "[AVISO] Frontend pode estar iniciando" -ForegroundColor Yellow
}

Write-Host ""

if ($proxyOk -and $backendOk) {
    Write-Host "===============================================" -ForegroundColor Green
    Write-Host "   CORRECAO APLICADA!" -ForegroundColor Green
    Write-Host "===============================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Aguarde 10-15 segundos e teste novamente a URL do Cloudflare Tunnel" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Teste local primeiro:" -ForegroundColor Cyan
    Write-Host "   curl http://localhost:8080/health" -ForegroundColor White
    Write-Host "   curl http://localhost:8080/api/v1/health" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "===============================================" -ForegroundColor Red
    Write-Host "   ALGUNS SERVICOS AINDA ESTAO INICIANDO" -ForegroundColor Yellow
    Write-Host "===============================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Aguarde mais alguns segundos e execute novamente:" -ForegroundColor Yellow
    Write-Host "   .\corrigir_502_rapido.ps1" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "OU execute o script completo:" -ForegroundColor Yellow
    Write-Host "   .\iniciar_tudo_corrigido.ps1" -ForegroundColor Cyan
    Write-Host ""
}

