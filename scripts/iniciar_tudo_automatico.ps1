# Script Completo - Inicia tudo e configura .env.local automaticamente

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "   Hotel Real Cabo Frio - Inicio Automatico" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

# Verificações iniciais
Write-Host "[1/6] Verificando requisitos..." -ForegroundColor Cyan

# Verificar Node.js
try {
    $nodeVersion = node --version 2>&1
    Write-Host "   [OK] Node.js: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "   [ERRO] Node.js nao encontrado!" -ForegroundColor Red
    exit 1
}

# Verificar cloudflared
try {
    $cloudflaredVersion = cloudflared --version 2>&1
    Write-Host "   [OK] cloudflared instalado" -ForegroundColor Green
} catch {
    Write-Host "   [ERRO] cloudflared nao encontrado!" -ForegroundColor Red
    Write-Host "   Instale: choco install cloudflared" -ForegroundColor Yellow
    exit 1
}

# Verificar autenticação Cloudflare
$certPath = "$env:USERPROFILE\.cloudflared\cert.pem"
$credentialsPath = "$env:USERPROFILE\.cloudflared\credentials.json"
$isAuthenticated = (Test-Path $certPath) -or (Test-Path $credentialsPath)

if (-not $isAuthenticated) {
    Write-Host "   [ERRO] Cloudflare nao autenticado!" -ForegroundColor Red
    Write-Host "   Execute: .\configurar_cloudflare_login.ps1" -ForegroundColor Yellow
    exit 1
}
Write-Host "   [OK] Cloudflare autenticado" -ForegroundColor Green

Write-Host ""

# Instalar dependências do proxy
Write-Host "[2/6] Verificando dependencias..." -ForegroundColor Cyan
if (-not (Test-Path "node_modules\express")) {
    Write-Host "   [INFO] Instalando dependencias do proxy..." -ForegroundColor Yellow
    npm install --silent | Out-Null
}
Write-Host "   [OK] Dependencias OK" -ForegroundColor Green
Write-Host ""

# Parar processos antigos
Write-Host "[3/6] Limpando portas..." -ForegroundColor Cyan
$ports = @(8000, 3000, 8080)
foreach ($port in $ports) {
    $processes = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
    if ($processes) {
        $processes | ForEach-Object {
            Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue
        }
    }
}
Start-Sleep -Seconds 2
Write-Host "   [OK] Portas liberadas" -ForegroundColor Green
Write-Host ""

# Iniciar Backend
Write-Host "[4/6] Iniciando Backend..." -ForegroundColor Cyan
$backendScript = @"
cd '$PWD\backend'
.\venv312\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
"@
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendScript | Out-Null
Start-Sleep -Seconds 5
Write-Host "   [OK] Backend iniciado (porta 8000)" -ForegroundColor Green

# Iniciar Frontend
Write-Host "[5/6] Iniciando Frontend..." -ForegroundColor Cyan
$frontendScript = @"
cd '$PWD\frontend'
npm run dev
"@
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendScript | Out-Null
Start-Sleep -Seconds 5
Write-Host "   [OK] Frontend iniciado (porta 3000)" -ForegroundColor Green

# Iniciar Proxy
Write-Host "[6/6] Iniciando Proxy..." -ForegroundColor Cyan
$proxyScript = @"
cd '$PWD'
node proxy-server.js
"@
Start-Process powershell -ArgumentList "-NoExit", "-Command", $proxyScript | Out-Null
Start-Sleep -Seconds 3
Write-Host "   [OK] Proxy iniciado (porta 8080)" -ForegroundColor Green
Write-Host ""

# Aguardar serviços ficarem prontos
Write-Host "Aguardando servicos ficarem prontos..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Verificar se proxy está respondendo
$proxyReady = $false
for ($i = 1; $i -le 10; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8080/health" -TimeoutSec 2 -ErrorAction Stop
        $proxyReady = $true
        break
    } catch {
        Start-Sleep -Seconds 2
    }
}

if (-not $proxyReady) {
    Write-Host "[AVISO] Proxy ainda nao esta respondendo, mas continuando..." -ForegroundColor Yellow
}

Write-Host ""

# Iniciar Cloudflare Tunnel e obter URL
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "   Iniciando Cloudflare Tunnel..." -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

# Criar arquivo temporário para capturar URL
$tempLogFile = Join-Path $env:TEMP "cloudflared-url-$(Get-Date -Format 'yyyyMMdd-HHmmss').txt"
$urlFound = $false
$publicUrl = ""

Write-Host "Iniciando Cloudflare Tunnel..." -ForegroundColor Cyan
Write-Host "Aguarde alguns segundos para obter a URL publica..." -ForegroundColor Yellow
Write-Host ""

# Script que captura URL e salva em arquivo
$tunnelScript = @"
cd '$PWD'
`$ErrorActionPreference = 'Continue'
`$urlFile = '$tempLogFile'

# Funcao para processar output
function Process-CloudflaredOutput {
    param([string]`$line)
    
    Write-Host `$line -ForegroundColor Cyan
    
    # Procurar URL no formato: https://xxxx-xxxx-xxxx.trycloudflare.com
    if (`$line -match 'https://([a-z0-9-]+)\.trycloudflare\.com') {
        `$url = `$matches[0]
        `$url | Out-File `$urlFile -Encoding UTF8 -Force
        Write-Host "URL CAPTURADA: `$url" -ForegroundColor Green
    }
}

# Iniciar cloudflared e processar output
cloudflared tunnel --url http://localhost:8080 2>&1 | ForEach-Object {
    Process-CloudflaredOutput `$_
}
"@

# Iniciar tunnel em processo separado
$tunnelProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", $tunnelScript -PassThru -WindowStyle Minimized

# Aguardar e tentar capturar URL
Write-Host "Aguardando URL do Cloudflare Tunnel..." -ForegroundColor Yellow
Write-Host "(Isso pode levar 10-20 segundos)" -ForegroundColor Gray
Write-Host ""

for ($i = 1; $i -le 40; $i++) {
    Start-Sleep -Seconds 1
    
    # Tentar ler URL do arquivo temporário
    if (Test-Path $tempLogFile) {
        $capturedUrl = Get-Content $tempLogFile -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($capturedUrl -and $capturedUrl -match 'https://[a-z0-9-]+\.trycloudflare\.com') {
            $publicUrl = $capturedUrl.Trim()
            $urlFound = $true
            break
        }
    }
    
    if ($i % 5 -eq 0) {
        Write-Host "." -NoNewline -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host ""

if ($urlFound -and $publicUrl) {
    Write-Host "===============================================" -ForegroundColor Green
    Write-Host "   URL PUBLICA OBTIDA!" -ForegroundColor Green
    Write-Host "===============================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "URL Publica: $publicUrl" -ForegroundColor Cyan
    Write-Host ""
    
    # Atualizar .env.local
    Write-Host "Atualizando frontend/.env.local..." -ForegroundColor Yellow
    
    $envLocalPath = "frontend\.env.local"
    $envContent = @"
# Configuracao automatica - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
NEXT_PUBLIC_API_URL=$publicUrl

# URLs de referencia
NEXT_PUBLIC_API_URL_LOCAL=http://localhost:8000
NEXT_PUBLIC_PROXY_URL=http://localhost:8080
"@
    
    # Criar diretório se não existir
    $frontendDir = "frontend"
    if (-not (Test-Path $frontendDir)) {
        New-Item -ItemType Directory -Path $frontendDir -Force | Out-Null
    }
    
    # Salvar arquivo
    Set-Content -Path $envLocalPath -Value $envContent -Encoding UTF8 -Force
    
    Write-Host "[OK] Arquivo frontend/.env.local atualizado!" -ForegroundColor Green
    Write-Host ""
    Write-Host "IMPORTANTE: Reinicie o frontend para aplicar as mudancas!" -ForegroundColor Yellow
    Write-Host "   Pare o frontend (Ctrl+C) e execute: cd frontend; npm run dev" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "[AVISO] Nao foi possivel obter a URL automaticamente" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "A URL aparecera no terminal do Cloudflare Tunnel" -ForegroundColor Cyan
    Write-Host "Formato: https://xxxx-xxxx-xxxx.trycloudflare.com" -ForegroundColor White
    Write-Host ""
    Write-Host "Quando obtiver a URL, edite manualmente:" -ForegroundColor Yellow
    Write-Host "   frontend/.env.local" -ForegroundColor White
    Write-Host ""
    Write-Host "E adicione:" -ForegroundColor Yellow
    Write-Host "   NEXT_PUBLIC_API_URL=https://SUA-URL.trycloudflare.com" -ForegroundColor Cyan
    Write-Host ""
}

# Resumo final
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "   SISTEMA INICIADO!" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "URLs Locais:" -ForegroundColor Yellow
Write-Host "   Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "   Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "   Proxy:    http://localhost:8080" -ForegroundColor White
Write-Host ""

if ($publicUrl) {
    Write-Host "URL Publica (Cloudflare Tunnel):" -ForegroundColor Yellow
    Write-Host "   $publicUrl" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Acesse esta URL para usar o sistema remotamente!" -ForegroundColor Green
} else {
    Write-Host "URL Publica:" -ForegroundColor Yellow
    Write-Host "   Veja no terminal do Cloudflare Tunnel" -ForegroundColor White
}

Write-Host ""
Write-Host "Para parar tudo, feche todos os terminais abertos" -ForegroundColor Red
Write-Host ""

