# ============================================================
# Script para Executar Testes de Frontend (Playwright)
# ============================================================

Write-Host "[INFO] Iniciando testes de frontend via navegador..." -ForegroundColor Cyan

# Verificar se containers estao rodando
Write-Host "[INFO] Verificando containers Docker..." -ForegroundColor Yellow
$containers = docker-compose ps --services --filter "status=running"

if (-not $containers -or $containers.Count -eq 0) {
    Write-Host "[ERRO] Containers nao estao rodando. Execute: docker-compose up -d" -ForegroundColor Red
    exit 1
}

Write-Host "[OK] Containers rodando" -ForegroundColor Green

# Aguardar frontend estar pronto
Write-Host "[INFO] Aguardando frontend estar pronto..." -ForegroundColor Yellow
$maxAttempts = 30
$attempt = 0
$frontendReady = $false

while ($attempt -lt $maxAttempts) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8080" -Method GET -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            $frontendReady = $true
            break
        }
    } catch {
        # Ignorar erros e tentar novamente
    }
    
    $attempt++
    Start-Sleep -Seconds 2
    Write-Host "  Tentativa $attempt/$maxAttempts..." -ForegroundColor Gray
}

if (-not $frontendReady) {
    Write-Host "[AVISO] Frontend pode nao estar pronto. Tentando executar testes mesmo assim..." -ForegroundColor Yellow
}

Write-Host "[OK] Frontend pronto" -ForegroundColor Green

# Verificar se Playwright esta instalado
Write-Host "[INFO] Verificando Playwright..." -ForegroundColor Yellow
try {
    $playwrightVersion = npx playwright --version 2>$null
    Write-Host "[OK] Playwright encontrado: $playwrightVersion" -ForegroundColor Green
} catch {
    Write-Host "[INFO] Instalando Playwright..." -ForegroundColor Yellow
    docker-compose exec -T frontend npm install @playwright/test
    docker-compose exec -T frontend npx playwright install
}

# Executar testes
Write-Host ""
Write-Host "[INFO] Executando testes de frontend..." -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Opcoes de execucao
$testMode = $args[0]

switch ($testMode) {
    "auth" {
        Write-Host "[INFO] Executando apenas testes de autenticacao..." -ForegroundColor Yellow
        docker-compose exec -T frontend npx playwright tests/auth.spec.js --reporter=line
    }
    "clientes" {
        Write-Host "[INFO] Executando apenas testes de clientes..." -ForegroundColor Yellow
        docker-compose exec -T frontend npx playwright tests/clientes.spec.js --reporter=line
    }
    "reservas" {
        Write-Host "[INFO] Executando apenas testes de reservas..." -ForegroundColor Yellow
        docker-compose exec -T frontend npx playwright tests/reservas.spec.js --reporter=line
    }
    "pagamentos" {
        Write-Host "[INFO] Executando apenas testes de pagamentos..." -ForegroundColor Yellow
        docker-compose exec -T frontend npx playwright tests/pagamentos.spec.js --reporter=line
    }
    "pontos" {
        Write-Host "[INFO] Executando apenas testes de pontos..." -ForegroundColor Yellow
        docker-compose exec -T frontend npx playwright tests/pontos.spec.js --reporter=line
    }
    "dashboard" {
        Write-Host "[INFO] Executando apenas testes de dashboard..." -ForegroundColor Yellow
        docker-compose exec -T frontend npx playwright tests/dashboard.spec.js --reporter=line
    }
    "fluxo" {
        Write-Host "[INFO] Executando fluxo completo..." -ForegroundColor Yellow
        docker-compose exec -T frontend npx playwright tests/fluxo-completo.spec.js --reporter=line
    }
    default {
        Write-Host "[INFO] Executando todos os testes..." -ForegroundColor Yellow
        docker-compose exec -T frontend npx playwright tests/ --reporter=line
    }
}

$exitCode = $LASTEXITCODE

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan

if ($exitCode -eq 0) {
    Write-Host "[OK] Testes de frontend concluidos com sucesso!" -ForegroundColor Green
} else {
    Write-Host "[ERRO] Alguns testes de frontend falharam. Codigo de saida: $exitCode" -ForegroundColor Red
}

# Gerar relatorio HTML
Write-Host ""
Write-Host "[INFO] Gerando relatorio HTML..." -ForegroundColor Yellow
docker-compose exec -T frontend npx playwright show-report

Write-Host ""
Write-Host "[INFO] Relatorios disponíveis em:" -ForegroundColor Cyan
Write-Host "  - frontend/playwright-report/index.html" -ForegroundColor White
Write-Host "  - frontend/test-results/" -ForegroundColor White

exit $exitCode
