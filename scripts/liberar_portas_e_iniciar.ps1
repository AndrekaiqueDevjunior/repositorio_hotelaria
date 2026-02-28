# ============================================================
# Script: Liberar Portas e Iniciar Sistema
# ============================================================
# Para todas as portas em uso e inicia o sistema limpo
# ============================================================

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "        LIBERANDO PORTAS E INICIANDO SISTEMA                    " -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# Portas necessarias
$portas = @(3000, 8000, 5432, 6379, 4040)

Write-Host "[*] Parando containers Docker..." -ForegroundColor Cyan
docker-compose --profile ngrok --profile tools down 2>$null

Write-Host "[*] Verificando portas em uso..." -ForegroundColor Cyan

foreach ($porta in $portas) {
    $conexoes = netstat -ano | findstr ":$porta" | Where-Object { $_ -match "LISTENING" }
    
    if ($conexoes) {
        Write-Host "[*] Porta $porta em uso, liberando..." -ForegroundColor Yellow
        
        foreach ($linha in $conexoes) {
            if ($linha -match "\s+(\d+)\s*$") {
                $pid = $matches[1]
                
                try {
                    $processo = Get-Process -Id $pid -ErrorAction SilentlyContinue
                    if ($processo) {
                        Write-Host "    Matando processo: $($processo.ProcessName) (PID: $pid)" -ForegroundColor Yellow
                        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
                        Start-Sleep -Milliseconds 500
                    }
                }
                catch {
                    # Ignorar erros
                }
            }
        }
    }
}

Write-Host "[OK] Portas liberadas!" -ForegroundColor Green
Write-Host ""

# Aguardar para garantir que as portas foram liberadas
Write-Host "[*] Aguardando liberacao completa..." -ForegroundColor Cyan
Start-Sleep -Seconds 2

# Limpar containers órfãos
Write-Host "[*] Limpando containers orfaos..." -ForegroundColor Cyan
docker container prune -f 2>$null

Write-Host ""
Write-Host "================================================================" -ForegroundColor Green
Write-Host "        INICIANDO SISTEMA LIMPO                                 " -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Green
Write-Host ""

# Iniciar sistema
Write-Host "[*] Iniciando sistema..." -ForegroundColor Cyan
docker-compose --profile ngrok up -d --build

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "[OK] Sistema iniciado com sucesso!" -ForegroundColor Green
    Write-Host ""
    
    # Aguardar containers iniciarem
    Write-Host "[*] Aguardando containers iniciarem..." -ForegroundColor Cyan
    Start-Sleep -Seconds 10
    
    # Mostrar status
    Write-Host ""
    Write-Host "================================================================" -ForegroundColor Cyan
    Write-Host "        STATUS DOS CONTAINERS                                   " -ForegroundColor Cyan
    Write-Host "================================================================" -ForegroundColor Cyan
    Write-Host ""
    docker-compose ps
    
    Write-Host ""
    Write-Host "================================================================" -ForegroundColor Green
    Write-Host "        URLS DE ACESSO                                          " -ForegroundColor Green
    Write-Host "================================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Locais:" -ForegroundColor Cyan
    Write-Host "  Frontend:  http://localhost:3000" -ForegroundColor White
    Write-Host "  Backend:   http://localhost:8000" -ForegroundColor White
    Write-Host "  API Docs:  http://localhost:8000/docs" -ForegroundColor White
    Write-Host ""
    Write-Host "ngrok:" -ForegroundColor Cyan
    Write-Host "  Dashboard: http://localhost:4040" -ForegroundColor White
    Write-Host ""
    Write-Host "[*] Ver URLs publicas em: http://localhost:4040" -ForegroundColor Yellow
    Write-Host ""
}
else {
    Write-Host ""
    Write-Host "[ERRO] Erro ao iniciar sistema!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Ver logs:" -ForegroundColor Yellow
    Write-Host "  docker-compose logs" -ForegroundColor White
    Write-Host ""
}

Write-Host ""

