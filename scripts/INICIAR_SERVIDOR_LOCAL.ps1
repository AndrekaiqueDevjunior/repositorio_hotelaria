# =========================================
# Servidor Local - Acesso via Rede Local
# =========================================
# Expose sistema na rede local (sem internet)

Write-Host "[INICIO] Configurando acesso via rede local..." -ForegroundColor Cyan
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

Write-Host "[URLS] URLs para acesso local:" -ForegroundColor Cyan
Write-Host "   Frontend: $frontendUrl" -ForegroundColor White
Write-Host "   Backend:  $backendUrl" -ForegroundColor White
Write-Host ""

# Atualizar variáveis de ambiente para rede local
Write-Host "[CONFIG] Configurando variaveis de ambiente..." -ForegroundColor Cyan

# Backend .env
$backendEnvFile = "$PSScriptRoot\backend\.env.docker"
$backendEnvContent = Get-Content $backendEnvFile -Raw

# Atualizar CORS_ORIGINS
$corsOrigins = "$backendUrl,$frontendUrl,http://localhost:3000,http://localhost:8000"
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
$backendEnvContent = $backendEnvContent -replace "COOKIE_SAMESITE=.*", "COOKIE_SAMESITE=lax"
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
Write-Host "[OK] SISTEMA ACESSIVEL NA REDE LOCAL!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "[SHARE] Compartilhe com quem estiver na mesma rede:" -ForegroundColor Cyan
Write-Host ""
Write-Host "   Aplicacao: $frontendUrl" -ForegroundColor White
Write-Host "   API:       $backendUrl" -ForegroundColor White
Write-Host ""
Write-Host "[LOGIN] Credenciais de acesso:" -ForegroundColor Yellow
Write-Host "   Email: admin@hotelreal.com.br" -ForegroundColor White
Write-Host "   Senha: admin123" -ForegroundColor White
Write-Host ""
Write-Host "[IMPORTANTE] Instrucoes:" -ForegroundColor Yellow
Write-Host "   - Funciona apenas na mesma rede (WiFi/Ethernet)" -ForegroundColor Gray
Write-Host "   - Nao precisa de internet externa" -ForegroundColor Gray
Write-Host "   - Ideal para apresentacoes na empresa" -ForegroundColor Gray
Write-Host "   - Firewalls podem bloquear acesso" -ForegroundColor Gray
Write-Host ""
Write-Host "[TEST] Para testar:" -ForegroundColor Cyan
Write-Host "   1. No seu PC: $frontendUrl" -ForegroundColor Gray
Write-Host "   2. No celular/tablet (mesma WiFi): $frontendUrl" -ForegroundColor Gray
Write-Host ""
Write-Host "[MONITOR] Para monitorar:" -ForegroundColor Cyan
Write-Host "   docker-compose logs -f backend" -ForegroundColor Gray
Write-Host "   docker-compose logs -f frontend" -ForegroundColor Gray
Write-Host ""
Write-Host "[RESTAURAR] Para voltar ao localhost:" -ForegroundColor Cyan
Write-Host "   .\RESTAURAR_CONFIG_LOCAL.ps1" -ForegroundColor Gray
Write-Host ""
Write-Host "[OK] Sistema pronto para uso na rede local!" -ForegroundColor Green
