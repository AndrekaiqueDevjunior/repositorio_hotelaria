# Script de Upload Manual para VPS via SCP
# Execute cada comando individualmente e insira a senha quando solicitado

$VPS_HOST = "root@72.61.27.152"
$VPS_PATH = "/opt/hotel"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Comandos para Upload Manual" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Execute os comandos abaixo um por vez:" -ForegroundColor Yellow
Write-Host ""

Write-Host "# 1. Criar diretórios na VPS" -ForegroundColor Green
Write-Host "ssh $VPS_HOST `"mkdir -p $VPS_PATH/backup $VPS_PATH/uploads $VPS_PATH/nginx/conf.d $VPS_PATH/scripts`"" -ForegroundColor White
Write-Host ""

Write-Host "# 2. Upload docker-compose.production.yml" -ForegroundColor Green
Write-Host "scp docker-compose.production.yml ${VPS_HOST}:${VPS_PATH}/" -ForegroundColor White
Write-Host ""

Write-Host "# 3. Upload .env.production.example" -ForegroundColor Green
Write-Host "scp .env.production.example ${VPS_HOST}:${VPS_PATH}/" -ForegroundColor White
Write-Host ""

Write-Host "# 4. Upload script de backup" -ForegroundColor Green
Write-Host "scp scripts/backup.sh ${VPS_HOST}:${VPS_PATH}/scripts/" -ForegroundColor White
Write-Host ""

Write-Host "# 5. Upload nginx" -ForegroundColor Green
Write-Host "scp -r nginx ${VPS_HOST}:${VPS_PATH}/" -ForegroundColor White
Write-Host ""

Write-Host "# 6. Upload backend (DEMORA)" -ForegroundColor Green
Write-Host "scp -r backend ${VPS_HOST}:${VPS_PATH}/" -ForegroundColor White
Write-Host ""

Write-Host "# 7. Upload frontend (DEMORA)" -ForegroundColor Green
Write-Host "scp -r frontend ${VPS_HOST}:${VPS_PATH}/" -ForegroundColor White
Write-Host ""

Write-Host "# 8. Upload documentação" -ForegroundColor Green
Write-Host "scp DEPLOY_VPS.md CHECKLIST_PRODUCAO.md ${VPS_HOST}:${VPS_PATH}/" -ForegroundColor White
Write-Host ""

Write-Host "# 9. Verificar arquivos" -ForegroundColor Green
Write-Host "ssh $VPS_HOST `"ls -la $VPS_PATH/`"" -ForegroundColor White
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Dica: Use PSCP ou WinSCP para upload gráfico" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
