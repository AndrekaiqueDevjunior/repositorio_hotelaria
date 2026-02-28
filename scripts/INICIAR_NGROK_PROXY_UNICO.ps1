# Iniciar Ngrok com Proxy Reverso Unico (RECOMENDADO PARA NGROK FREE)
# Uso: .\INICIAR_NGROK_PROXY_UNICO.ps1

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "NGROK FREE - PROXY REVERSO UNICO" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Verificar se ngrok esta instalado
if (-not (Get-Command ngrok -ErrorAction SilentlyContinue)) {
    Write-Host "[ERRO] Ngrok nao encontrado. Instale em: https://ngrok.com/download" -ForegroundColor Red
    exit 1
}

# Verificar se Node.js esta instalado
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "[ERRO] Node.js nao encontrado. Instale em: https://nodejs.org" -ForegroundColor Red
    exit 1
}

# Verificar se servicos estao rodando
Write-Host "[1] Verificando servicos locais..." -ForegroundColor Yellow

$backendRunning = Test-NetConnection -ComputerName localhost -Port 8000 -InformationLevel Quiet -WarningAction SilentlyContinue
$frontendRunning = Test-NetConnection -ComputerName localhost -Port 3000 -InformationLevel Quiet -WarningAction SilentlyContinue

if (-not $backendRunning) {
    Write-Host "[AVISO] Backend nao esta rodando na porta 8000" -ForegroundColor Yellow
    Write-Host "[INFO] Inicie: docker-compose up -d backend frontend" -ForegroundColor Cyan
    exit 1
}

if (-not $frontendRunning) {
    Write-Host "[AVISO] Frontend nao esta rodando na porta 3000" -ForegroundColor Yellow
    Write-Host "[INFO] Inicie: docker-compose up -d backend frontend" -ForegroundColor Cyan
    exit 1
}

Write-Host "[OK] Backend e frontend rodando" -ForegroundColor Green

# Parar ngrok existente
Write-Host "`n[2] Parando ngrok existente..." -ForegroundColor Yellow
Get-Process | Where-Object {$_.ProcessName -like "*ngrok*"} | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Verificar se http-proxy esta instalado
Write-Host "`n[3] Verificando dependencias do proxy..." -ForegroundColor Yellow

$packageJsonPath = "package.json"
$proxyInstalled = $false

if (Test-Path $packageJsonPath) {
    try {
        $packageJson = Get-Content $packageJsonPath -Raw | ConvertFrom-Json
        if ($packageJson.dependencies -and $packageJson.dependencies."http-proxy") {
            $proxyInstalled = $true
            Write-Host "[OK] http-proxy ja instalado" -ForegroundColor Green
        }
    } catch {
        Write-Host "[AVISO] Erro ao ler package.json" -ForegroundColor Yellow
    }
}

if (-not $proxyInstalled) {
    Write-Host "[INFO] Instalando http-proxy..." -ForegroundColor Cyan
    try {
        npm install http-proxy --save
        Write-Host "[OK] http-proxy instalado" -ForegroundColor Green
    } catch {
        Write-Host "[ERRO] Falha ao instalar http-proxy: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "[INFO] Tente manualmente: npm install http-proxy" -ForegroundColor Cyan
        exit 1
    }
}

# Iniciar proxy reverso em background
Write-Host "`n[4] Iniciando proxy reverso na porta 9000..." -ForegroundColor Green

# Verificar se porta 9000 esta livre
$port9000InUse = Test-NetConnection -ComputerName localhost -Port 9000 -InformationLevel Quiet -WarningAction SilentlyContinue
if ($port9000InUse) {
    Write-Host "[AVISO] Porta 9000 ja esta em uso" -ForegroundColor Yellow
    Write-Host "[INFO] Tentando liberar..." -ForegroundColor Gray
    Get-Process | Where-Object {$_.ProcessName -like "*node*" -and $_.MainWindowTitle -like "*proxy*"} | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

Start-Process powershell -ArgumentList "-NoExit", "-Command", "node proxy-ngrok.js"

Start-Sleep -Seconds 3

# Verificar se proxy esta rodando
$proxyRunning = Test-NetConnection -ComputerName localhost -Port 9000 -InformationLevel Quiet -WarningAction SilentlyContinue

if (-not $proxyRunning) {
    Write-Host "[ERRO] Proxy nao iniciou corretamente" -ForegroundColor Red
    Write-Host "[INFO] Verifique o console do proxy para erros" -ForegroundColor Cyan
    exit 1
}

Write-Host "[OK] Proxy reverso rodando na porta 9000" -ForegroundColor Green

# Iniciar tunel ngrok para o proxy
Write-Host "`n[5] Iniciando tunel ngrok para o proxy..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "ngrok http 9000 --host-header='localhost:9000'"

Start-Sleep -Seconds 5

# Obter URL via API do ngrok
Write-Host "`n[6] Obtendo URL publica..." -ForegroundColor Cyan

$retryCount = 0
$maxRetries = 10
$ngrokUrl = ""

while ($retryCount -lt $maxRetries -and -not $ngrokUrl) {
    try {
        $tunnels = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels" -ErrorAction Stop
        
        if ($tunnels.tunnels.Count -gt 0) {
            $ngrokUrl = $tunnels.tunnels[0].public_url
            break
        }
        
        Write-Host "[INFO] Aguardando tunel ngrok... (tentativa $($retryCount + 1))" -ForegroundColor Gray
        Start-Sleep -Seconds 2
        
    } catch {
        Write-Host "[INFO] Aguardando API do ngrok... (tentativa $($retryCount + 1))" -ForegroundColor Gray
        Start-Sleep -Seconds 2
    }
    
    $retryCount++
}

if (-not $ngrokUrl) {
    Write-Host "[ERRO] Nao foi possivel obter URL do ngrok" -ForegroundColor Red
    exit 1
}

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "TUNEL NGROK ATIVO (PROXY REVERSO)" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

Write-Host "`nURL PUBLICA:" -ForegroundColor Yellow
Write-Host "  $ngrokUrl" -ForegroundColor White

Write-Host "`nACESSO:" -ForegroundColor Yellow
Write-Host "  Frontend: $ngrokUrl" -ForegroundColor White
Write-Host "  Backend:  $ngrokUrl/api/v1/*" -ForegroundColor White

Write-Host "`nLOCAL:" -ForegroundColor Gray
Write-Host "  Proxy:    http://localhost:9000" -ForegroundColor Gray
Write-Host "  Frontend: http://localhost:3000" -ForegroundColor Gray
Write-Host "  Backend:  http://localhost:8000" -ForegroundColor Gray

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "`n[IMPORTANTE] Execute o proximo comando:" -ForegroundColor Cyan
Write-Host ".\ATUALIZAR_ENV_PROXY.ps1" -ForegroundColor White

# Salvar URL em arquivo temporario
$urlData = @{
    ngrokUrl = $ngrokUrl
} | ConvertTo-Json

$urlData | Set-Content -Path ".ngrok_proxy_url.tmp" -Encoding UTF8

Write-Host "`n[INFO] Dashboard ngrok: http://localhost:4040" -ForegroundColor Cyan
Write-Host "[INFO] Pressione Ctrl+C na janela do ngrok para encerrar" -ForegroundColor Gray
Write-Host "`n========================================`n" -ForegroundColor Cyan
