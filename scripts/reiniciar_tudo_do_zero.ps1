# Script para PARAR TUDO e reiniciar do zero

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "===============================================" -ForegroundColor Red
Write-Host "   REINICIAR TUDO DO ZERO" -ForegroundColor Yellow
Write-Host "===============================================" -ForegroundColor Red
Write-Host ""
Write-Host "Este script vai PARAR TODOS os processos e reiniciar" -ForegroundColor Yellow
Write-Host ""

# 1. PARAR TUDO
Write-Host "[1/5] PARANDO TODOS OS PROCESSOS..." -ForegroundColor Red

# Parar Cloudflare
Write-Host "   Parando Cloudflare Tunnels..." -ForegroundColor Yellow
$cloudflared = Get-Process -Name "cloudflared" -ErrorAction SilentlyContinue
if ($cloudflared) {
    $cloudflared | ForEach-Object {
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    }
    Write-Host "   [OK] $($cloudflared.Count) processo(s) Cloudflare parado(s)" -ForegroundColor Green
}

# Parar processos nas portas
Write-Host "   Parando processos nas portas 8000, 3000, 8080..." -ForegroundColor Yellow
$ports = @(8000, 3000, 8080)
$totalStopped = 0
foreach ($port in $ports) {
    $processes = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | 
        Select-Object -ExpandProperty OwningProcess -Unique
    if ($processes) {
        $processes | ForEach-Object {
            $proc = Get-Process -Id $_ -ErrorAction SilentlyContinue
            if ($proc) {
                Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue
                $totalStopped++
            }
        }
    }
}
Write-Host "   [OK] $totalStopped processo(s) parado(s)" -ForegroundColor Green

# Aguardar processos terminarem
Start-Sleep -Seconds 3

# Verificar se ainda há processos
$remaining = Get-NetTCPConnection -LocalPort 8000,3000,8080 -ErrorAction SilentlyContinue | 
    Where-Object { $_.State -eq "Listen" } | 
    Select-Object -ExpandProperty OwningProcess -Unique
if ($remaining) {
    Write-Host "   [AVISO] Alguns processos ainda estao rodando, forçando parada..." -ForegroundColor Yellow
    $remaining | ForEach-Object {
        Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 2
}

Write-Host "   [OK] Todos os processos parados" -ForegroundColor Green
Write-Host ""

# 2. Aguardar portas ficarem livres
Write-Host "[2/5] Aguardando portas ficarem livres..." -ForegroundColor Cyan
Start-Sleep -Seconds 3
Write-Host "   [OK] Portas liberadas" -ForegroundColor Green
Write-Host ""

# 3. Verificar requisitos
Write-Host "[3/5] Verificando requisitos..." -ForegroundColor Cyan
$allOk = $true

try {
    node --version | Out-Null
    Write-Host "   [OK] Node.js" -ForegroundColor Green
} catch {
    Write-Host "   [ERRO] Node.js nao encontrado!" -ForegroundColor Red
    $allOk = $false
}

try {
    cloudflared --version | Out-Null
    Write-Host "   [OK] cloudflared" -ForegroundColor Green
} catch {
    Write-Host "   [ERRO] cloudflared nao encontrado!" -ForegroundColor Red
    $allOk = $false
}

$certPath = "$env:USERPROFILE\.cloudflared\cert.pem"
if (-not (Test-Path $certPath)) {
    Write-Host "   [ERRO] Cloudflare nao autenticado!" -ForegroundColor Red
    Write-Host "   Execute: .\configurar_cloudflare_login.ps1" -ForegroundColor Yellow
    $allOk = $false
} else {
    Write-Host "   [OK] Cloudflare autenticado" -ForegroundColor Green
}

if (-not $allOk) {
    Write-Host ""
    Write-Host "[ERRO] Requisitos nao atendidos. Corrija e execute novamente." -ForegroundColor Red
    exit 1
}

Write-Host ""

# 4. Instalar dependências se necessário
Write-Host "[4/5] Verificando dependencias..." -ForegroundColor Cyan
if (-not (Test-Path "node_modules\express")) {
    Write-Host "   Instalando dependencias..." -ForegroundColor Yellow
    npm install --silent | Out-Null
}
Write-Host "   [OK] Dependencias OK" -ForegroundColor Green
Write-Host ""

# 5. Iniciar serviços na ordem correta
Write-Host "[5/5] Iniciando servicos..." -ForegroundColor Cyan
Write-Host ""

# Backend
Write-Host "   [1/4] Iniciando Backend..." -ForegroundColor Yellow
$backendScript = @"
cd '$PWD\backend'
Write-Host '=== BACKEND (Porta 8000) ===' -ForegroundColor Green
.\venv312\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
"@
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendScript | Out-Null
Start-Sleep -Seconds 8

# Frontend
Write-Host "   [2/4] Iniciando Frontend..." -ForegroundColor Yellow
$frontendScript = @"
cd '$PWD\frontend'
Write-Host '=== FRONTEND (Porta 3000) ===' -ForegroundColor Green
npm run dev
"@
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendScript | Out-Null
Start-Sleep -Seconds 8

# Proxy
Write-Host "   [3/4] Iniciando Proxy..." -ForegroundColor Yellow
$proxyScript = @"
cd '$PWD'
Write-Host '=== PROXY (Porta 8080) ===' -ForegroundColor Green
node proxy-server.js
"@
Start-Process powershell -ArgumentList "-NoExit", "-Command", $proxyScript | Out-Null
Start-Sleep -Seconds 5

# Cloudflare Tunnel
Write-Host "   [4/4] Iniciando Cloudflare Tunnel..." -ForegroundColor Yellow
$tunnelScript = @"
cd '$PWD'
Write-Host '=== CLOUDFLARE TUNNEL ===' -ForegroundColor Green
Write-Host 'Aguardando proxy ficar pronto...' -ForegroundColor Yellow
Start-Sleep -Seconds 10
Write-Host 'Iniciando tunnel...' -ForegroundColor Cyan
cloudflared tunnel --url http://localhost:8080
"@
Start-Process powershell -ArgumentList "-NoExit", "-Command", $tunnelScript | Out-Null

Write-Host ""
Write-Host "===============================================" -ForegroundColor Green
Write-Host "   SERVICOS INICIADOS!" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Aguarde 20-30 segundos para tudo ficar pronto..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Depois, teste:" -ForegroundColor Cyan
Write-Host "   curl http://localhost:8080/health" -ForegroundColor White
Write-Host ""
Write-Host "A URL publica aparecera no terminal do Cloudflare Tunnel" -ForegroundColor Cyan
Write-Host ""

