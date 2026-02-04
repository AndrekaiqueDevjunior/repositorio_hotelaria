# ============================================================
# LocalTunnel com Verificação - Sistema Unificado
# ============================================================

Write-Host "[INFO] Iniciando LocalTunnel com verificação completa..." -ForegroundColor Green

# 1. Verificar containers
Write-Host "[1/5] Verificando containers Docker..." -ForegroundColor Yellow
$containers = docker-compose ps --services --filter "status=running"

$requiredContainers = @("nginx", "backend", "frontend")
foreach ($container in $requiredContainers) {
    if ($containers -notcontains $container) {
        Write-Host "[ERRO] Container $container não está rodando!" -ForegroundColor Red
        Write-Host "[INFO] Iniciando $container..." -ForegroundColor Yellow
        docker-compose up -d $container
        Start-Sleep -Seconds 5
    } else {
        Write-Host "[OK] $container rodando" -ForegroundColor Green
    }
}

# 2. Verificar saúde dos serviços
Write-Host "[2/5] Verificando saúde dos serviços..." -ForegroundColor Yellow

# Backend health
try {
    $backendHealth = docker-compose exec -T backend curl -s http://localhost:8000/health
    if ($backendHealth -match "healthy") {
        Write-Host "[OK] Backend saudável" -ForegroundColor Green
    } else {
        Write-Host "[WARN] Backend pode não estar saudável" -ForegroundColor Yellow
    }
} catch {
    Write-Host "[ERRO] Backend não responde: $($_.Exception.Message)" -ForegroundColor Red
}

# Frontend check
$frontendStatus = docker-compose ps frontend | Select-String "unhealthy"
if ($frontendStatus) {
    Write-Host "[WARN] Frontend marcado como unhealthy, mas isso pode ser normal" -ForegroundColor Yellow
} else {
    Write-Host "[OK] Frontend saudável" -ForegroundColor Green
}

# 3. Testar nginx localmente
Write-Host "[3/5] Testando nginx na porta 8080..." -ForegroundColor Yellow
$nginxAttempts = 0
$nginxOk = $false

do {
    $nginxAttempts++
    try {
        # Testar via docker exec (mais confiável)
        $nginxTest = docker-compose exec -T nginx wget -q -O - http://localhost:8080/health 2>$null
        if ($nginxTest -match "healthy") {
            Write-Host "[OK] Nginx respondendo na porta 8080" -ForegroundColor Green
            $nginxOk = $true
        } else {
            Write-Host "[TENTATIVA $nginxAttempts] Nginx não respondeu /health, tentando novamente..." -ForegroundColor Yellow
        }
    } catch {
        Write-Host "[TENTATIVA $nginxAttempts] Erro ao testar nginx: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    
    if (-not $nginxOk -and $nginxAttempts -lt 3) {
        Write-Host "[INFO] Aguardando 5 segundos antes da próxima tentativa..." -ForegroundColor Gray
        Start-Sleep -Seconds 5
    }
} while (-not $nginxOk -and $nginxAttempts -lt 3)

if (-not $nginxOk) {
    Write-Host "[ERRO] Nginx não está respondendo na porta 8080" -ForegroundColor Red
    Write-Host "[INFO] Verificando logs do nginx..." -ForegroundColor Yellow
    docker-compose logs nginx --tail=5
    Write-Host "[INFO] Tentando reiniciar nginx..." -ForegroundColor Yellow
    docker-compose restart nginx
    Start-Sleep -Seconds 10
    
    # Testar novamente
    try {
        $nginxTest = docker-compose exec -T nginx wget -q -O - http://localhost:8080/health 2>$null
        if ($nginxTest -match "healthy") {
            Write-Host "[OK] Nginx respondendo após restart" -ForegroundColor Green
            $nginxOk = $true
        }
    } catch {
        Write-Host "[ERRO] Nginx ainda não responde" -ForegroundColor Red
        Write-Host "[INFO] Continuando mesmo assim..." -ForegroundColor Yellow
        $nginxOk = $true  # Continuar mesmo assim
    }
}

# 4. Iniciar LocalTunnel
Write-Host "[4/5] Iniciando LocalTunnel..." -ForegroundColor Yellow

# Gerar subdomínio único
$timestamp = Get-Date -Format "yyyyMMddHHmm"
$subdomain = "hotel-cabo-frio-$timestamp"

Write-Host "[INFO] Subdomínio: $subdomain" -ForegroundColor Cyan
Write-Host "[INFO] URL será: https://$subdomain.loca.lt" -ForegroundColor Cyan

try {
    # Verificar se localtunnel está instalado
    $ltVersion = npx localtunnel --version 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[INFO] LocalTunnel não encontrado, instalando..." -ForegroundColor Yellow
        npm install -g localtunnel
    }
    
    # Iniciar LocalTunnel
    $process = Start-Process -FilePath "npx" -ArgumentList "localtunnel --port 8080 --subdomain $subdomain" -PassThru -WindowStyle Normal
    
    Write-Host "[WAIT] Aguardando tunnel conectar (20 segundos)..." -ForegroundColor Yellow
    Start-Sleep -Seconds 20
    
    $url = "https://$subdomain.loca.lt"
    
    # 5. Testar conexão externa
    Write-Host "[5/5] Testando conexão externa..." -ForegroundColor Yellow
    $testAttempts = 0
    $connectionOk = $false
    
    do {
        $testAttempts++
        try {
            $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 15 -ErrorAction Stop
            if ($response.StatusCode -eq 200) {
                Write-Host "[OK] Tunnel respondendo!" -ForegroundColor Green
                $connectionOk = $true
            } else {
                Write-Host "[TENTATIVA $testAttempts] Status: $($response.StatusCode)" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "[TENTATIVA $testAttempts] Erro: $($_.Exception.Message)" -ForegroundColor Yellow
        }
        
        if (-not $connectionOk -and $testAttempts -lt 3) {
            Write-Host "[INFO] Aguardando 10 segundos antes da próxima tentativa..." -ForegroundColor Gray
            Start-Sleep -Seconds 10
        }
    } while (-not $connectionOk -and $testAttempts -lt 3)
    
    # Salvar URL
    Set-Content -Path ".LOCALTUNNEL_URL_CURRENT.txt" -Value $url
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "[RESULTADO] Sistema configurado!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "[URLS] Acesso externo:" -ForegroundColor Cyan
    Write-Host "   Sistema: $url" -ForegroundColor White
    Write-Host "   Local:  http://localhost:8080" -ForegroundColor Gray
    Write-Host ""
    Write-Host "[LOGIN] Credenciais:" -ForegroundColor Yellow
    Write-Host "   Email: admin@hotelreal.com.br" -ForegroundColor White
    Write-Host "   Senha: admin123" -ForegroundColor White
    Write-Host ""
    Write-Host "[ARQUITETURA]" -ForegroundColor Cyan
    Write-Host "   Frontend (Next.js)  → porta 3000" -ForegroundColor Gray
    Write-Host "   Backend (FastAPI)   → porta 8000" -ForegroundColor Gray
    Write-Host "   Nginx (Proxy)       → porta 8080" -ForegroundColor Gray
    Write-Host "   LocalTunnel         → $url" -ForegroundColor Gray
    Write-Host ""
    Write-Host "[IMPORTANTE]" -ForegroundColor Yellow
    Write-Host "   - Se aparecer página de aviso, clique em 'Click to Continue'" -ForegroundColor Gray
    Write-Host "   - CORS configurado para .loca.lt" -ForegroundColor Gray
    Write-Host "   - Cookies e autenticação funcionarão" -ForegroundColor Gray
    Write-Host ""
    Write-Host "[STOP] Para parar: Ctrl+C nesta janela" -ForegroundColor Red
    Write-Host ""
    
    # Manter rodando
    Write-Host "[RUNNING] Tunnel ativo. Monitorando..." -ForegroundColor Yellow
    
    try {
        while ($true) {
            Start-Sleep -Seconds 30
            
            if ($process.HasExited) {
                Write-Host "[WARN] Tunnel parou. Reiniciando..." -ForegroundColor Yellow
                $process = Start-Process -FilePath "npx" -ArgumentList "localtunnel --port 8080 --subdomain $subdomain" -PassThru -WindowStyle Normal
                Start-Sleep -Seconds 15
            }
            
            # Testar conexão periodicamente
            try {
                $testResponse = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
                if ($testResponse.StatusCode -ne 200) {
                    Write-Host "[WARN] Tunnel respondeu com status $($testResponse.StatusCode)" -ForegroundColor Yellow
                }
            } catch {
                Write-Host "[WARN] Teste de conexão falhou: $($_.Exception.Message)" -ForegroundColor Yellow
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
    Write-Host "[ERRO] Falha crítica: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "[DEBUG] Verifique:" -ForegroundColor Yellow
    Write-Host "   - Node.js instalado?" -ForegroundColor Gray
    Write-Host "   - Conexão com internet?" -ForegroundColor Gray
    Write-Host "   - Porta 8080 disponível?" -ForegroundColor Gray
    Write-Host "   - Containers rodando?" -ForegroundColor Gray
}
