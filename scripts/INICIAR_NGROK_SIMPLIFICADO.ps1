#!/usr/bin/env pwsh

# ============================================================
# NGROK DOMÍNIO FIXO - VERSÃO SIMPLIFICADA
# Aponta ngrok local para nginx do Docker
# ============================================================

Write-Host "[NGROK] Iniciando com domínio fixo..." -ForegroundColor Green

# Garantir que o nginx está rodando
$nginxStatus = docker-compose ps nginx | Select-Object -Skip 1
if ($nginxStatus -notmatch "Up") {
    Write-Host "[ERROR] Nginx não está rodando. Iniciando..." -ForegroundColor Red
    docker-compose up -d nginx
    Start-Sleep -Seconds 5
}

# Testar se nginx está respondendo
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8080" -Method Head -TimeoutSec 5
    Write-Host "[OK] Nginx respondendo na porta 8080" -ForegroundColor Green
} catch {
    Write-Host "[WARN] Nginx não respondeu, mas continuando..." -ForegroundColor Yellow
}

# Iniciar ngrok com domínio fixo
Write-Host "[NGROK] Conectando ao domínio: jacoby-unshifted-kylie.ngrok-free.dev" -ForegroundColor Cyan
Start-Process -FilePath "ngrok" -ArgumentList "http", "--domain=jacoby-unshifted-kylie.ngrok-free.dev", "localhost:8080" -WindowStyle Normal

Write-Host "[INFO] Aguarde 10 segundos para o ngrok inicializar..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Verificar status
try {
    $response = Invoke-WebRequest -Uri "https://jacoby-unshifted-kylie.ngrok-free.dev" -Method Head -TimeoutSec 10
    Write-Host "[OK] Domínio respondendo!" -ForegroundColor Green
    Write-Host "[URL] https://jacoby-unshifted-kylie.ngrok-free.dev" -ForegroundColor Cyan
} catch {
    Write-Host "[WARN] Domínio ainda não respondeu. Verifique em instantes." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[RESUMO]" -ForegroundColor Cyan
Write-Host "[INFO] Sistema: https://jacoby-unshifted-kylie.ngrok-free.dev" -ForegroundColor White
Write-Host "[INFO] Dashboard: http://localhost:4040" -ForegroundColor White
Write-Host "[INFO] Local: http://localhost:8080" -ForegroundColor White
