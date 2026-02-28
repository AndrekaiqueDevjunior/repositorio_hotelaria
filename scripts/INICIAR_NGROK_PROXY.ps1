# Iniciar Ngrok com Proxy Reverso Unico
# Uso: .\INICIAR_NGROK_PROXY.ps1

Write-Host "[INFO] Iniciando configuracao de proxy reverso..." -ForegroundColor Cyan

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
Write-Host "[INFO] Verificando servicos locais..." -ForegroundColor Yellow

$backendRunning = Test-NetConnection -ComputerName localhost -Port 8000 -InformationLevel Quiet
$frontendRunning = Test-NetConnection -ComputerName localhost -Port 3000 -InformationLevel Quiet

if (-not $backendRunning) {
    Write-Host "[AVISO] Backend nao esta rodando na porta 8000" -ForegroundColor Yellow
    Write-Host "[INFO] Inicie o backend primeiro: docker-compose up backend" -ForegroundColor Cyan
    exit 1
}

if (-not $frontendRunning) {
    Write-Host "[AVISO] Frontend nao esta rodando na porta 3000" -ForegroundColor Yellow
    Write-Host "[INFO] Inicie o frontend primeiro: docker-compose up frontend" -ForegroundColor Cyan
    exit 1
}

# Verificar se http-proxy esta instalado
Write-Host "[INFO] Verificando dependencias do proxy..." -ForegroundColor Yellow
$proxyInstalled = Test-Path "node_modules/http-proxy"

if (-not $proxyInstalled) {
    Write-Host "[INFO] Instalando http-proxy..." -ForegroundColor Cyan
    npm install http-proxy
}

# Iniciar proxy reverso em background
Write-Host "[INFO] Iniciando proxy reverso na porta 9000..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "node proxy-ngrok.js"

Start-Sleep -Seconds 2

# Verificar se proxy esta rodando
$proxyRunning = Test-NetConnection -ComputerName localhost -Port 9000 -InformationLevel Quiet

if (-not $proxyRunning) {
    Write-Host "[ERRO] Proxy nao iniciou corretamente" -ForegroundColor Red
    exit 1
}

Write-Host "[OK] Proxy reverso rodando na porta 9000" -ForegroundColor Green

# Iniciar tunel ngrok para o proxy
Write-Host "[INFO] Iniciando tunel ngrok para o proxy..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "ngrok http 9000 --host-header='localhost:9000'"

Start-Sleep -Seconds 3

# Obter URL via API do ngrok
Write-Host "`n[INFO] Obtendo URL publica..." -ForegroundColor Cyan

try {
    $tunnels = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels"
    
    Write-Host "`n========================================" -ForegroundColor Green
    Write-Host "TUNEL NGROK ATIVO (PROXY REVERSO)" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    
    foreach ($tunnel in $tunnels.tunnels) {
        $url = $tunnel.public_url
        
        Write-Host "`nURL PUBLICA:" -ForegroundColor Yellow
        Write-Host "  $url" -ForegroundColor White
        Write-Host "`nACESSO:" -ForegroundColor Yellow
        Write-Host "  Frontend: $url" -ForegroundColor White
        Write-Host "  Backend:  $url/api/v1/*" -ForegroundColor White
        Write-Host "`nLOCAL:" -ForegroundColor Gray
        Write-Host "  Proxy:    http://localhost:9000" -ForegroundColor Gray
        Write-Host "  Frontend: http://localhost:3000" -ForegroundColor Gray
        Write-Host "  Backend:  http://localhost:8000" -ForegroundColor Gray
    }
    
    Write-Host "`n========================================" -ForegroundColor Green
    Write-Host "`n[IMPORTANTE] Atualize os arquivos .env:" -ForegroundColor Cyan
    Write-Host "1. Backend .env -> CORS_ORIGINS com a URL acima" -ForegroundColor White
    Write-Host "2. Frontend .env.local -> NEXT_PUBLIC_API_URL com URL/api/v1" -ForegroundColor White
    Write-Host "`n[INFO] Dashboard ngrok: http://localhost:4040" -ForegroundColor Cyan
    
} catch {
    Write-Host "[AVISO] Nao foi possivel obter URL automaticamente" -ForegroundColor Yellow
    Write-Host "[INFO] Acesse http://localhost:4040 para ver a URL" -ForegroundColor Cyan
}

Write-Host "`n[INFO] Pressione Ctrl+C nas janelas para encerrar" -ForegroundColor Gray
