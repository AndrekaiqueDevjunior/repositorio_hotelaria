# =========================================
# Servidor Externo - Acesso Completo
# =========================================
# Expõe backend, frontend, banco de dados e tudo

Write-Host "[INICIO] Configurando acesso externo completo..." -ForegroundColor Cyan
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
$dbUrl = "postgresql://postgres:postgres@$ipAddress:5432/hotel_db"
$redisUrl = "redis://$ipAddress:6379"

Write-Host "[URLS] URLs para acesso completo:" -ForegroundColor Cyan
Write-Host "   Frontend: $frontendUrl" -ForegroundColor White
Write-Host "   Backend:  $backendUrl" -ForegroundColor White
Write-Host "   Banco DB: $dbUrl" -ForegroundColor Gray
Write-Host "   Redis:    $redisUrl" -ForegroundColor Gray
Write-Host ""

# Atualizar variáveis de ambiente para rede local
Write-Host "[CONFIG] Configurando variaveis de ambiente..." -ForegroundColor Cyan

# Backend .env
$backendEnvFile = "$PSScriptRoot\backend\.env.docker"
$backendEnvContent = Get-Content $backendEnvFile -Raw

# Atualizar CORS_ORIGINS para permitir qualquer origem (acesso externo)
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

# Configurar cookies para HTTP local
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
Write-Host "[OK] SISTEMA COMPLETO ACESSIVEL EXTERNAMENTE!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "[SHARE] Compartilhe com quem estiver na mesma rede:" -ForegroundColor Cyan
Write-Host ""
Write-Host "   📱 Aplicacao: $frontendUrl" -ForegroundColor White
Write-Host "   🔌 API Backend: $backendUrl" -ForegroundColor White
Write-Host "   🗄️ Banco Dados: $dbUrl" -ForegroundColor Gray
Write-Host "   🔴 Redis: $redisUrl" -ForegroundColor Gray
Write-Host ""
Write-Host "[LOGIN] Credenciais de acesso:" -ForegroundColor Yellow
Write-Host "   Email: admin@hotelreal.com.br" -ForegroundColor White
Write-Host "   Senha: admin123" -ForegroundColor White
Write-Host ""
Write-Host "[DATABASE] Acesso ao banco:" -ForegroundColor Yellow
Write-Host "   Host: $ipAddress" -ForegroundColor Gray
Write-Host "   Porta: 5432" -ForegroundColor Gray
Write-Host "   Usuario: postgres" -ForegroundColor Gray
Write-Host "   Senha: postgres" -ForegroundColor Gray
Write-Host "   Database: hotel_db" -ForegroundColor Gray
Write-Host ""
Write-Host "[IMPORTANTE] Instrucoes:" -ForegroundColor Yellow
Write-Host "   - Funciona na mesma rede (WiFi/Ethernet)" -ForegroundColor Gray
Write-Host "   - CORS configurado para permitir qualquer origem" -ForegroundColor Gray
Write-Host "   - Banco de dados acessivel externamente" -ForegroundColor Gray
Write-Host "   - Redis acessivel externamente" -ForegroundColor Gray
Write-Host "   - Firewalls podem bloquear acesso" -ForegroundColor Gray
Write-Host ""
Write-Host "[TEST] Para testar:" -ForegroundColor Cyan
Write-Host "   1. Frontend: $frontendUrl" -ForegroundColor Gray
Write-Host "   2. API Health: $backendUrl/health" -ForegroundColor Gray
Write-Host "   3. Banco: Use DBeaver/PostgreSQL com $dbUrl" -ForegroundColor Gray
Write-Host ""
Write-Host "[MONITOR] Para monitorar:" -ForegroundColor Cyan
Write-Host "   docker-compose logs -f backend" -ForegroundColor Gray
Write-Host "   docker-compose logs -f frontend" -ForegroundColor Gray
Write-Host "   docker-compose logs -f postgres" -ForegroundColor Gray
Write-Host "   docker-compose logs -f redis" -ForegroundColor Gray
Write-Host ""
Write-Host "[RESTAURAR] Para voltar ao localhost:" -ForegroundColor Cyan
Write-Host "   .\RESTAURAR_CONFIG_LOCAL.ps1" -ForegroundColor Gray
Write-Host ""
Write-Host "[OK] Sistema completo pronto para acesso externo!" -ForegroundColor Green
