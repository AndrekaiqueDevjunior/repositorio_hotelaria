# ============================================================
# INICIAR NGROK E ATUALIZAR URL AUTOMATICAMENTE
# ============================================================

Write-Host "[INFO] Iniciando ngrok..." -ForegroundColor Green

# Parar ngrok existente
docker-compose stop ngrok

# Iniciar ngrok
docker-compose --profile ngrok up -d ngrok

# Aguardar ngrok iniciar
Write-Host "[INFO] Aguardando ngrok iniciar..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Atualizar URL automaticamente
Write-Host "[INFO] Atualizando URL..." -ForegroundColor Green
.\ATUALIZAR_NGROK_URL.ps1

# Exibir informacoes finais
Write-Host "[CONCLUIDO] Ngrok iniciado e URL atualizado!" -ForegroundColor Green
Write-Host "" -ForegroundColor White

$url = Get-Content ".NGROK_URL_CURRENT.txt" | Where-Object { $_ -match "https://.*\.ngrok-free\.dev" }

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "URL DE ACESSO AO SISTEMA:" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Frontend: $url" -ForegroundColor White
Write-Host "Backend API: $url/api/v1" -ForegroundColor White
Write-Host "Ngrok Dashboard: http://localhost:4040" -ForegroundColor White
Write-Host "================================================" -ForegroundColor Cyan
