# ============================================================
# Script para executar testes de integracao via Docker
# ============================================================

Write-Host "[INFO] Iniciando testes de integracao API..." -ForegroundColor Cyan

# Verificar se containers estao rodando
Write-Host "[INFO] Verificando containers Docker..." -ForegroundColor Yellow
$containers = docker-compose ps --services --filter "status=running"

if (-not $containers -or $containers.Count -eq 0) {
    Write-Host "[ERRO] Containers nao estao rodando. Execute: docker-compose up -d" -ForegroundColor Red
    exit 1
}

Write-Host "[OK] Containers rodando" -ForegroundColor Green

# Aguardar backend estar pronto
Write-Host "[INFO] Aguardando backend estar pronto..." -ForegroundColor Yellow
$maxAttempts = 30
$attempt = 0
$backendReady = $false

while ($attempt -lt $maxAttempts) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8080/api/v1/health" -Method GET -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            $backendReady = $true
            break
        }
    } catch {
        # Ignorar erros e tentar novamente
    }
    
    $attempt++
    Start-Sleep -Seconds 2
    Write-Host "  Tentativa $attempt/$maxAttempts..." -ForegroundColor Gray
}

if (-not $backendReady) {
    Write-Host "[AVISO] Backend pode nao estar pronto. Tentando executar testes mesmo assim..." -ForegroundColor Yellow
}

Write-Host "[OK] Backend pronto" -ForegroundColor Green

# Executar testes dentro do container backend
Write-Host "" 
Write-Host "[INFO] Executando testes de integracao..." -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

docker-compose exec -T backend pytest tests/test_integration_api.py -v --tb=short

$exitCode = $LASTEXITCODE

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan

if ($exitCode -eq 0) {
    Write-Host "[OK] Testes concluidos com sucesso!" -ForegroundColor Green
} else {
    Write-Host "[ERRO] Alguns testes falharam. Codigo de saida: $exitCode" -ForegroundColor Red
}

# Verificar se relatorio foi gerado
Write-Host ""
Write-Host "[INFO] Verificando relatorio..." -ForegroundColor Yellow

if (Test-Path "backend/test_report.md") {
    Write-Host "[OK] Relatorio gerado: backend/test_report.md" -ForegroundColor Green
    Write-Host ""
    Write-Host "Conteudo do relatorio:" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Get-Content "backend/test_report.md"
    Write-Host "============================================================" -ForegroundColor Cyan
} else {
    Write-Host "[AVISO] Relatorio nao encontrado" -ForegroundColor Yellow
}

exit $exitCode
