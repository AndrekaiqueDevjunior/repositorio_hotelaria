# =========================================
# ngrok - Acesso Externo Global
# =========================================

Write-Host "[INICIO] Configurando ngrok para acesso externo..." -ForegroundColor Cyan
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

# Verificar se ngrok está instalado
$ngrokExists = Get-Command ngrok -ErrorAction SilentlyContinue
if (-not $ngrokExists) {
    Write-Host "[ERROR] ngrok nao esta instalado!" -ForegroundColor Red
    Write-Host "[INFO] Instale: choco install ngrok" -ForegroundColor Yellow
    Write-Host "[INFO] Ou baixe: https://ngrok.com/download" -ForegroundColor Yellow
    exit 1
}

Write-Host "[OK] ngrok instalado" -ForegroundColor Green
Write-Host ""

# Iniciar ngrok para backend
Write-Host "[SETUP] Iniciando ngrok para Backend (porta 8000)..." -ForegroundColor Cyan
$backendProcess = Start-Process -FilePath "ngrok" -ArgumentList "http 8000 --log=stdout" -PassThru -WindowStyle Normal

Start-Sleep -Seconds 5

# Iniciar ngrok para frontend
Write-Host "[SETUP] Iniciando ngrok para Frontend (porta 3000)..." -ForegroundColor Cyan
$frontendProcess = Start-Process -FilePath "ngrok" -ArgumentList "http 3000 --log=stdout" -PassThru -WindowStyle Normal

Start-Sleep -Seconds 5

# Obter URLs do ngrok via API
Write-Host "[API] Obtendo URLs do ngrok..." -ForegroundColor Cyan
Start-Sleep -Seconds 3

try {
    $ngrokApi = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels" -ErrorAction Stop
    
    $tunnels = $ngrokApi.tunnels
    $backendTunnel = $tunnels | Where-Object { $_.config.addr -like "*8000" } | Select-Object -First 1
    $frontendTunnel = $tunnels | Where-Object { $_.config.addr -like "*3000" } | Select-Object -First 1
    
    $backendUrl = $backendTunnel.public_url
    $frontendUrl = $frontendTunnel.public_url
    
    if (-not $backendUrl -or -not $frontendUrl) {
        Write-Host "[WARN] Nao foi possivel obter URLs automaticamente" -ForegroundColor Yellow
        Write-Host "[INFO] Verifique manualmente em: http://localhost:4040" -ForegroundColor Yellow
        
        $backendUrl = "https://BACKEND-URL.ngrok.io"
        $frontendUrl = "https://FRONTEND-URL.ngrok.io"
    }
    
} catch {
    Write-Host "[WARN] Erro ao obter URLs da API ngrok" -ForegroundColor Yellow
    Write-Host "[INFO] Verifique manualmente em: http://localhost:4040" -ForegroundColor Yellow
    
    $backendUrl = "https://BACKEND-URL.ngrok.io"
    $frontendUrl = "https://FRONTEND-URL.ngrok.io"
}

Write-Host ""
Write-Host "[OK] ngrok iniciado!" -ForegroundColor Green
Write-Host ""
Write-Host "[URLS] URLs Publicas:" -ForegroundColor Cyan
Write-Host "   Backend:  $backendUrl" -ForegroundColor White
Write-Host "   Frontend: $frontendUrl" -ForegroundColor White
Write-Host ""

# Atualizar variáveis de ambiente
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

# ngrok usa HTTPS, configurar cookies
$backendEnvContent = $backendEnvContent -replace "COOKIE_SECURE=.*", "COOKIE_SECURE=True"
$backendEnvContent = $backendEnvContent -replace "COOKIE_SAMESITE=.*", "COOKIE_SAMESITE=none"
$backendEnvContent = $backendEnvContent -replace "COOKIE_DOMAIN=.*", "COOKIE_DOMAIN="

Set-Content -Path $backendEnvFile -Value $backendEnvContent

# Frontend .env
$frontendEnvFile = "$PSScriptRoot\frontend\.env.local"
$frontendEnvContent = "NEXT_PUBLIC_API_URL=$backendUrl/api/v1"
Set-Content -Path $frontendEnvFile -Value $frontendEnvContent

Write-Host "[OK] Variaveis de ambiente atualizadas" -ForegroundColor Green
Write-Host ""

# Reiniciar containers
Write-Host "[RESTART] Reiniciando containers..." -ForegroundColor Cyan
docker-compose restart backend frontend

Write-Host ""
Write-Host "[WAIT] Aguardando containers iniciarem..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "[OK] SISTEMA ACESSIVEL GLOBALMENTE!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "[SHARE] URLs para compartilhar:" -ForegroundColor Cyan
Write-Host ""
Write-Host "   Aplicacao: $frontendUrl" -ForegroundColor White
Write-Host "   API:       $backendUrl" -ForegroundColor White
Write-Host ""
Write-Host "[LOGIN] Credenciais:" -ForegroundColor Yellow
Write-Host "   Email: admin@hotelreal.com.br" -ForegroundColor White
Write-Host "   Senha: admin123" -ForegroundColor White
Write-Host ""
Write-Host "[IMPORTANTE] Instrucoes:" -ForegroundColor Yellow
Write-Host "   - URLs com HTTPS seguro" -ForegroundColor Gray
Write-Host "   - Funciona de qualquer lugar" -ForegroundColor Gray
Write-Host "   - Dashboard ngrok: http://localhost:4040" -ForegroundColor Gray
Write-Host "   - Cookie autenticacao configurado" -ForegroundColor Gray
Write-Host ""
Write-Host "[DASHBOARD] Para ver estatisticas:" -ForegroundColor Cyan
Write-Host "   Abra no navegador: http://localhost:4040" -ForegroundColor Gray
Write-Host ""
Write-Host "[MONITOR] Para monitorar:" -ForegroundColor Cyan
Write-Host "   docker-compose logs -f backend" -ForegroundColor Gray
Write-Host "   docker-compose logs -f frontend" -ForegroundColor Gray
Write-Host ""
Write-Host "[STOP] Para parar:" -ForegroundColor Red
Write-Host "   Pressione Ctrl+C ou feche as janelas ngrok" -ForegroundColor Gray
Write-Host ""

# Manter script rodando
Write-Host "[RUNNING] ngrok ativo. Pressione Ctrl+C para parar..." -ForegroundColor Yellow
Write-Host ""

# Loop infinito até Ctrl+C
try {
    while ($true) {
        Start-Sleep -Seconds 5
        
        # Verificar se processos ainda estão rodando
        if ($backendProcess.HasExited -or $frontendProcess.HasExited) {
            Write-Host ""
            Write-Host "[WARN] Um ou mais tunnels pararam." -ForegroundColor Yellow
            Write-Host "[INFO] Reinicie o script se necessario" -ForegroundColor Yellow
            break
        }
    }
} finally {
    Write-Host ""
    Write-Host "[STOP] Parando ngrok..." -ForegroundColor Red
    
    # Matar processos
    if (-not $backendProcess.HasExited) {
        Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
    }
    
    if (-not $frontendProcess.HasExited) {
        Stop-Process -Id $frontendProcess.Id -Force -ErrorAction SilentlyContinue
    }
    
    # Matar todos os processos ngrok
    Get-Process | Where-Object { $_.ProcessName -like "*ngrok*" } | Stop-Process -Force -ErrorAction SilentlyContinue
    
    Write-Host "[OK] ngrok parado" -ForegroundColor Green
    Write-Host ""
    Write-Host "[INFO] Para restaurar configuracao local:" -ForegroundColor Cyan
    Write-Host "   .\RESTAURAR_CONFIG_LOCAL.ps1" -ForegroundColor Gray
}
