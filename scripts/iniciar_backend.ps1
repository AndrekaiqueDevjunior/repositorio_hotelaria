# Script para iniciar o Backend
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "Iniciando Backend FastAPI..." -ForegroundColor Green
Write-Host ""

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendPath = Join-Path $scriptPath "backend"
$venvPath = Join-Path $backendPath "venv312\Scripts\Activate.ps1"

if (-not (Test-Path $venvPath)) {
    Write-Host "ERRO: Ambiente virtual nao encontrado em: $venvPath" -ForegroundColor Red
    Write-Host "   Execute: cd backend && python -m venv venv312" -ForegroundColor Yellow
    exit 1
}

Set-Location $backendPath
& $venvPath

Write-Host "OK: Ambiente virtual ativado" -ForegroundColor Green
Write-Host "Iniciando servidor em http://localhost:8000" -ForegroundColor Cyan
Write-Host "Documentacao: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

