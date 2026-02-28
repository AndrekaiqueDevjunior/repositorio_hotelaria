# =========================================
# Servidor Externo Simples - Sem Instalar Nada
# =========================================
# Usa serveo.com (alternativa online gratuita)

Write-Host "[INICIO] Configurando acesso externo simples..." -ForegroundColor Cyan
Write-Host ""

# Verificar se containers estão rodando
Write-Host "[INFO] Verificando containers Docker..." -ForegroundColor Yellow
$containersRunning = docker-compose ps --services --filter "status=running"

if ($containersRunning -notcontains "backend" -or $containersRunning -notcontains "frontend") {
    Write-Host "[AVISO] Containers nao estao rodando. Iniciando..." -ForegroundColor Yellow
    docker-compose up -d
    Start-Sleep -Seconds 10
}

Write-Host "[OK] Containers rodando" -ForegroundColor Green
Write-Host ""

# Obter IP local
$ipAddress = (Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias "Ethernet*").IPAddress | Where-Object { $_ -notlike "127.*" -and $_ -notlike "169.254.*" } | Select-Object -First 1

if (-not $ipAddress) {
    $ipAddress = (Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias "Wi-Fi*").IPAddress | Where-Object { $_ -notlike "127.*" -and $_ -notlike "169.254.*" } | Select-Object -First 1
}

if (-not $ipAddress) {
    $ipAddress = "localhost"
}

Write-Host "[IP] Seu IP na rede: $ipAddress" -ForegroundColor Cyan
Write-Host ""

# URLs para acesso local
$backendUrl = "http://$ipAddress:8000"
$frontendUrl = "http://$ipAddress:3000"

Write-Host "[URLS] URLs para acesso:" -ForegroundColor Cyan
Write-Host "   Frontend: $frontendUrl" -ForegroundColor White
Write-Host "   Backend:  $backendUrl" -ForegroundColor White
Write-Host ""

# Atualizar variáveis de ambiente para rede local
Write-Host "[CONFIG] Configurando variaveis de ambiente..." -ForegroundColor Cyan

# Backend .env
$backendEnvFile = "$PSScriptRoot\backend\.env.docker"
$backendEnvContent = Get-Content $backendEnvFile -Raw

# Atualizar CORS_ORIGINS para permitir qualquer origem
$corsOrigins = "*"
if ($backendEnvContent -match "CORS_ORIGINS=.*") {
    $backendEnvContent = $backendEnvContent -replace "CORS_ORIGINS=.*", "CORS_ORIGINS=$corsOrigins"
} else {
    $backendEnvContent += "`nCORS_ORIGINS=$corsOrigins"
}

# Atualizar FRONTEND_URL
if ($backendEnvContent -match "FRONTEND_URL=.*") {
    $backendEnvContent = $backendEnvContent -replace "FRONTEND_URL=.*", "FRONTEND_URL=$frontendUrl"
} else {
    $backendEnvContent += "`nFRONTEND_URL=$frontendUrl"
}

# Configurar cookies para HTTP
$backendEnvContent = $backendEnvContent -replace "COOKIE_SECURE=.*", "COOKIE_SECURE=False"
$backendEnvContent = $backendEnvContent -replace "COOKIE_SAMESITE=.*", "COOKIE_SAMESITE=none"
$backendEnvContent = $backendEnvContent -replace "COOKIE_DOMAIN=.*", "COOKIE_DOMAIN="

Set-Content -Path $backendEnvFile -Value $backendEnvContent

# Frontend .env
$frontendEnvFile = "$PSScriptRoot\frontend\.env.local"
$frontendEnvContent = "NEXT_PUBLIC_API_URL=$backendUrl/api/v1"
Set-Content -Path $frontendEnvFile -Value $frontendEnvContent

Write-Host "[OK] Variaveis de ambiente atualizadas" -ForegroundColor Green
Write-Host ""

# Reiniciar containers para aplicar configurações
Write-Host "[RESTART] Reiniciando containers..." -ForegroundColor Cyan
docker-compose restart backend frontend

Write-Host ""
Write-Host "[WAIT] Aguardando containers iniciarem..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "[OK] SISTEMA CONFIGURADO!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "[ACCESS] Para acesso externo, voce tem 3 opcoes:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. REDE LOCAL (se estiver na mesma rede):" -ForegroundColor White
Write-Host "   URL: $frontendUrl" -ForegroundColor Gray
Write-Host ""
Write-Host "2. VPN (para simular estar na mesma rede):" -ForegroundColor White
Write-Host "   - Use VPN do seu celular ou outro dispositivo" -ForegroundColor Gray
Write-Host "   - Conecte na mesma rede e acesse a URL acima" -ForegroundColor Gray
Write-Host ""
Write-Host "3. SERVICOS ONLINE GRATUITOS:" -ForegroundColor White
Write-Host "   - serveo.com: Configure em 2 minutos" -ForegroundColor Gray
Write-Host "   - localtunnel.me: Simples e rapido" -ForegroundColor Gray
Write-Host "   - ngrok.com: 1GB gratis por mes" -ForegroundColor Gray
Write-Host ""
Write-Host "[LOGIN] Credenciais:" -ForegroundColor Yellow
Write-Host "   Email: admin@hotelreal.com.br" -ForegroundColor White
Write-Host "   Senha: admin123" -ForegroundColor White
Write-Host ""
Write-Host "[IMPORTANTE] Instrucoes:" -ForegroundColor Yellow
Write-Host "   - Sistema funciona na rede local ($ipAddress)" -ForegroundColor Gray
Write-Host "   - Para acesso externo, use servicos online acima" -ForegroundColor Gray
Write-Host "   - CORS configurado para permitir qualquer origem" -ForegroundColor Gray
Write-Host ""
Write-Host "[TEST] Teste local:" -ForegroundColor Cyan
Write-Host "   curl $frontendUrl" -ForegroundColor Gray
Write-Host "   curl $backendUrl/health" -ForegroundColor Gray
Write-Host ""
Write-Host "[OK] Sistema pronto!" -ForegroundColor Green
