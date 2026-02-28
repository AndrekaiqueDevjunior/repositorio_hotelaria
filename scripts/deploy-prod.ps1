# Script de deploy para produção (Windows PowerShell)

Write-Host ""
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "  Deploy Hotel Real Cabo Frio - Producao" -ForegroundColor Green
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""

# Verificar se está no diretório correto
if (-not (Test-Path "docker-compose.prod.yml")) {
    Write-Host "ERRO: Execute este script na raiz do projeto" -ForegroundColor Red
    exit 1
}

# Verificar se .env existe
if (-not (Test-Path "backend\.env")) {
    Write-Host "ERRO: backend\.env nao encontrado" -ForegroundColor Red
    Write-Host "   Copie: cp backend\env.production.example backend\.env" -ForegroundColor Yellow
    Write-Host "   E configure as credenciais Cielo" -ForegroundColor Yellow
    exit 1
}

# Verificar credenciais Cielo
Write-Host "Verificando configuracao Cielo..." -ForegroundColor Yellow
$envContent = Get-Content "backend\.env" -Raw
if ($envContent -match "seu-merchant-id-aqui") {
    Write-Host "AVISO: Credenciais Cielo nao configuradas!" -ForegroundColor Yellow
    Write-Host "   Edite backend\.env com suas credenciais reais" -ForegroundColor Yellow
    $response = Read-Host "Continuar mesmo assim? (s/N)"
    if ($response -ne "s" -and $response -ne "S") {
        exit 1
    }
}

# Pull das últimas imagens
Write-Host ""
Write-Host "Baixando imagens Docker..." -ForegroundColor Cyan
docker-compose -f docker-compose.prod.yml pull

# Build das imagens
Write-Host ""
Write-Host "Construindo imagens..." -ForegroundColor Cyan
docker-compose -f docker-compose.prod.yml build --no-cache

# Parar containers antigos
Write-Host ""
Write-Host "Parando containers antigos..." -ForegroundColor Yellow
docker-compose -f docker-compose.prod.yml down

# Aplicar migrações
Write-Host ""
Write-Host "Aplicando migracoes do banco..." -ForegroundColor Cyan
docker-compose -f docker-compose.prod.yml run --rm api npx prisma migrate deploy

# Iniciar serviços
Write-Host ""
Write-Host "Iniciando servicos..." -ForegroundColor Green
docker-compose -f docker-compose.prod.yml up -d

# Aguardar inicialização
Write-Host ""
Write-Host "Aguardando inicializacao..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Verificar saúde
Write-Host ""
Write-Host "Verificando saude dos servicos..." -ForegroundColor Cyan
docker-compose -f docker-compose.prod.yml ps

Write-Host ""
Write-Host "Health check API..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing
    Write-Host "OK: API respondendo!" -ForegroundColor Green
} catch {
    Write-Host "AVISO: API ainda inicializando" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "  Deploy concluido!" -ForegroundColor Green
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Verificar logs:" -ForegroundColor Yellow
Write-Host "   docker-compose -f docker-compose.prod.yml logs -f api" -ForegroundColor White
Write-Host ""
Write-Host "URLs:" -ForegroundColor Yellow
Write-Host "   API: http://localhost:8000" -ForegroundColor Cyan
Write-Host "   Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "   Health: http://localhost:8000/health" -ForegroundColor Cyan
Write-Host ""
Write-Host "Proximos passos:" -ForegroundColor Yellow
Write-Host "   1. Configure DNS apontando para este servidor" -ForegroundColor White
Write-Host "   2. Configure SSL com certbot" -ForegroundColor White
Write-Host "   3. Faca deploy do frontend" -ForegroundColor White
Write-Host "   4. Teste pagamento com cartao real (valor baixo)" -ForegroundColor White
Write-Host ""


