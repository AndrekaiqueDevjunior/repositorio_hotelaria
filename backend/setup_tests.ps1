# Script PowerShell para configurar e executar testes
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Configuração de Testes - Hotel Cabo Frio" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar se Prisma está instalado
Write-Host "1. Verificando Prisma..." -ForegroundColor Yellow
try {
    $prismaVersion = npx prisma --version 2>&1
    Write-Host "   Prisma encontrado: $prismaVersion" -ForegroundColor Green
} catch {
    Write-Host "   Prisma não encontrado. Instalando..." -ForegroundColor Yellow
    npm install -g prisma
}

# Gerar cliente Prisma
Write-Host ""
Write-Host "2. Gerando cliente Prisma..." -ForegroundColor Yellow
try {
    npx prisma generate
    Write-Host "   Cliente Prisma gerado com sucesso!" -ForegroundColor Green
} catch {
    Write-Host "   Erro ao gerar cliente Prisma. Verifique se o schema.prisma existe." -ForegroundColor Red
    exit 1
}

# Verificar dependências Python
Write-Host ""
Write-Host "3. Verificando dependências Python..." -ForegroundColor Yellow
$pytestCheck = python -c "import pytest; print('OK')" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "   pytest instalado" -ForegroundColor Green
} else {
    Write-Host "   Instalando pytest..." -ForegroundColor Yellow
    pip install pytest pytest-asyncio
}

# Testar import do Prisma
Write-Host ""
Write-Host "4. Testando import do Prisma..." -ForegroundColor Yellow
$prismaTest = python -c "from prisma import Prisma; print('OK')" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "   Prisma import funcionando!" -ForegroundColor Green
} else {
    Write-Host "   ERRO: Prisma não pode ser importado!" -ForegroundColor Red
    Write-Host "   Execute: npx prisma generate" -ForegroundColor Yellow
    exit 1
}

# Executar testes
Write-Host ""
Write-Host "5. Executando testes..." -ForegroundColor Yellow
Write-Host ""
python -m pytest tests/ -v

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Todos os testes passaram!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "Alguns testes falharam." -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
}

