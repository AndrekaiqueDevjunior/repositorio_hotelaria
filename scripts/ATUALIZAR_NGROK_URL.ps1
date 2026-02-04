# ============================================================
# ATUALIZAR URL NGROK AUTOMATICAMENTE
# ============================================================

Write-Host "[INFO] Verificando URL atual do ngrok..." -ForegroundColor Green

# Obter URL atual do ngrok
$ngrokUrl = docker-compose logs ngrok | Select-String "url=https://.*\.ngrok-free\.dev" | Select-Object -Last 1

if ($ngrokUrl) {
    $url = $ngrokUrl -replace '.*url=(https://.*\.ngrok-free\.dev).*', '$1'
    Write-Host "[INFO] URL detectado: $url" -ForegroundColor Yellow
    
    # Atualizar arquivo .env
    $envFile = ".\.env"
    if (Test-Path $envFile) {
        $envContent = Get-Content $envFile
        $newEnvContent = $envContent | ForEach-Object {
            if ($_ -match "^NGROK_URL=") {
                "NGROK_URL=$url"
            } elseif ($_ -match "^NEXT_PUBLIC_NGROK_URL=") {
                "NEXT_PUBLIC_NGROK_URL=$url"
            } else {
                $_
            }
        }
        
        # Adicionar URLs se não existirem
        if ($newEnvContent -notmatch "^NGROK_URL=") {
            $newEnvContent += "NGROK_URL=$url"
        }
        if ($newEnvContent -notmatch "^NEXT_PUBLIC_NGROK_URL=") {
            $newEnvContent += "NEXT_PUBLIC_NGROK_URL=$url"
        }
        
        Set-Content -Path $envFile -Value $newEnvContent
        Write-Host "[OK] Arquivo .env atualizado" -ForegroundColor Green
    }
    
    # Criar arquivo de URL para referencia rapida
    Set-Content -Path ".NGROK_URL_CURRENT.txt" -Value $url
    Write-Host "[OK] URL salvo em .NGROK_URL_CURRENT.txt" -ForegroundColor Green
    
    Write-Host "[INFO] Use o URL: $url" -ForegroundColor Cyan
    Write-Host "[INFO] Frontend: $url" -ForegroundColor Cyan
    Write-Host "[INFO] Backend API: $url/api/v1" -ForegroundColor Cyan
    
} else {
    Write-Host "[ERRO] Nao foi possivel detectar URL do ngrok" -ForegroundColor Red
    Write-Host "[INFO] Verifique se o container ngrok esta rodando" -ForegroundColor Yellow
}
