#!/usr/bin/env pwsh

# ============================================================
# VERIFICAR CONFIGURAÇÃO NGROK DOMÍNIO FIXO
# ============================================================

Write-Host "[CHECK] Verificando configuração do Ngrok..." -ForegroundColor Green

# Verificar .env
$envFile = Get-Content -Path ".env" -Raw
if ($envFile -match "jacoby-unshifted-kylie\.ngrok-free\.dev") {
    Write-Host "[OK] .env configurado com domínio correto" -ForegroundColor Green
} else {
    Write-Host "[ERRO] .env não contém o domínio correto" -ForegroundColor Red
}

# Verificar arquivo de URL atual
if (Test-Path ".NGROK_URL_CURRENT.txt") {
    $urlAtual = Get-Content -Path ".NGROK_URL_CURRENT.txt"
    if ($urlAtual -eq "https://jacoby-unshifted-kylie.ngrok-free.dev") {
        Write-Host "[OK] Arquivo de URL atualizado" -ForegroundColor Green
    } else {
        Write-Host "[ERRO] Arquivo de URL atual incorreto: $urlAtual" -ForegroundColor Red
    }
} else {
    Write-Host "[ERRO] Arquivo .NGROK_URL_CURRENT.txt não encontrado" -ForegroundColor Red
}

# Verificar se ngrok está rodando
$ngrokProcess = Get-Process -Name "ngrok" -ErrorAction SilentlyContinue
if ($ngrokProcess) {
    Write-Host "[OK] Ngrok está rodando (PID: $($ngrokProcess.Id))" -ForegroundColor Green
} else {
    Write-Host "[WARN] Ngrok não está rodando" -ForegroundColor Yellow
}

# Verificar se proxy está rodando
$proxyProcess = Get-Process -Name "node" -ErrorAction SilentlyContinue | Where-Object {$_.MainWindowTitle -like "*proxy*" -or $_.CommandLine -like "*proxy-ngrok*"}
if ($proxyProcess) {
    Write-Host "[OK] Proxy reverso está rodando (PID: $($proxyProcess.Id))" -ForegroundColor Green
} else {
    Write-Host "[WARN] Proxy reverso não está rodando" -ForegroundColor Yellow
}

# Testar conexão HTTP
Write-Host "[TEST] Testando conexão com o domínio..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "https://jacoby-unshifted-kylie.ngrok-free.dev" -TimeoutSec 10 -Method Head
    if ($response.StatusCode -eq 200) {
        Write-Host "[OK] Domínio respondendo (Status: $($response.StatusCode))" -ForegroundColor Green
    } else {
        Write-Host "[WARN] Domínio respondeu com status: $($response.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "[ERRO] Falha ao conectar ao domínio: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "[RESUMO] Verificação concluída!" -ForegroundColor Cyan
Write-Host "[INFO] Domínio: https://jacoby-unshifted-kylie.ngrok-free.dev" -ForegroundColor Cyan
Write-Host "[INFO] Dashboard: http://localhost:4040" -ForegroundColor Cyan
