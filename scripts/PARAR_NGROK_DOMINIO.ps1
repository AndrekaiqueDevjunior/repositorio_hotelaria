#!/usr/bin/env pwsh

# ============================================================
# PARAR NGROK E PROXY REVERSO
# ============================================================

Write-Host "[STOP] Parando processos Ngrok..." -ForegroundColor Red

# Parar ngrok
Get-Process -Name "ngrok" -ErrorAction SilentlyContinue | Stop-Process -Force
Write-Host "[STOP] Ngrok finalizado" -ForegroundColor Yellow

# Parar proxy (node)
Get-Process -Name "node" -ErrorAction SilentlyContinue | Where-Object {$_.MainWindowTitle -like "*proxy*" -or $_.CommandLine -like "*proxy-ngrok*"} | Stop-Process -Force
Write-Host "[STOP] Proxy reverso finalizado" -ForegroundColor Yellow

# Limpar arquivos temporários
if (Test-Path ".NGROK_URL_CURRENT.txt") {
    Clear-Content -Path ".NGROK_URL_CURRENT.txt"
    Write-Host "[CLEAN] Arquivo de URL atual limpo" -ForegroundColor Yellow
}

Write-Host "[OK] Todos os processos ngrok e proxy foram parados!" -ForegroundColor Green
