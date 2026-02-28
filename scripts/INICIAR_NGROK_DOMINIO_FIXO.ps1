#!/usr/bin/env pwsh

# ============================================================
# NGROK COM DOMÍNIO FIXO E PROXY REVERSO
# Domínio: jacoby-unshifted-kylie.ngrok-free.dev
# ============================================================

Write-Host "[CONFIG] Iniciando Ngrok com domínio fixo..." -ForegroundColor Green

# Atualizar .env com o novo domínio
$envContent = Get-Content -Path ".env" -Raw
$envContent = $envContent -replace "NGROK_URL=.*", "NGROK_URL=https://jacoby-unshifted-kylie.ngrok-free.dev"
$envContent = $envContent -replace "NEXT_PUBLIC_NGROK_URL=.*", "NEXT_PUBLIC_NGROK_URL=https://jacoby-unshifted-kylie.ngrok-free.dev"
Set-Content -Path ".env" -Value $envContent -NoNewline

# Atualizar arquivo de URL atual
Set-Content -Path ".NGROK_URL_CURRENT.txt" -Value "https://jacoby-unshifted-kylie.ngrok-free.dev" -NoNewline

Write-Host "[CONFIG] Domínio atualizado nos arquivos de configuração" -ForegroundColor Green

# Iniciar proxy reverso na porta 9000
Write-Host "[PROXY] Iniciando proxy reverso na porta 9000..." -ForegroundColor Yellow
Start-Process -FilePath "node" -ArgumentList "proxy-ngrok.js" -WindowStyle Hidden
Start-Sleep -Seconds 2

# Iniciar ngrok apontando para o proxy
Write-Host "[NGROK] Iniciando tunnel para proxy reverso..." -ForegroundColor Yellow
Start-Process -FilePath "ngrok" -ArgumentList "http", "--domain=jacoby-unshifted-kylie.ngrok-free.dev", "9000" -WindowStyle Normal

Write-Host "[OK] Sistema configurado!" -ForegroundColor Green
Write-Host "[INFO] Frontend: http://localhost:3000" -ForegroundColor Cyan
Write-Host "[INFO] Proxy: http://localhost:9000" -ForegroundColor Cyan  
Write-Host "[INFO] Ngrok: https://jacoby-unshifted-kylie.ngrok-free.dev" -ForegroundColor Cyan
Write-Host "[INFO] Dashboard Ngrok: http://localhost:4040" -ForegroundColor Cyan

Write-Host ""
Write-Host "[ATENCAO] Aguarde alguns segundos para o ngrok inicializar" -ForegroundColor Yellow
Write-Host "[ATENCAO] Depois acesse: https://jacoby-unshifted-kylie.ngrok-free.dev" -ForegroundColor Yellow
