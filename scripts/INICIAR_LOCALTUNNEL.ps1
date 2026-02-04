# =========================================
# LocalTunnel - Expose Backend + Frontend
# =========================================
# Sistema de gestão hoteleira com autenticação JWT em cookies
# Autor: Sistema Hotel Cabo Frio
# Data: 2026-01-03

Write-Host "[INICIO] Iniciando LocalTunnel para Backend e Frontend..." -ForegroundColor Cyan
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

# Criar diretório temporário para armazenar URLs
$tempDir = "$PSScriptRoot\.localtunnel"
if (-not (Test-Path $tempDir)) {
    New-Item -ItemType Directory -Path $tempDir | Out-Null
}

# Arquivo para armazenar URLs
$urlFile = "$tempDir\urls.json"

Write-Host "[CONFIG] Configurando LocalTunnel..." -ForegroundColor Cyan
Write-Host ""

# Função para iniciar tunnel e capturar URL
function Start-Tunnel {
    param(
        [string]$Port,
        [string]$Subdomain,
        [string]$Name
    )
    
    Write-Host "[TUNNEL] Iniciando tunnel para $Name (porta $Port)..." -ForegroundColor Yellow
    
    # Iniciar localtunnel em background sem minimizar para ver output
    if ($Subdomain) {
        $process = Start-Process -FilePath "npx" -ArgumentList "localtunnel --port $Port --subdomain $Subdomain" -PassThru -WindowStyle Normal
    } else {
        $process = Start-Process -FilePath "npx" -ArgumentList "localtunnel --port $Port" -PassThru -WindowStyle Normal
    }
    
    # Aguardar mais tempo para tunnel conectar
    Write-Host "[WAIT] Aguardando tunnel conectar (10 segundos)..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    
    # URL do tunnel
    if ($Subdomain) {
        $url = "https://$Subdomain.loca.lt"
    } else {
        # LocalTunnel gera URL aleatória, precisamos capturar do output
        # Para simplificar, vamos usar subdomain fixo
        $url = "https://hotel-$Name-$(Get-Random -Minimum 1000 -Maximum 9999).loca.lt"
    }
    
    # Testar se tunnel está respondendo
    Write-Host "[TEST] Testando conexao com $url..." -ForegroundColor Yellow
    try {
        $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "[OK] Tunnel respondendo!" -ForegroundColor Green
        } else {
            Write-Host "[WARN] Tunnel respondeu com status $($response.StatusCode)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "[ERROR] Tunnel nao respondendo: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    return @{
        Url = $url
        Process = $process
        Port = $Port
        Name = $Name
    }
}

Write-Host "[IMPORTANTE] LocalTunnel pode pedir para abrir URL no navegador" -ForegroundColor Yellow
Write-Host "   Se aparecer página de aviso, clique em 'Click to Continue'" -ForegroundColor Yellow
Write-Host ""

# Gerar subdomínios únicos baseados em timestamp
$timestamp = Get-Date -Format "yyyyMMddHHmm"
$backendSubdomain = "hotel-api-$timestamp"
$frontendSubdomain = "hotel-app-$timestamp"

# Iniciar tunnels
Write-Host "[SETUP] Iniciando Backend Tunnel..." -ForegroundColor Cyan
$backendTunnel = Start-Tunnel -Port 8000 -Subdomain $backendSubdomain -Name "backend"

Write-Host "[SETUP] Iniciando Frontend Tunnel..." -ForegroundColor Cyan
$frontendTunnel = Start-Tunnel -Port 3000 -Subdomain $frontendSubdomain -Name "frontend"

Start-Sleep -Seconds 3

# URLs finais
$backendUrl = $backendTunnel.Url
$frontendUrl = $frontendTunnel.Url

Write-Host ""
Write-Host "[OK] Tunnels iniciados com sucesso!" -ForegroundColor Green
Write-Host ""
Write-Host "[URLS] URLs Publicas:" -ForegroundColor Cyan
Write-Host "   Backend:  $backendUrl" -ForegroundColor White
Write-Host "   Frontend: $frontendUrl" -ForegroundColor White
Write-Host ""

# Salvar URLs em arquivo JSON
$urlData = @{
    backend = $backendUrl
    frontend = $frontendUrl
    timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    backendPort = 8000
    frontendPort = 3000
}

$urlData | ConvertTo-Json | Set-Content -Path $urlFile

Write-Host "[SAVE] URLs salvas em: $urlFile" -ForegroundColor Yellow
Write-Host ""

# Atualizar variáveis de ambiente
Write-Host "[CONFIG] Configurando variaveis de ambiente..." -ForegroundColor Cyan

# Backend .env
$backendEnvFile = "$PSScriptRoot\backend\.env.docker"
$backendEnvContent = Get-Content $backendEnvFile -Raw

# Atualizar CORS_ORIGINS
$corsOrigins = "$backendUrl,$frontendUrl"
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

# Configurar Cookie para produção (LocalTunnel usa HTTPS)
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

# Reiniciar containers para aplicar novas configurações
Write-Host "[RESTART] Reiniciando containers com novas configuracoes..." -ForegroundColor Cyan
docker-compose restart backend frontend

Write-Host ""
Write-Host "[WAIT] Aguardando containers iniciarem..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "[OK] SISTEMA PRONTO PARA ACESSO EXTERNO!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "[SHARE] URLs para compartilhar:" -ForegroundColor Cyan
Write-Host ""
Write-Host "   Aplicacao: $frontendUrl" -ForegroundColor White
Write-Host "   API:       $backendUrl" -ForegroundColor White
Write-Host ""
Write-Host "[LOGIN] Credenciais de acesso:" -ForegroundColor Yellow
Write-Host "   Email: admin@hotelreal.com.br" -ForegroundColor White
Write-Host "   Senha: admin123" -ForegroundColor White
Write-Host ""
Write-Host "[IMPORTANTE] Instrucoes:" -ForegroundColor Yellow
Write-Host "   - Na primeira vez, LocalTunnel pode mostrar página de aviso" -ForegroundColor Gray
Write-Host "   - Clique em 'Click to Continue' para acessar" -ForegroundColor Gray
Write-Host "   - Cookie de autenticação está configurado (HttpOnly, Secure)" -ForegroundColor Gray
Write-Host "   - Sessão persiste após refresh da página" -ForegroundColor Gray
Write-Host ""
Write-Host "[MONITOR] Para monitorar:" -ForegroundColor Cyan
Write-Host "   docker-compose logs -f backend" -ForegroundColor Gray
Write-Host "   docker-compose logs -f frontend" -ForegroundColor Gray
Write-Host ""
Write-Host "[STOP] Para parar os tunnels:" -ForegroundColor Red
Write-Host "   Pressione Ctrl+C nesta janela" -ForegroundColor Gray
Write-Host ""

# Manter script rodando
Write-Host "[RUNNING] Tunnels ativos. Pressione Ctrl+C para parar..." -ForegroundColor Yellow
Write-Host ""

# Criar arquivo de processo para controle
$processFile = "$tempDir\processes.txt"
"Backend PID: $($backendTunnel.Process.Id)" | Out-File -FilePath $processFile
"Frontend PID: $($frontendTunnel.Process.Id)" | Out-File -FilePath $processFile -Append

# Loop infinito até Ctrl+C
try {
    while ($true) {
        Start-Sleep -Seconds 5
        
        # Verificar se processos ainda estão rodando
        if ($backendTunnel.Process.HasExited -or $frontendTunnel.Process.HasExited) {
            Write-Host ""
            Write-Host "[WARN] Um ou mais tunnels pararam. Reiniciando..." -ForegroundColor Yellow
            
            if ($backendTunnel.Process.HasExited) {
                $backendTunnel = Start-Tunnel -Port 8000 -Subdomain $backendSubdomain -Name "backend"
            }
            
            if ($frontendTunnel.Process.HasExited) {
                $frontendTunnel = Start-Tunnel -Port 3000 -Subdomain $frontendSubdomain -Name "frontend"
            }
        }
    }
} finally {
    Write-Host ""
    Write-Host "[STOP] Parando tunnels..." -ForegroundColor Red
    
    # Matar processos
    if (-not $backendTunnel.Process.HasExited) {
        Stop-Process -Id $backendTunnel.Process.Id -Force -ErrorAction SilentlyContinue
    }
    
    if (-not $frontendTunnel.Process.HasExited) {
        Stop-Process -Id $frontendTunnel.Process.Id -Force -ErrorAction SilentlyContinue
    }
    
    # Matar todos os processos localtunnel
    Get-Process | Where-Object { $_.ProcessName -like "*localtunnel*" -or $_.ProcessName -like "*lt*" } | Stop-Process -Force -ErrorAction SilentlyContinue
    
    Write-Host "[OK] Tunnels parados" -ForegroundColor Green
    Write-Host ""
    Write-Host "[INFO] Para restaurar configuracao local:" -ForegroundColor Cyan
    Write-Host "   Execute: .\RESTAURAR_CONFIG_LOCAL.ps1" -ForegroundColor Gray
}
