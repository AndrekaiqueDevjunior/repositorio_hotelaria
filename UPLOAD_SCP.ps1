# Script de Upload para VPS via SCP
# Execute este script no PowerShell

$VPS_HOST = "root@72.61.27.152"
$VPS_PATH = "/opt/hotel"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Upload para VPS via SCP" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Criar diretórios na VPS
Write-Host "[1/9] Criando estrutura de diretórios na VPS..." -ForegroundColor Yellow
ssh $VPS_HOST "mkdir -p $VPS_PATH/backup $VPS_PATH/uploads $VPS_PATH/nginx/conf.d"

# 2. Upload docker-compose.production.yml
Write-Host "[2/9] Enviando docker-compose.production.yml..." -ForegroundColor Yellow
scp docker-compose.production.yml ${VPS_HOST}:${VPS_PATH}/

# 3. Upload .env.production.example
Write-Host "[3/9] Enviando .env.production.example..." -ForegroundColor Yellow
scp .env.production.example ${VPS_HOST}:${VPS_PATH}/

# 4. Upload scripts (apenas backup.sh)
Write-Host "[4/9] Enviando scripts..." -ForegroundColor Yellow
scp scripts/backup.sh ${VPS_HOST}:${VPS_PATH}/scripts/

# 5. Upload nginx
Write-Host "[5/9] Enviando configurações Nginx..." -ForegroundColor Yellow
scp -r nginx/ ${VPS_HOST}:${VPS_PATH}/

# 6. Upload backend
Write-Host "[6/9] Enviando Backend (isso pode demorar)..." -ForegroundColor Yellow
scp -r backend/ ${VPS_HOST}:${VPS_PATH}/

# 7. Upload frontend
Write-Host "[7/9] Enviando Frontend (isso pode demorar)..." -ForegroundColor Yellow
scp -r frontend/ ${VPS_HOST}:${VPS_PATH}/

# 8. Upload documentação
Write-Host "[8/9] Enviando documentação..." -ForegroundColor Yellow
scp DEPLOY_VPS.md ${VPS_HOST}:${VPS_PATH}/
scp CHECKLIST_PRODUCAO.md ${VPS_HOST}:${VPS_PATH}/

# 9. Verificar upload
Write-Host "[9/9] Verificando arquivos enviados..." -ForegroundColor Yellow
ssh $VPS_HOST "ls -la $VPS_PATH/"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Upload Concluído!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Próximos passos na VPS:" -ForegroundColor Cyan
Write-Host "1. ssh $VPS_HOST" -ForegroundColor White
Write-Host "2. cd $VPS_PATH" -ForegroundColor White
Write-Host "3. cp .env.production.example .env.production" -ForegroundColor White
Write-Host "4. nano .env.production  # Configure as variáveis" -ForegroundColor White
Write-Host "5. docker-compose -f docker-compose.production.yml up -d" -ForegroundColor White
Write-Host ""
