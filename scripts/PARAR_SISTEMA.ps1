# ============================================================
# SCRIPT DE PARADA SEGURA - Sistema Hotel Cabo Frio
# ============================================================

Write-Host "============================================================" -ForegroundColor Yellow
Write-Host "  PARANDO SISTEMA HOTEL CABO FRIO" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Yellow
Write-Host ""

# Passo 1: Parar containers com profile ngrok
Write-Host "[1/4] Parando containers ngrok..." -ForegroundColor Cyan
docker-compose --profile ngrok down --remove-orphans 2>$null

if ($LASTEXITCODE -ne 0) {
    Write-Host "[AVISO] Erro ao parar com profile ngrok, tentando metodo alternativo..." -ForegroundColor Yellow
    
    # Passo 2: Parar containers normais
    Write-Host "[2/4] Parando containers sem profile..." -ForegroundColor Cyan
    docker-compose down --remove-orphans 2>$null
}

# Passo 3: Forcar parada de containers orfaos
Write-Host "[3/4] Verificando containers orfaos..." -ForegroundColor Cyan
$orphans = docker ps -aq --filter "name=hotel-" 2>$null
if ($orphans) {
    Write-Host "  - Encontrados containers orfaos, removendo..." -ForegroundColor Gray
    $orphans | ForEach-Object { docker rm -f $_ 2>$null }
}

$appOrphans = docker ps -aq --filter "name=app_hotel_cabo_frio-" 2>$null
if ($appOrphans) {
    Write-Host "  - Encontrados containers app_hotel, removendo..." -ForegroundColor Gray
    $appOrphans | ForEach-Object { docker rm -f $_ 2>$null }
}

# Passo 4: Limpar rede se ainda estiver em uso
Write-Host "[4/4] Limpando rede..." -ForegroundColor Cyan
$network = docker network ls --filter "name=hotel_network" --format "{{.Name}}" 2>$null
if ($network) {
    docker network rm hotel_network 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  - Rede ainda em uso, forcando limpeza..." -ForegroundColor Gray
        
        # Desconectar todos os containers da rede
        $containers = docker network inspect hotel_network --format '{{range .Containers}}{{.Name}} {{end}}' 2>$null
        if ($containers) {
            $containers.Split(' ') | ForEach-Object {
                if ($_ -ne "") {
                    docker network disconnect -f hotel_network $_ 2>$null
                }
            }
        }
        
        # Tentar remover novamente
        docker network rm hotel_network 2>$null
    }
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  SISTEMA PARADO COM SUCESSO!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Para iniciar novamente:" -ForegroundColor Cyan
Write-Host "  .\INICIAR_SISTEMA_NGROK.ps1" -ForegroundColor White
Write-Host ""
Write-Host "Ou modo rapido:" -ForegroundColor Cyan
Write-Host "  .\INICIAR_NGROK_RAPIDO.ps1" -ForegroundColor White
Write-Host ""

# Mostrar status final
Write-Host "Verificando containers restantes..." -ForegroundColor Gray
$remaining = docker ps -a --filter "name=hotel" --format "{{.Names}}"
if ($remaining) {
    Write-Host "[AVISO] Ainda existem containers:" -ForegroundColor Yellow
    docker ps -a --filter "name=hotel" --format "table {{.Names}}\t{{.Status}}"
} else {
    Write-Host "[OK] Nenhum container hotel ativo" -ForegroundColor Green
}

Write-Host ""
