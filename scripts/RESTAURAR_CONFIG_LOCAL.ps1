# =========================================
# Restaurar Configuração Local
# =========================================
# Volta as configurações para desenvolvimento local

Write-Host "[RESTAURAR] Restaurando configuracao local..." -ForegroundColor Cyan
Write-Host ""

# Backend .env
$backendEnvFile = "$PSScriptRoot\backend\.env.docker"
Write-Host "[UPDATE] Atualizando backend\.env.docker..." -ForegroundColor Yellow

$backendEnvContent = Get-Content $backendEnvFile -Raw

# Restaurar CORS para localhost
$backendEnvContent = $backendEnvContent -replace "CORS_ORIGINS=.*", "CORS_ORIGINS=http://localhost:3000,http://localhost:8000"
$backendEnvContent = $backendEnvContent -replace "FRONTEND_URL=.*", "FRONTEND_URL=http://localhost:3000"

# Restaurar Cookie para localhost
$backendEnvContent = $backendEnvContent -replace "COOKIE_SECURE=.*", "COOKIE_SECURE=False"
$backendEnvContent = $backendEnvContent -replace "COOKIE_SAMESITE=.*", "COOKIE_SAMESITE=lax"
$backendEnvContent = $backendEnvContent -replace "COOKIE_DOMAIN=.*", "COOKIE_DOMAIN=.localhost"

Set-Content -Path $backendEnvFile -Value $backendEnvContent

# Frontend .env
$frontendEnvFile = "$PSScriptRoot\frontend\.env.local"
Write-Host "[UPDATE] Atualizando frontend\.env.local..." -ForegroundColor Yellow

$frontendEnvContent = "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1"
Set-Content -Path $frontendEnvFile -Value $frontendEnvContent

Write-Host ""
Write-Host "[OK] Configuracao local restaurada!" -ForegroundColor Green
Write-Host ""
Write-Host "[RESTART] Reiniciando containers..." -ForegroundColor Cyan
docker-compose restart backend frontend

Start-Sleep -Seconds 5

Write-Host ""
Write-Host "[OK] Sistema configurado para desenvolvimento local" -ForegroundColor Green
Write-Host ""
Write-Host "[ACESSO] Acesse: http://localhost:3000" -ForegroundColor Cyan
Write-Host ""
