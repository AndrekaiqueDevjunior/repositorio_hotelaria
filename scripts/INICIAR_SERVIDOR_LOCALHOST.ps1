# =========================================
# Servidor LocalHost - Fallback Simples
# =========================================
# Apenas localhost, sem rede externa

Write-Host "[INICIO] Configurando acesso localhost apenas..." -ForegroundColor Cyan
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

# URLs localhost
$backendUrl = "http://localhost:8000"
$frontendUrl = "http://localhost:3000"

Write-Host "[URLS] URLs localhost:" -ForegroundColor Cyan
Write-Host "   Frontend: $frontendUrl" -ForegroundColor White
Write-Host "   Backend:  $backendUrl" -ForegroundColor White
Write-Host ""

# Atualizar variáveis de ambiente para localhost
Write-Host "[CONFIG] Configurando variaveis de ambiente..." -ForegroundColor Cyan

# Backend .env
$backendEnvFile = "$PSScriptRoot\backend\.env.docker"
$backendEnvContent = Get-Content $backendEnvFile -Raw

# Atualizar CORS_ORIGINS para localhost apenas
$corsOrigins = "http://localhost:3000,http://localhost:8000"
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

# Configurar cookies para localhost
$backendEnvContent = $backendEnvContent -replace "COOKIE_SECURE=.*", "COOKIE_SECURE=False"
$backendEnvContent = $backendEnvContent -replace "COOKIE_SAMESITE=.*", "COOKIE_SAMESITE=lax"
$backendEnvContent = $backendEnvContent -replace "COOKIE_DOMAIN=.*", "COOKIE_DOMAIN=.localhost"

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
Write-Host "[OK] SISTEMA PRONTO EM LOCALHOST!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "[ACCESS] Acesse no seu navegador:" -ForegroundColor Cyan
Write-Host ""
Write-Host "   Aplicacao: $frontendUrl" -ForegroundColor White
Write-Host "   API:       $backendUrl" -ForegroundColor White
Write-Host ""
Write-Host "[LOGIN] Credenciais de acesso:" -ForegroundColor Yellow
Write-Host "   Email: admin@hotelreal.com.br" -ForegroundColor White
Write-Host "   Senha: admin123" -ForegroundColor White
Write-Host ""
Write-Host "[IMPORTANTE] Instrucoes:" -ForegroundColor Yellow
Write-Host "   - Apenas localhost (seu computador)" -ForegroundColor Gray
Write-Host "   - Sem acesso externo" -ForegroundColor Gray
Write-Host "   - Sem problemas de firewall/rede" -ForegroundColor Gray
Write-Host "   - Funciona imediatamente" -ForegroundColor Gray
Write-Host ""
Write-Host "[TEST] Para testar:" -ForegroundColor Cyan
Write-Host "   1. Abra: $frontendUrl" -ForegroundColor Gray
Write-Host "   2. Faca login com as credenciais acima" -ForegroundColor Gray
Write-Host "   3. Teste todas as funcionalidades" -ForegroundColor Gray
Write-Host ""
Write-Host "[MONITOR] Para monitorar:" -ForegroundColor Cyan
Write-Host "   docker-compose logs -f backend" -ForegroundColor Gray
Write-Host "   docker-compose logs -f frontend" -ForegroundColor Gray
Write-Host ""
Write-Host "[OK] Sistema pronto em localhost!" -ForegroundColor Green
