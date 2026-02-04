# ============================================================
# Obter Senha do LocalTunnel
# ============================================================

Write-Host "[INFO] Verificando se há túneis ativos..." -ForegroundColor Green

# Parar túneis existentes
Get-Process | Where-Object {$_.ProcessName -like "*node*"} | Stop-Process -Force -ErrorAction SilentlyContinue

Write-Host "[INFO] Iniciando novo túnel para capturar senha..." -ForegroundColor Yellow

# Gerar subdomínio único
$timestamp = Get-Date -Format "yyyyMMddHHmm"
$subdomain = "hotel-cabo-frio-$timestamp"

Write-Host "[INFO] Subdomínio: $subdomain" -ForegroundColor Cyan
Write-Host "[INFO] URL será: https://$subdomain.loca.lt" -ForegroundColor Cyan

# Iniciar LocalTunnel e capturar output
Write-Host "[TUNNEL] Iniciando LocalTunnel..." -ForegroundColor Yellow

# Criar um arquivo temporário para capturar o output
$tempFile = "$env:TEMP\localtunnel_output.txt"

# Iniciar o processo e capturar output
$process = Start-Process -FilePath "cmd" -ArgumentList "/c", "npx localtunnel --port 8080 --subdomain $subdomain 2>&1 | tee $tempFile" -PassThru -WindowStyle Normal

Write-Host "[WAIT] Aguardando túnel iniciar (15 segundos)..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# Ler o output para encontrar a senha
if (Test-Path $tempFile) {
    $output = Get-Content $tempFile -Raw
    Write-Host "[DEBUG] Output capturado:" -ForegroundColor Gray
    Write-Host $output -ForegroundColor Gray
    
    # Procurar por senha no output
    if ($output -match "password[:\s]+([^\s\n]+)") {
        $senha = $matches[1]
        Write-Host ""
        Write-Host "[OK] SENHA ENCONTRADA!" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "URL:  https://$subdomain.loca.lt" -ForegroundColor White
        Write-Host "Senha: $senha" -ForegroundColor Yellow
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "[INFO] Use esta senha para acessar o sistema" -ForegroundColor Cyan
        Write-Host "[INFO] Login do sistema: admin@hotelreal.com.br / admin123" -ForegroundColor Cyan
        
        # Salvar senha
        Set-Content -Path ".LOCALTUNNEL_SENHA.txt" -Value $senha
        Set-Content -Path ".LOCALTUNNEL_URL_CURRENT.txt" -Value "https://$subdomain.loca.lt"
        
    } else {
        Write-Host "[ERRO] Senha não encontrada no output" -ForegroundColor Red
        Write-Host "[INFO] Verifique a janela do LocalTunnel para a senha" -ForegroundColor Yellow
    }
} else {
    Write-Host "[ERRO] Arquivo de output não criado" -ForegroundColor Red
}

Write-Host "[INFO] Mantendo túnel ativo. Feche esta janela para parar." -ForegroundColor Yellow

# Manter processo rodando
try {
    while (-not $process.HasExited) {
        Start-Sleep -Seconds 5
    }
} finally {
    Write-Host "[STOP] Túnel parado" -ForegroundColor Red
    if (Test-Path $tempFile) {
        Remove-Item $tempFile -ErrorAction SilentlyContinue
    }
}
