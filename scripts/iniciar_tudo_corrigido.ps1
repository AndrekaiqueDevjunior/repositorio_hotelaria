# Script Corrigido - Inicia tudo e aguarda cada serviço ficar pronto

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "   Iniciar Sistema - Versao Corrigida" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

# Função para aguardar serviço ficar pronto
function Wait-ForService {
    param(
        [string]$Url,
        [string]$Name,
        [int]$MaxAttempts = 30,
        [int]$DelaySeconds = 2
    )
    
    Write-Host "   Aguardando $Name ficar pronto..." -ForegroundColor Yellow -NoNewline
    
    for ($i = 1; $i -le $MaxAttempts; $i++) {
        try {
            $response = Invoke-WebRequest -Uri $Url -TimeoutSec 2 -ErrorAction Stop
            Write-Host " [OK]" -ForegroundColor Green
            return $true
        } catch {
            Start-Sleep -Seconds $DelaySeconds
            Write-Host "." -NoNewline -ForegroundColor Gray
        }
    }
    
    Write-Host " [FALHOU]" -ForegroundColor Red
    return $false
}

# 1. Parar tudo primeiro
Write-Host "[1/6] Parando processos antigos..." -ForegroundColor Cyan

# Parar Cloudflare Tunnels
$cloudflared = Get-Process -Name "cloudflared" -ErrorAction SilentlyContinue
if ($cloudflared) {
    Write-Host "   Parando $($cloudflared.Count) processo(s) Cloudflare..." -ForegroundColor Yellow
    $cloudflared | ForEach-Object {
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 2
}

# Parar processos nas portas
$ports = @(8000, 3000, 8080)
foreach ($port in $ports) {
    $processes = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | 
        Where-Object { $_.State -eq "Listen" } | 
        Select-Object -ExpandProperty OwningProcess -Unique
    if ($processes) {
        $processes | ForEach-Object {
            Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue
        }
    }
}

Start-Sleep -Seconds 2
Write-Host "   [OK] Processos parados" -ForegroundColor Green
Write-Host ""

# 2. Verificar requisitos
Write-Host "[2/6] Verificando requisitos..." -ForegroundColor Cyan

try {
    node --version | Out-Null
    Write-Host "   [OK] Node.js" -ForegroundColor Green
} catch {
    Write-Host "   [ERRO] Node.js nao encontrado!" -ForegroundColor Red
    exit 1
}

try {
    cloudflared --version | Out-Null
    Write-Host "   [OK] cloudflared" -ForegroundColor Green
} catch {
    Write-Host "   [ERRO] cloudflared nao encontrado!" -ForegroundColor Red
    exit 1
}

$certPath = "$env:USERPROFILE\.cloudflared\cert.pem"
if (-not (Test-Path $certPath)) {
    Write-Host "   [ERRO] Cloudflare nao autenticado!" -ForegroundColor Red
    Write-Host "   Execute: .\configurar_cloudflare_login.ps1" -ForegroundColor Yellow
    exit 1
}
Write-Host "   [OK] Cloudflare autenticado" -ForegroundColor Green
Write-Host ""

# 3. Instalar dependências
Write-Host "[3/6] Verificando dependencias..." -ForegroundColor Cyan
if (-not (Test-Path "node_modules\express")) {
    Write-Host "   Instalando dependencias..." -ForegroundColor Yellow
    npm install --silent | Out-Null
}
Write-Host "   [OK] Dependencias OK" -ForegroundColor Green
Write-Host ""

# 4. Iniciar Backend
Write-Host "[4/6] Iniciando Backend..." -ForegroundColor Cyan
$backendScript = @"
cd '$PWD\backend'
.\venv312\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
"@
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendScript | Out-Null
Start-Sleep -Seconds 3

if (-not (Wait-ForService -Url "http://localhost:8000/health" -Name "Backend")) {
    Write-Host "   [AVISO] Backend pode estar iniciando ainda..." -ForegroundColor Yellow
}
Write-Host ""

# 5. Iniciar Frontend
Write-Host "[5/6] Iniciando Frontend..." -ForegroundColor Cyan
$frontendScript = @"
cd '$PWD\frontend'
npm run dev
"@
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendScript | Out-Null
Start-Sleep -Seconds 3

if (-not (Wait-ForService -Url "http://localhost:3000" -Name "Frontend")) {
    Write-Host "   [AVISO] Frontend pode estar iniciando ainda..." -ForegroundColor Yellow
}
Write-Host ""

# 6. Iniciar Proxy
Write-Host "[6/6] Iniciando Proxy..." -ForegroundColor Cyan
$proxyScript = @"
cd '$PWD'
Write-Host '=== PROXY SERVER ===' -ForegroundColor Green
node proxy-server.js
"@
Start-Process powershell -ArgumentList "-NoExit", "-Command", $proxyScript | Out-Null
Start-Sleep -Seconds 3

if (-not (Wait-ForService -Url "http://localhost:8080/health" -Name "Proxy")) {
    Write-Host "   [ERRO] Proxy nao iniciou corretamente!" -ForegroundColor Red
    Write-Host "   Verifique os logs do proxy no terminal" -ForegroundColor Yellow
} else {
    Write-Host "   [OK] Proxy respondendo!" -ForegroundColor Green
}
Write-Host ""

# Aguardar um pouco mais para garantir que tudo está estável
Write-Host "Aguardando servicos ficarem estaveis..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Iniciar Cloudflare Tunnel
Write-Host ""
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "   Iniciando Cloudflare Tunnel..." -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

# Criar arquivo temporário para capturar URL
$tempLogFile = Join-Path $env:TEMP "cloudflared-url-$(Get-Date -Format 'yyyyMMdd-HHmmss').txt"

$tunnelScript = @"
cd '$PWD'
`$ErrorActionPreference = 'Continue'
`$urlFile = '$tempLogFile'

Write-Host '===============================================' -ForegroundColor Cyan
Write-Host '   Cloudflare Tunnel - Proxy Unificado' -ForegroundColor Green
Write-Host '===============================================' -ForegroundColor Cyan
Write-Host ''
Write-Host 'Este tunel serve TANTO frontend quanto API' -ForegroundColor Yellow
Write-Host 'URL publica aparecera abaixo:' -ForegroundColor Cyan
Write-Host ''

cloudflared tunnel --url http://localhost:8080 2>&1 | ForEach-Object {
    `$line = `$_
    Write-Host `$line -ForegroundColor Cyan
    
    if (`$line -match 'https://([a-z0-9-]+)\.trycloudflare\.com') {
        `$url = `$matches[0]
        `$url | Out-File `$urlFile -Encoding UTF8 -Force
        Write-Host ''
        Write-Host '===============================================' -ForegroundColor Green
        Write-Host "   URL PUBLICA: `$url" -ForegroundColor Green
        Write-Host '===============================================' -ForegroundColor Green
        Write-Host ''
    }
}
"@

$tunnelProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", $tunnelScript -PassThru

Write-Host "Aguardando URL publica do Cloudflare Tunnel..." -ForegroundColor Yellow
Write-Host "(Isso pode levar 10-20 segundos)" -ForegroundColor Gray
Write-Host ""

$urlFound = $false
$publicUrl = ""

for ($i = 1; $i -le 40; $i++) {
    Start-Sleep -Seconds 1
    
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

# Atualizar .env.local
if ($urlFound -and $publicUrl) {
    Write-Host "===============================================" -ForegroundColor Green
    Write-Host "   URL PUBLICA OBTIDA!" -ForegroundColor Green
    Write-Host "===============================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "URL: $publicUrl" -ForegroundColor Cyan
    Write-Host ""
    
    $envLocalPath = "frontend\.env.local"
    $envContent = @"
# Configuracao automatica - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
NEXT_PUBLIC_API_URL=$publicUrl

# URLs de referencia
NEXT_PUBLIC_API_URL_LOCAL=http://localhost:8000
NEXT_PUBLIC_PROXY_URL=http://localhost:8080
"@
    
    Set-Content -Path $envLocalPath -Value $envContent -Encoding UTF8 -Force
    Write-Host "[OK] frontend/.env.local atualizado!" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "[AVISO] URL nao capturada automaticamente" -ForegroundColor Yellow
    Write-Host "Veja o terminal do Cloudflare Tunnel para a URL" -ForegroundColor Cyan
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
    Write-Host "URL Publica:" -ForegroundColor Yellow
    Write-Host "   $publicUrl" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "IMPORTANTE:" -ForegroundColor Yellow
    Write-Host "   Reinicie o frontend para aplicar mudancas no .env.local" -ForegroundColor White
    Write-Host "   (Ou aguarde o Next.js recarregar automaticamente)" -ForegroundColor Gray
} else {
    Write-Host "URL Publica:" -ForegroundColor Yellow
    Write-Host "   Veja no terminal do Cloudflare Tunnel" -ForegroundColor White
}

Write-Host ""
Write-Host "Para parar tudo, feche todos os terminais" -ForegroundColor Red
Write-Host ""

