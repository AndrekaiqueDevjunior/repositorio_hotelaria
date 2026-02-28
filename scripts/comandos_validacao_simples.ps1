# ============================================================
# COMANDOS SIMPLES - Validacao Prisma Remoto
# ============================================================
# Comandos basicos para validar configuracao do banco remoto
# Sem emojis - compativel com PowerShell Windows
# ============================================================

Write-Host "[COMANDOS] Validacao Prisma Data Platform" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Gray

Write-Host "`n[1] DIAGNOSTICO RAPIDO" -ForegroundColor Yellow
Write-Host "Executar: .\diagnostico_database_url.ps1" -ForegroundColor White

Write-Host "`n[2] VALIDACAO COMPLETA" -ForegroundColor Yellow  
Write-Host "Executar: .\validar_configuracao_prisma.ps1" -ForegroundColor White

Write-Host "`n[3] VALIDACAO COM DETALHES" -ForegroundColor Yellow
Write-Host "Executar: .\validar_configuracao_prisma.ps1 -Verbose" -ForegroundColor White

Write-Host "`n[4] PULAR TESTE BACKEND" -ForegroundColor Yellow
Write-Host "Executar: .\validar_configuracao_prisma.ps1 -SkipBackendTest" -ForegroundColor White

Write-Host "`n[5] REINICIAR CONTAINERS" -ForegroundColor Yellow
Write-Host "Executar: docker-compose down" -ForegroundColor White
Write-Host "Executar: docker-compose up -d" -ForegroundColor White

Write-Host "`n[6] VER LOGS BACKEND" -ForegroundColor Yellow
Write-Host "Executar: docker-compose logs backend" -ForegroundColor White

Write-Host "`n[7] TESTAR ENDPOINT DEBUG" -ForegroundColor Yellow
Write-Host "Executar: curl http://localhost:8000/api/v1/debug/prisma" -ForegroundColor White

Write-Host "`n[8] VALIDACAO PYTHON DIRETA" -ForegroundColor Yellow
Write-Host "Executar: cd backend" -ForegroundColor White
Write-Host "Executar: python validar_prisma_remoto.py" -ForegroundColor White

Write-Host "`n[INFO] Todos os scripts foram corrigidos para remover emojis" -ForegroundColor Green
Write-Host "[INFO] Agora sao compativeis com PowerShell Windows" -ForegroundColor Green

Write-Host "`n============================================================" -ForegroundColor Gray
