# ============================================================
# Script de Limpeza Completa do Docker
# Resolve: "Bind for 0.0.0.0:8000 failed", "No such container", 
#          "network has active endpoints"
# ============================================================

Write-Host "[INFO] Iniciando limpeza completa do Docker..." -ForegroundColor Cyan

# Passo 1: Parar TODOS os containers do projeto
Write-Host "`n[PASSO 1] Parando containers do projeto..." -ForegroundColor Yellow
docker-compose down 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Containers parados com sucesso" -ForegroundColor Green
} else {
    Write-Host "[AVISO] Alguns containers podem nao existir" -ForegroundColor Yellow
}

# Passo 2: Forçar remoção de containers órfãos
Write-Host "`n[PASSO 2] Removendo containers orfaos..." -ForegroundColor Yellow
docker ps -a --filter "name=app_hotel_cabo_frio" -q | ForEach-Object {
    Write-Host "Removendo container: $_" -ForegroundColor Gray
    docker rm -f $_ 2>$null
}
Write-Host "[OK] Containers orfaos removidos" -ForegroundColor Green

# Passo 3: Limpar rede com endpoints ativos
Write-Host "`n[PASSO 3] Limpando rede hotel_network..." -ForegroundColor Yellow
$networkExists = docker network ls --filter "name=hotel_network" -q
if ($networkExists) {
    Write-Host "Removendo rede hotel_network..." -ForegroundColor Gray
    docker network rm hotel_network 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Rede removida com sucesso" -ForegroundColor Green
    } else {
        Write-Host "[AVISO] Rede pode ter endpoints ativos, tentando remocao forcada..." -ForegroundColor Yellow
        
        # Desconectar todos os containers da rede
        $containers = docker network inspect hotel_network --format '{{range .Containers}}{{.Name}} {{end}}' 2>$null
        if ($containers) {
            $containers.Split() | ForEach-Object {
                if ($_ -ne "") {
                    Write-Host "Desconectando container $_ da rede..." -ForegroundColor Gray
                    docker network disconnect -f hotel_network $_ 2>$null
                }
            }
        }
        
        # Tentar remover novamente
        docker network rm hotel_network 2>$null
        Write-Host "[OK] Rede removida apos desconexao forcada" -ForegroundColor Green
    }
} else {
    Write-Host "[INFO] Rede hotel_network nao existe" -ForegroundColor Gray
}

# Passo 4: Validar portas livres no host
Write-Host "`n[PASSO 4] Validando portas no host..." -ForegroundColor Yellow
$portsToCheck = @(8080)  # Apenas nginx expõe porta agora

foreach ($port in $portsToCheck) {
    $connection = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($connection) {
        $processId = $connection.OwningProcess
        $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
        Write-Host "[AVISO] Porta $port em uso pelo processo: $($process.Name) (PID: $processId)" -ForegroundColor Yellow
        
        # Perguntar se deseja matar o processo
        $response = Read-Host "Deseja encerrar o processo na porta $port? (S/N)"
        if ($response -eq "S" -or $response -eq "s") {
            Stop-Process -Id $processId -Force
            Write-Host "[OK] Processo encerrado" -ForegroundColor Green
        }
    } else {
        Write-Host "[OK] Porta $port livre" -ForegroundColor Green
    }
}

# Passo 5: Limpar volumes órfãos (OPCIONAL - dados serão perdidos)
Write-Host "`n[PASSO 5] Limpar volumes? (dados serao perdidos)" -ForegroundColor Yellow
$response = Read-Host "Deseja remover volumes do Docker? (S/N)"
if ($response -eq "S" -or $response -eq "s") {
    docker volume prune -f
    Write-Host "[OK] Volumes limpos" -ForegroundColor Green
} else {
    Write-Host "[INFO] Volumes mantidos" -ForegroundColor Gray
}

# Passo 6: Limpar imagens dangling
Write-Host "`n[PASSO 6] Limpando imagens dangling..." -ForegroundColor Yellow
docker image prune -f
Write-Host "[OK] Imagens dangling removidas" -ForegroundColor Green

# Resumo final
Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "[SUCESSO] Limpeza completa finalizada!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Proximos passos:" -ForegroundColor Cyan
Write-Host "  1. docker-compose build --no-cache" -ForegroundColor White
Write-Host "  2. docker-compose up -d" -ForegroundColor White
Write-Host "  3. Acessar: http://localhost:8080" -ForegroundColor White
Write-Host ""
Write-Host "IMPORTANTE: Com a nova arquitetura SaaS:" -ForegroundColor Yellow
Write-Host "  - Backend NAO expoe porta 8000 diretamente" -ForegroundColor Gray
Write-Host "  - Frontend NAO expoe porta 3000 diretamente" -ForegroundColor Gray
Write-Host "  - Tudo passa pelo Nginx na porta 8080" -ForegroundColor Gray
Write-Host ""
