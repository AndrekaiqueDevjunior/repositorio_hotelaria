# ============================================================
# SCRIPT DE INICIALIZACAO COMPLETO - SISTEMA HOTEL CABO FRIO
# Com NGROK (Frontend + Backend em um unico link)
# ============================================================

Write-Host "[INFO] Iniciando Sistema Hotel Cabo Frio com ngrok..." -ForegroundColor Cyan
Write-Host ""

# ============================================================
# ETAPA 1: Limpar containers e volumes antigos
# ============================================================
Write-Host "[ETAPA 1/6] Limpando containers antigos..." -ForegroundColor Yellow

Write-Host "  - Parando todos os containers..." -ForegroundColor Gray
docker-compose --profile ngrok down --remove-orphans 2>$null
docker-compose down --remove-orphans 2>$null

Write-Host "  - Removendo containers orfaos manualmente..." -ForegroundColor Gray
docker ps -aq --filter "name=hotel-" | ForEach-Object { docker rm -f $_ 2>$null }
docker ps -aq --filter "name=app_hotel_cabo_frio-" | ForEach-Object { docker rm -f $_ 2>$null }

Write-Host "  - Limpando sistema Docker..." -ForegroundColor Gray
docker system prune -f 2>$null | Out-Null

Write-Host "[OK] Containers limpos" -ForegroundColor Green
Write-Host ""

# ============================================================
# ETAPA 2: Verificar arquivo .env
# ============================================================
Write-Host "[ETAPA 2/6] Verificando configuracao..." -ForegroundColor Yellow

if (-not (Test-Path ".env")) {
    Write-Host "[ERRO] Arquivo .env nao encontrado!" -ForegroundColor Red
    Write-Host "  Por favor, crie o arquivo .env antes de continuar." -ForegroundColor Red
    exit 1
}

# Ler NGROK_AUTHTOKEN do .env
$envContent = Get-Content .env -Raw
if ($envContent -match 'NGROK_AUTHTOKEN=([^\r\n]+)') {
    $ngrokToken = $matches[1]
    if ([string]::IsNullOrWhiteSpace($ngrokToken)) {
        Write-Host "[ERRO] NGROK_AUTHTOKEN esta vazio no .env!" -ForegroundColor Red
        Write-Host "  Obtenha seu token em: https://dashboard.ngrok.com/get-started/your-authtoken" -ForegroundColor Yellow
        exit 1
    }
    Write-Host "  - NGROK_AUTHTOKEN configurado: " -NoNewline -ForegroundColor Gray
    Write-Host "OK" -ForegroundColor Green
} else {
    Write-Host "[ERRO] NGROK_AUTHTOKEN nao encontrado no .env!" -ForegroundColor Red
    exit 1
}

Write-Host "[OK] Configuracao valida" -ForegroundColor Green
Write-Host ""

# ============================================================
# ETAPA 3: Iniciar containers com ngrok
# ============================================================
Write-Host "[ETAPA 3/6] Iniciando containers Docker..." -ForegroundColor Yellow

Write-Host "  - Subindo servicos: redis, backend, frontend, nginx-proxy, ngrok..." -ForegroundColor Gray
docker-compose --profile ngrok up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERRO] Falha ao iniciar containers!" -ForegroundColor Red
    exit 1
}

Write-Host "[OK] Containers iniciados" -ForegroundColor Green
Write-Host ""

# ============================================================
# ETAPA 4: Aguardar inicializacao dos servicos
# ============================================================
Write-Host "[ETAPA 4/6] Aguardando inicializacao dos servicos..." -ForegroundColor Yellow

Write-Host "  - Aguardando Redis..." -ForegroundColor Gray
Start-Sleep -Seconds 3

Write-Host "  - Aguardando Backend..." -ForegroundColor Gray
Start-Sleep -Seconds 5

Write-Host "  - Aguardando Frontend..." -ForegroundColor Gray
Start-Sleep -Seconds 5

Write-Host "  - Aguardando Nginx e ngrok..." -ForegroundColor Gray
Start-Sleep -Seconds 5

Write-Host "[OK] Servicos inicializados" -ForegroundColor Green
Write-Host ""

# ============================================================
# ETAPA 5: Capturar URL publica do ngrok
# ============================================================
Write-Host "[ETAPA 5/6] Capturando URL publica do ngrok..." -ForegroundColor Yellow

$maxRetries = 10
$retryCount = 0
$ngrokUrl = $null

while ($retryCount -lt $maxRetries -and $null -eq $ngrokUrl) {
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels" -Method Get -ErrorAction Stop
        
        if ($response.tunnels -and $response.tunnels.Count -gt 0) {
            $ngrokUrl = $response.tunnels[0].public_url
            
            # Garantir que seja HTTPS
            if ($ngrokUrl -match '^http://') {
                $ngrokUrl = $ngrokUrl -replace '^http://', 'https://'
            }
            
            Write-Host "  - URL capturada: $ngrokUrl" -ForegroundColor Green
        } else {
            throw "Nenhum tunel encontrado"
        }
    } catch {
        $retryCount++
        Write-Host "  - Tentativa $retryCount/$maxRetries..." -ForegroundColor Gray
        Start-Sleep -Seconds 2
    }
}

if ($null -eq $ngrokUrl) {
    Write-Host "[ERRO] Nao foi possivel obter a URL do ngrok!" -ForegroundColor Red
    Write-Host "  Verifique se o ngrok esta rodando corretamente." -ForegroundColor Yellow
    Write-Host "  Dashboard ngrok: http://localhost:4040" -ForegroundColor Yellow
    exit 1
}

Write-Host "[OK] URL publica obtida" -ForegroundColor Green
Write-Host ""

# ============================================================
# ETAPA 6: Atualizar .env com a URL do ngrok
# ============================================================
Write-Host "[ETAPA 6/6] Atualizando arquivo .env..." -ForegroundColor Yellow

# Ler conteudo atual do .env
$envContent = Get-Content .env -Raw

# Atualizar NEXT_PUBLIC_API_URL
if ($envContent -match 'NEXT_PUBLIC_API_URL=.*') {
    $envContent = $envContent -replace 'NEXT_PUBLIC_API_URL=.*', "NEXT_PUBLIC_API_URL=$ngrokUrl"
} else {
    $envContent += "`nNEXT_PUBLIC_API_URL=$ngrokUrl"
}

# Atualizar CORS_ORIGINS se necessario
if ($envContent -notmatch 'CORS_ORIGINS=\*') {
    Write-Host "  - Configurando CORS para aceitar qualquer origem..." -ForegroundColor Gray
    if ($envContent -match 'CORS_ORIGINS=.*') {
        $envContent = $envContent -replace 'CORS_ORIGINS=.*', 'CORS_ORIGINS=*'
    } else {
        $envContent += "`nCORS_ORIGINS=*"
    }
}

# Salvar .env atualizado
Set-Content -Path .env -Value $envContent -NoNewline

Write-Host "  - NEXT_PUBLIC_API_URL atualizado para: $ngrokUrl" -ForegroundColor Green
Write-Host "[OK] Arquivo .env atualizado" -ForegroundColor Green
Write-Host ""

# ============================================================
# Reiniciar frontend para aplicar nova configuracao
# ============================================================
Write-Host "[FINALIZACAO] Reiniciando frontend para aplicar configuracoes..." -ForegroundColor Yellow
docker-compose restart frontend

Write-Host "  - Aguardando frontend reiniciar..." -ForegroundColor Gray
Start-Sleep -Seconds 8

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  SISTEMA INICIADO COM SUCESSO!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Acesso ao sistema:" -ForegroundColor Cyan
Write-Host "  - URL Publica (ngrok): $ngrokUrl" -ForegroundColor White
Write-Host "  - Dashboard ngrok:     http://localhost:4040" -ForegroundColor White
Write-Host ""
Write-Host "Credenciais de acesso:" -ForegroundColor Cyan
Write-Host "  - Email: admin@hotelreal.com.br" -ForegroundColor White
Write-Host "  - Senha: admin123" -ForegroundColor White
Write-Host ""
Write-Host "Servicos disponiveis:" -ForegroundColor Cyan
Write-Host "  - Frontend:  $ngrokUrl" -ForegroundColor White
Write-Host "  - Backend:   $ngrokUrl/api/v1" -ForegroundColor White
Write-Host "  - Docs API:  $ngrokUrl/api/v1/docs" -ForegroundColor White
Write-Host "  - Health:    $ngrokUrl/health" -ForegroundColor White
Write-Host ""
Write-Host "IMPORTANTE:" -ForegroundColor Yellow
Write-Host "  - O link ngrok funciona de qualquer lugar da internet" -ForegroundColor Gray
Write-Host "  - Frontend e Backend estao no mesmo link (unificado)" -ForegroundColor Gray
Write-Host "  - O ngrok pode exibir uma tela de aviso, clique em 'Visit Site'" -ForegroundColor Gray
Write-Host ""
Write-Host "Para ver logs dos containers:" -ForegroundColor Cyan
Write-Host "  docker-compose --profile ngrok logs -f" -ForegroundColor White
Write-Host ""
Write-Host "Para parar o sistema:" -ForegroundColor Cyan
Write-Host "  docker-compose --profile ngrok down" -ForegroundColor White
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
