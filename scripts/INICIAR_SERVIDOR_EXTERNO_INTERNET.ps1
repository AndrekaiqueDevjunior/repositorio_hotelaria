# =========================================
# Servidor Externo Internet - Acesso Global
# =========================================
# Para acesso de qualquer lugar (fora da rede local)

Write-Host "[INICIO] Configurando acesso externo via internet..." -ForegroundColor Cyan
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

# Verificar se bore está instalado
Write-Host "[CHECK] Verificando instalacao do Bore..." -ForegroundColor Yellow
$boreExists = Get-Command bore -ErrorAction SilentlyContinue

if (-not $boreExists) {
    Write-Host "[INSTALL] Instalando Bore via Cargo..." -ForegroundColor Cyan
    Write-Host "   Executando: cargo install bore-cli" -ForegroundColor Gray
    
    # Tentar instalar cargo se não tiver
    $cargoExists = Get-Command cargo -ErrorAction SilentlyContinue
    if (-not $cargoExists) {
        Write-Host "[INSTALL] Instalando Rust (Cargo)..." -ForegroundColor Cyan
        winget install Rustlang.Rustup --force
        
        Write-Host "[INFO] Por favor, reinicie o PowerShell e execute novamente este script" -ForegroundColor Yellow
        Read-Host "Pressione Enter para sair"
        exit 1
    }
    
    cargo install bore-cli
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Falha ao instalar Bore" -ForegroundColor Red
        Write-Host "[INFO] Alternativa: Baixe manualmente de https://github.com/ekzhang/bore/releases" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host "[OK] Bore instalado" -ForegroundColor Green
Write-Host ""

# Criar diretório temporário para armazenar URLs
$tempDir = "$PSScriptRoot\.bore"
if (-not (Test-Path $tempDir)) {
    New-Item -ItemType Directory -Path $tempDir | Out-Null
}

# Arquivo para armazenar URLs
$urlFile = "$tempDir\urls.json"

Write-Host "[CONFIG] Configurando Bore para acesso global..." -ForegroundColor Cyan
Write-Host ""

# Portas aleatórias para evitar conflitos
$backendRemotePort = Get-Random -Minimum 10000 -Maximum 60000
$frontendRemotePort = Get-Random -Minimum 10000 -Maximum 60000

# Iniciar Bore para backend
Write-Host "[SETUP] Iniciando Bore para Backend (porta local 8000 -> remota $backendRemotePort)..." -ForegroundColor Cyan
$backendProcess = Start-Process -FilePath "bore" -ArgumentList "local 8000 --to bore.pub --port $backendRemotePort" -PassThru -WindowStyle Normal

Start-Sleep -Seconds 3

# Iniciar Bore para frontend
Write-Host "[SETUP] Iniciando Bore para Frontend (porta local 3000 -> remota $frontendRemotePort)..." -ForegroundColor Cyan
$frontendProcess = Start-Process -FilePath "bore" -ArgumentList "local 3000 --to bore.pub --port $frontendRemotePort" -PassThru -WindowStyle Normal

Start-Sleep -Seconds 5

# URLs geradas
$backendUrl = "http://bore.pub:$backendRemotePort"
$frontendUrl = "http://bore.pub:$frontendRemotePort"

Write-Host ""
Write-Host "[OK] Bore iniciado com sucesso!" -ForegroundColor Green
Write-Host ""
Write-Host "[URLS] URLs Publicas Globais:" -ForegroundColor Cyan
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
    backendRemotePort = $backendRemotePort
    frontendRemotePort = $frontendRemotePort
}

$urlData | ConvertTo-Json | Set-Content -Path $urlFile

Write-Host "[SAVE] URLs salvas em: $urlFile" -ForegroundColor Yellow
Write-Host ""

# Atualizar variáveis de ambiente
Write-Host "[CONFIG] Configurando variaveis de ambiente..." -ForegroundColor Cyan

# Backend .env
$backendEnvFile = "$PSScriptRoot\backend\.env.docker"
$backendEnvContent = Get-Content $backendEnvFile -Raw

# Atualizar CORS_ORIGINS para permitir bore.pub
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

# Bore usa HTTP, ajustar cookies
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

# Reiniciar containers para aplicar novas configurações
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
Write-Host "[SHARE] URLs para compartilhar GLOBALMENTE:" -ForegroundColor Cyan
Write-Host ""
Write-Host "   🌍 Aplicacao: $frontendUrl" -ForegroundColor White
Write-Host "   🔌 API:       $backendUrl" -ForegroundColor White
Write-Host ""
Write-Host "[LOGIN] Credenciais de acesso:" -ForegroundColor Yellow
Write-Host "   Email: admin@hotelreal.com.br" -ForegroundColor White
Write-Host "   Senha: admin123" -ForegroundColor White
Write-Host ""
Write-Host "[IMPORTANTE] Instrucoes:" -ForegroundColor Yellow
Write-Host "   - Funciona de QUALQUER lugar do mundo" -ForegroundColor Gray
Write-Host "   - Sem limites de bandwidth" -ForegroundColor Gray
Write-Host "   - Usa HTTP (nao HTTPS)" -ForegroundColor Gray
Write-Host "   - URLs estaveis enquanto script rodar" -ForegroundColor Gray
Write-Host ""
Write-Host "[TEST] Para testar:" -ForegroundColor Cyan
Write-Host "   1. No seu PC: $frontendUrl" -ForegroundColor Gray
Write-Host "   2. No celular (4G/5G): $frontendUrl" -ForegroundColor Gray
Write-Host "   3. Em qualquer lugar: $frontendUrl" -ForegroundColor Gray
Write-Host ""
Write-Host "[MONITOR] Para monitorar:" -ForegroundColor Cyan
Write-Host "   docker-compose logs -f backend" -ForegroundColor Gray
Write-Host "   docker-compose logs -f frontend" -ForegroundColor Gray
Write-Host ""
Write-Host "[STOP] Para parar:" -ForegroundColor Red
Write-Host "   Pressione Ctrl+C nesta janela" -ForegroundColor Gray
Write-Host ""

# Manter script rodando
Write-Host "[RUNNING] Bore ativo. Pressione Ctrl+C para parar..." -ForegroundColor Yellow
Write-Host ""

# Loop infinito até Ctrl+C
try {
    while ($true) {
        Start-Sleep -Seconds 5
        
        # Verificar se processos ainda estão rodando
        if ($backendProcess.HasExited -or $frontendProcess.HasExited) {
            Write-Host ""
            Write-Host "[WARN] Um ou mais tunnels pararam. Reiniciando..." -ForegroundColor Yellow
            
            if ($backendProcess.HasExited) {
                $backendProcess = Start-Process -FilePath "bore" -ArgumentList "local 8000 --to bore.pub --port $backendRemotePort" -PassThru -WindowStyle Normal
            }
            
            if ($frontendProcess.HasExited) {
                $frontendProcess = Start-Process -FilePath "bore" -ArgumentList "local 3000 --to bore.pub --port $frontendRemotePort" -PassThru -WindowStyle Normal
            }
        }
    }
} finally {
    Write-Host ""
    Write-Host "[STOP] Parando Bore..." -ForegroundColor Red
    
    # Matar processos
    if (-not $backendProcess.HasExited) {
        Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
    }
    
    if (-not $frontendProcess.HasExited) {
        Stop-Process -Id $frontendProcess.Id -Force -ErrorAction SilentlyContinue
    }
    
    # Matar todos os processos bore
    Get-Process | Where-Object { $_.ProcessName -like "*bore*" } | Stop-Process -Force -ErrorAction SilentlyContinue
    
    Write-Host "[OK] Bore parado" -ForegroundColor Green
    Write-Host ""
    Write-Host "[INFO] Para restaurar configuracao local:" -ForegroundColor Cyan
    Write-Host "   .\RESTAURAR_CONFIG_LOCAL.ps1" -ForegroundColor Gray
}
