# Script para iniciar o Frontend
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "Iniciando Frontend Next.js..." -ForegroundColor Green
Write-Host ""

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$frontendPath = Join-Path $scriptPath "frontend"

Set-Location $frontendPath

if (-not (Test-Path "node_modules")) {
    Write-Host "Instalando dependencias..." -ForegroundColor Yellow
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERRO: Erro ao instalar dependencias" -ForegroundColor Red
        exit 1
    }
}

Write-Host "OK: Dependencias instaladas" -ForegroundColor Green
Write-Host "Iniciando servidor em http://localhost:3000" -ForegroundColor Cyan
Write-Host ""

npm run dev

