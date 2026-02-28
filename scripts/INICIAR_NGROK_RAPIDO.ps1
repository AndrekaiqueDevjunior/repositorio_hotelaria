# ============================================================
# INICIALIZACAO RAPIDA - Sistema com ngrok
# ============================================================

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  HOTEL CABO FRIO - Inicializacao Rapida com ngrok" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Verificar se containers ja estao rodando
$running = docker ps --filter "name=app_hotel_cabo_frio" --format "{{.Names}}" 2>$null

if ($running) {
    Write-Host "[INFO] Containers ja estao rodando!" -ForegroundColor Green
    Write-Host ""
    
    # Capturar URL do ngrok
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels" -Method Get -ErrorAction Stop
        $ngrokUrl = $response.tunnels[0].public_url
        
        if ($ngrokUrl -match '^http://') {
            $ngrokUrl = $ngrokUrl -replace '^http://', 'https://'
        }
        
        Write-Host "============================================================" -ForegroundColor Green
        Write-Host "  SISTEMA JA ESTA ATIVO!" -ForegroundColor Green
        Write-Host "============================================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "Acesso ao sistema:" -ForegroundColor Cyan
        Write-Host "  - URL Publica: $ngrokUrl" -ForegroundColor White
        Write-Host "  - Dashboard:   http://localhost:4040" -ForegroundColor White
        Write-Host ""
        Write-Host "Credenciais:" -ForegroundColor Cyan
        Write-Host "  - Email: admin@hotelreal.com.br" -ForegroundColor White
        Write-Host "  - Senha: admin123" -ForegroundColor White
        Write-Host ""
        
    } catch {
        Write-Host "[AVISO] ngrok nao esta respondendo" -ForegroundColor Yellow
        Write-Host "  Reiniciando ngrok..." -ForegroundColor Gray
        docker restart app_hotel_cabo_frio-ngrok-1
        Start-Sleep -Seconds 5
        
        # Tentar novamente
        try {
            $response = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels" -Method Get -ErrorAction Stop
            $ngrokUrl = $response.tunnels[0].public_url
            
            if ($ngrokUrl -match '^http://') {
                $ngrokUrl = $ngrokUrl -replace '^http://', 'https://'
            }
            
            Write-Host "[OK] URL obtida: $ngrokUrl" -ForegroundColor Green
        } catch {
            Write-Host "[ERRO] Nao foi possivel obter URL do ngrok" -ForegroundColor Red
        }
    }
    
} else {
    Write-Host "[INFO] Containers nao estao rodando. Iniciando..." -ForegroundColor Yellow
    Write-Host ""
    
    # Iniciar containers
    docker start app_hotel_cabo_frio-redis-1 app_hotel_cabo_frio-postgres-1 2>$null
    Start-Sleep -Seconds 10
    
    docker start app_hotel_cabo_frio-backend-1 2>$null
    Start-Sleep -Seconds 5
    
    docker start app_hotel_cabo_frio-frontend-1 app_hotel_cabo_frio-nginx-proxy-1 app_hotel_cabo_frio-ngrok-1 2>$null
    Start-Sleep -Seconds 10
    
    Write-Host "[OK] Containers iniciados!" -ForegroundColor Green
    Write-Host ""
    
    # Capturar URL
    $maxRetries = 10
    $retryCount = 0
    $ngrokUrl = $null
    
    while ($retryCount -lt $maxRetries -and $null -eq $ngrokUrl) {
        try {
            $response = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels" -Method Get -ErrorAction Stop
            
            if ($response.tunnels -and $response.tunnels.Count -gt 0) {
                $ngrokUrl = $response.tunnels[0].public_url
                
                if ($ngrokUrl -match '^http://') {
                    $ngrokUrl = $ngrokUrl -replace '^http://', 'https://'
                }
            }
        } catch {
            $retryCount++
            Write-Host "  - Aguardando ngrok... ($retryCount/$maxRetries)" -ForegroundColor Gray
            Start-Sleep -Seconds 2
        }
    }
    
    if ($ngrokUrl) {
        Write-Host ""
        Write-Host "============================================================" -ForegroundColor Green
        Write-Host "  SISTEMA INICIADO COM SUCESSO!" -ForegroundColor Green
        Write-Host "============================================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "Acesso ao sistema:" -ForegroundColor Cyan
        Write-Host "  - URL Publica: $ngrokUrl" -ForegroundColor White
        Write-Host "  - Dashboard:   http://localhost:4040" -ForegroundColor White
        Write-Host ""
        Write-Host "Credenciais:" -ForegroundColor Cyan
        Write-Host "  - Email: admin@hotelreal.com.br" -ForegroundColor White
        Write-Host "  - Senha: admin123" -ForegroundColor White
        Write-Host ""
    } else {
        Write-Host "[ERRO] Nao foi possivel obter URL do ngrok" -ForegroundColor Red
    }
}

Write-Host "Para ver logs: docker-compose --profile ngrok logs -f" -ForegroundColor Gray
Write-Host "Para parar: docker-compose --profile ngrok down" -ForegroundColor Gray
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
