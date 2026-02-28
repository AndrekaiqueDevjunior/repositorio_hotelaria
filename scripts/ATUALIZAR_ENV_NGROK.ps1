# Script para Atualizar .env com URLs do Ngrok e Reiniciar Containers
# Uso: .\ATUALIZAR_ENV_NGROK.ps1

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "ATUALIZACAO AUTOMATICA - NGROK + DOCKER" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# 1. Obter URLs do ngrok via API
Write-Host "[1] Obtendo URLs do ngrok..." -ForegroundColor Yellow

try {
    $tunnels = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels" -ErrorAction Stop
    
    if ($tunnels.tunnels.Count -eq 0) {
        Write-Host "[ERRO] Nenhum tunel ngrok ativo!" -ForegroundColor Red
        Write-Host "[INFO] Execute primeiro: .\INICIAR_NGROK_DUAL.ps1" -ForegroundColor Cyan
        exit 1
    }
    
    $backendUrl = ""
    $frontendUrl = ""
    
    foreach ($tunnel in $tunnels.tunnels) {
        $port = $tunnel.config.addr -replace ".*:", ""
        $url = $tunnel.public_url
        
        if ($port -eq "8000") {
            $backendUrl = $url
            Write-Host "[OK] Backend URL: $backendUrl" -ForegroundColor Green
        }
        elseif ($port -eq "3000") {
            $frontendUrl = $url
            Write-Host "[OK] Frontend URL: $frontendUrl" -ForegroundColor Green
        }
    }
    
    if (-not $backendUrl -or -not $frontendUrl) {
        Write-Host "[ERRO] URLs do ngrok nao encontradas completamente" -ForegroundColor Red
        Write-Host "[INFO] Backend: $backendUrl" -ForegroundColor Gray
        Write-Host "[INFO] Frontend: $frontendUrl" -ForegroundColor Gray
        exit 1
    }
    
} catch {
    Write-Host "[ERRO] Nao foi possivel conectar ao ngrok API" -ForegroundColor Red
    Write-Host "[INFO] Verifique se ngrok esta rodando: http://localhost:4040" -ForegroundColor Cyan
    exit 1
}

# 2. Atualizar .env do backend
Write-Host "`n[2] Atualizando backend/.env..." -ForegroundColor Yellow

$envPath = ".env"
$backupPath = ".env.backup.$(Get-Date -Format 'yyyyMMdd_HHmmss')"

if (Test-Path $envPath) {
    # Fazer backup
    Copy-Item $envPath $backupPath
    Write-Host "[INFO] Backup criado: $backupPath" -ForegroundColor Gray
    
    # Ler conteudo atual
    $envContent = Get-Content $envPath -Raw
    
    # Construir nova linha de CORS_ORIGINS
    $newCorsOrigins = "CORS_ORIGINS=http://localhost:3000,$frontendUrl,$backendUrl"
    
    # Atualizar CORS_ORIGINS
    if ($envContent -match "CORS_ORIGINS=.+") {
        $envContent = $envContent -replace "CORS_ORIGINS=.+", $newCorsOrigins
        Write-Host "[OK] CORS_ORIGINS atualizado" -ForegroundColor Green
    } else {
        $envContent += "`n$newCorsOrigins"
        Write-Host "[OK] CORS_ORIGINS adicionado" -ForegroundColor Green
    }
    
    # Atualizar COOKIE_SECURE
    if ($envContent -match "COOKIE_SECURE=.+") {
        $envContent = $envContent -replace "COOKIE_SECURE=.+", "COOKIE_SECURE=true"
    } else {
        $envContent += "`nCOOKIE_SECURE=true"
    }
    Write-Host "[OK] COOKIE_SECURE=true" -ForegroundColor Green
    
    # Atualizar COOKIE_SAMESITE
    if ($envContent -match "COOKIE_SAMESITE=.+") {
        $envContent = $envContent -replace "COOKIE_SAMESITE=.+", "COOKIE_SAMESITE=none"
    } else {
        $envContent += "`nCOOKIE_SAMESITE=none"
    }
    Write-Host "[OK] COOKIE_SAMESITE=none" -ForegroundColor Green
    
    # Atualizar COOKIE_DOMAIN (vazio)
    if ($envContent -match "COOKIE_DOMAIN=.+") {
        $envContent = $envContent -replace "COOKIE_DOMAIN=.+", "COOKIE_DOMAIN="
    } else {
        $envContent += "`nCOOKIE_DOMAIN="
    }
    Write-Host "[OK] COOKIE_DOMAIN= (vazio)" -ForegroundColor Green
    
    # Salvar arquivo
    $envContent | Set-Content $envPath -NoNewline
    Write-Host "[OK] Arquivo .env atualizado" -ForegroundColor Green
    
} else {
    Write-Host "[ERRO] Arquivo .env nao encontrado!" -ForegroundColor Red
    Write-Host "[INFO] Crie a partir de: .env.ngrok.example" -ForegroundColor Cyan
    exit 1
}

# 3. Atualizar frontend/.env.local
Write-Host "`n[3] Atualizando frontend/.env.local..." -ForegroundColor Yellow

$frontendEnvPath = "frontend/.env.local"
$frontendBackupPath = "frontend/.env.local.backup.$(Get-Date -Format 'yyyyMMdd_HHmmss')"

# Criar diretorio se nao existir
if (-not (Test-Path "frontend")) {
    Write-Host "[ERRO] Diretorio frontend/ nao encontrado!" -ForegroundColor Red
    exit 1
}

# Fazer backup se arquivo existir
if (Test-Path $frontendEnvPath) {
    Copy-Item $frontendEnvPath $frontendBackupPath
    Write-Host "[INFO] Backup criado: $frontendBackupPath" -ForegroundColor Gray
    $frontendEnvContent = Get-Content $frontendEnvPath -Raw
} else {
    $frontendEnvContent = ""
    Write-Host "[INFO] Criando novo arquivo .env.local" -ForegroundColor Gray
}

# Construir nova linha de NEXT_PUBLIC_API_URL
$newApiUrl = "NEXT_PUBLIC_API_URL=$backendUrl/api/v1"

# Atualizar ou adicionar
if ($frontendEnvContent -match "NEXT_PUBLIC_API_URL=.+") {
    $frontendEnvContent = $frontendEnvContent -replace "NEXT_PUBLIC_API_URL=.+", $newApiUrl
    Write-Host "[OK] NEXT_PUBLIC_API_URL atualizado" -ForegroundColor Green
} else {
    if ($frontendEnvContent) {
        $frontendEnvContent += "`n$newApiUrl"
    } else {
        $frontendEnvContent = $newApiUrl
    }
    Write-Host "[OK] NEXT_PUBLIC_API_URL adicionado" -ForegroundColor Green
}

# Salvar arquivo
$frontendEnvContent | Set-Content $frontendEnvPath -NoNewline
Write-Host "[OK] Arquivo frontend/.env.local atualizado" -ForegroundColor Green

# 4. Reiniciar containers Docker
Write-Host "`n[4] Reiniciando containers Docker..." -ForegroundColor Yellow

try {
    # Parar containers
    Write-Host "[INFO] Parando containers..." -ForegroundColor Gray
    docker-compose stop backend frontend 2>&1 | Out-Null
    
    Start-Sleep -Seconds 2
    
    # Iniciar containers
    Write-Host "[INFO] Iniciando containers..." -ForegroundColor Gray
    docker-compose up -d backend frontend 2>&1 | Out-Null
    
    Start-Sleep -Seconds 3
    
    Write-Host "[OK] Containers reiniciados" -ForegroundColor Green
    
} catch {
    Write-Host "[ERRO] Falha ao reiniciar containers: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 5. Verificar se servicos estao respondendo
Write-Host "`n[5] Verificando servicos..." -ForegroundColor Yellow

Start-Sleep -Seconds 5

$backendOk = Test-NetConnection -ComputerName localhost -Port 8000 -InformationLevel Quiet -WarningAction SilentlyContinue
$frontendOk = Test-NetConnection -ComputerName localhost -Port 3000 -InformationLevel Quiet -WarningAction SilentlyContinue

if ($backendOk) {
    Write-Host "[OK] Backend respondendo na porta 8000" -ForegroundColor Green
} else {
    Write-Host "[AVISO] Backend nao esta respondendo" -ForegroundColor Yellow
}

if ($frontendOk) {
    Write-Host "[OK] Frontend respondendo na porta 3000" -ForegroundColor Green
} else {
    Write-Host "[AVISO] Frontend nao esta respondendo" -ForegroundColor Yellow
}

# 6. Resumo final
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "CONFIGURACAO CONCLUIDA" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "URLs Ngrok Configuradas:" -ForegroundColor Yellow
Write-Host "  Frontend: $frontendUrl" -ForegroundColor White
Write-Host "  Backend:  $backendUrl" -ForegroundColor White

Write-Host "`nArquivos Atualizados:" -ForegroundColor Yellow
Write-Host "  .env -> CORS_ORIGINS, COOKIE_*" -ForegroundColor White
Write-Host "  frontend/.env.local -> NEXT_PUBLIC_API_URL" -ForegroundColor White

Write-Host "`nContainers Docker:" -ForegroundColor Yellow
Write-Host "  Backend:  $(if($backendOk){'RODANDO'}else{'VERIFICAR'})" -ForegroundColor $(if($backendOk){'Green'}else{'Yellow'})
Write-Host "  Frontend: $(if($frontendOk){'RODANDO'}else{'VERIFICAR'})" -ForegroundColor $(if($frontendOk){'Green'}else{'Yellow'})

Write-Host "`nProximo Passo:" -ForegroundColor Yellow
Write-Host "  Acesse: $frontendUrl" -ForegroundColor White
Write-Host "  Login: admin@hotelreal.com.br / admin123" -ForegroundColor Gray

Write-Host "`nBackups Criados:" -ForegroundColor Yellow
Write-Host "  $backupPath" -ForegroundColor Gray
Write-Host "  $frontendBackupPath" -ForegroundColor Gray

Write-Host "`n========================================`n" -ForegroundColor Cyan
