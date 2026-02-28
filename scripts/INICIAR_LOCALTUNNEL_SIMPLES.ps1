# ============================================================
# LocalTunnel Simples - Apenas para Nginx (porta 8080)
# ============================================================

Write-Host "[INFO] Iniciando LocalTunnel para porta 8080 (Nginx)..." -ForegroundColor Green

# Verificar se containers estão rodando
Write-Host "[INFO] Verificando containers Docker..." -ForegroundColor Yellow
$nginxStatus = docker-compose ps nginx | Select-String "Up"

if (-not $nginxStatus) {
    Write-Host "[ERRO] Container nginx não está rodando!" -ForegroundColor Red
    Write-Host "[INFO] Iniciando containers..." -ForegroundColor Yellow
    docker-compose up -d nginx
    Start-Sleep -Seconds 5
}

# Gerar subdomínio único
$timestamp = Get-Date -Format "yyyyMMddHHmm"
$subdomain = "hotel-cabo-frio-$timestamp"

Write-Host "[INFO] Subdomínio: $subdomain" -ForegroundColor Cyan
Write-Host "[INFO] URL será: https://$subdomain.loca.lt" -ForegroundColor Cyan

# Iniciar LocalTunnel
Write-Host "[TUNNEL] Iniciando LocalTunnel..." -ForegroundColor Yellow

try {
    # Iniciar em background
    $process = Start-Process -FilePath "npx" -ArgumentList "localtunnel --port 8080 --subdomain $subdomain" -PassThru -WindowStyle Normal
    
    Write-Host "[WAIT] Aguardando tunnel conectar (15 segundos)..." -ForegroundColor Yellow
    Start-Sleep -Seconds 15
    
    $url = "https://$subdomain.loca.lt"
    
    # Testar conexão
    Write-Host "[TEST] Testando conexão com $url..." -ForegroundColor Yellow
    try {
        $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "[OK] Tunnel respondendo!" -ForegroundColor Green
        } else {
            Write-Host "[WARN] Tunnel respondeu com status $($response.StatusCode)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "[WARN] Tunnel pode ainda estar iniciando: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    
    # Salvar URL
    Set-Content -Path ".LOCALTUNNEL_URL_CURRENT.txt" -Value $url
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "[OK] LocalTunnel iniciado com sucesso!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "[URL] Sistema disponível em:" -ForegroundColor Cyan
    Write-Host "   $url" -ForegroundColor White
    Write-Host ""
    Write-Host "[LOGIN] Credenciais:" -ForegroundColor Yellow
    Write-Host "   Email: admin@hotelreal.com.br" -ForegroundColor White
    Write-Host "   Senha: admin123" -ForegroundColor White
    Write-Host ""
    Write-Host "[IMPORTANTE] Instruções:" -ForegroundColor Yellow
    Write-Host "   - Se aparecer página de aviso, clique em 'Click to Continue'" -ForegroundColor Gray
    Write-Host "   - O sistema está configurado para aceitar LocalTunnel (.loca.lt)" -ForegroundColor Gray
    Write-Host "   - Cookies e autenticação funcionarão normalmente" -ForegroundColor Gray
    Write-Host ""
    Write-Host "[STOP] Para parar: Pressione Ctrl+C ou feche esta janela" -ForegroundColor Red
    Write-Host ""
    
    # Manter rodando
    Write-Host "[RUNNING] Tunnel ativo. Aguardando..." -ForegroundColor Yellow
    
    # Loop para manter processo ativo
    try {
        while ($true) {
            Start-Sleep -Seconds 10
            
            if ($process.HasExited) {
                Write-Host "[WARN] Tunnel parou. Reiniciando..." -ForegroundColor Yellow
                $process = Start-Process -FilePath "npx" -ArgumentList "localtunnel --port 8080 --subdomain $subdomain" -PassThru -WindowStyle Normal
                Start-Sleep -Seconds 10
            }
        }
    } finally {
        Write-Host "[STOP] Parando tunnel..." -ForegroundColor Red
        if (-not $process.HasExited) {
            Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
        }
        Write-Host "[OK] Tunnel parado" -ForegroundColor Green
    }
    
} catch {
    Write-Host "[ERRO] Falha ao iniciar LocalTunnel: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "[INFO] Verifique se Node.js e localtunnel estão instalados" -ForegroundColor Yellow
    Write-Host "[INFO] Instale com: npm install -g localtunnel" -ForegroundColor Yellow
}
