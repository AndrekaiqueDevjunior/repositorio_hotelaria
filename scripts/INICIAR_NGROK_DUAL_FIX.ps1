# Iniciar Ngrok com Dois Tuneis - Versao Corrigida
# Uso: .\INICIAR_NGROK_DUAL_FIX.ps1

Write-Host "[INFO] Iniciando tuneis ngrok (versao corrigida)..." -ForegroundColor Cyan

# Verificar se ngrok esta instalado
if (-not (Get-Command ngrok -ErrorAction SilentlyContinue)) {
    Write-Host "[ERRO] Ngrok nao encontrado. Instale em: https://ngrok.com/download" -ForegroundColor Red
    exit 1
}

# Verificar se servicos estao rodando
Write-Host "[INFO] Verificando servicos locais..." -ForegroundColor Yellow

$backendRunning = Test-NetConnection -ComputerName localhost -Port 8000 -InformationLevel Quiet -WarningAction SilentlyContinue
$frontendRunning = Test-NetConnection -ComputerName localhost -Port 3000 -InformationLevel Quiet -WarningAction SilentlyContinue

if (-not $backendRunning) {
    Write-Host "[AVISO] Backend nao esta rodando na porta 8000" -ForegroundColor Yellow
    Write-Host "[INFO] Inicie o backend primeiro: docker-compose up backend" -ForegroundColor Cyan
}

if (-not $frontendRunning) {
    Write-Host "[AVISO] Frontend nao esta rodando na porta 3000" -ForegroundColor Yellow
    Write-Host "[INFO] Inicie o frontend primeiro: docker-compose up frontend" -ForegroundColor Cyan
}

# Parar ngrok existente para evitar conflitos
Write-Host "[INFO] Limpando processos ngrok existentes..." -ForegroundColor Yellow
Get-Process | Where-Object {$_.ProcessName -like "*ngrok*"} | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Iniciar tunel backend em background com delay
Write-Host "[INFO] Iniciando tunel para backend (porta 8000)..." -ForegroundColor Green
$backendProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", "ngrok http 8000 --host-header='localhost:8000'" -PassThru

Start-Sleep -Seconds 3

# Iniciar tunel frontend em background com delay
Write-Host "[INFO] Iniciando tunel para frontend (porta 3000)..." -ForegroundColor Green
$frontendProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", "ngrok http 3000 --host-header='localhost:3000'" -PassThru

Start-Sleep -Seconds 5

# Obter URLs via API do ngrok com retry
Write-Host "`n[INFO] Obtendo URLs publicas..." -ForegroundColor Cyan

$retryCount = 0
$maxRetries = 10
$tunnels = $null

while ($retryCount -lt $maxRetries -and (-not $tunnels -or $tunnels.tunnels.Count -lt 2)) {
    try {
        $tunnels = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels" -ErrorAction Stop
        
        if ($tunnels.tunnels.Count -ge 2) {
            break
        }
        
        Write-Host "[INFO] Aguardando mais tuneis... ($($tunnels.tunnels.Count)/2)" -ForegroundColor Gray
        Start-Sleep -Seconds 2
        
    } catch {
        Write-Host "[INFO] Aguardando API do ngrod... (tentativa $($retryCount + 1))" -ForegroundColor Gray
        Start-Sleep -Seconds 2
    }
    
    $retryCount++
}

if (-not $tunnels -or $tunnels.tunnels.Count -lt 2) {
    Write-Host "[ERRO] Nao foi possivel iniciar ambos os tuneis" -ForegroundColor Red
    if ($tunnels) {
        Write-Host "[INFO] Apenas $($tunnels.tunnels.Count) tunel(is) iniciado(s)" -ForegroundColor Yellow
        foreach ($tunnel in $tunnels.tunnels) {
            Write-Host "[INFO] $($tunnel.config.addr) -> $($tunnel.public_url)" -ForegroundColor Gray
        }
    }
    exit 1
}

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "TUNEIS NGROK ATIVOS" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

$backendUrl = ""
$frontendUrl = ""

foreach ($tunnel in $tunnels.tunnels) {
    $port = $tunnel.config.addr -replace ".*:", ""
    $url = $tunnel.public_url
    
    if ($port -eq "8000") {
        $backendUrl = $url
        Write-Host "`nBACKEND:" -ForegroundColor Yellow
        Write-Host "  URL Publica: $url" -ForegroundColor White
        Write-Host "  URL Local:   http://localhost:8000" -ForegroundColor Gray
    }
    elseif ($port -eq "3000") {
        $frontendUrl = $url
        Write-Host "`nFRONTEND:" -ForegroundColor Yellow
        Write-Host "  URL Publica: $url" -ForegroundColor White
        Write-Host "  URL Local:   http://localhost:3000" -ForegroundColor Gray
    }
}

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "`n[IMPORTANTE] Execute o proximo comando:" -ForegroundColor Cyan
Write-Host ".\ATUALIZAR_ENV_NGROK_FIX.ps1" -ForegroundColor White
Write-Host "`n[INFO] Dashboard ngrok: http://localhost:4040" -ForegroundColor Cyan

# Salvar URLs em arquivo temporario para o proximo script
$urlData = @{
    backendUrl = $backendUrl
    frontendUrl = $frontendUrl
} | ConvertTo-Json

$urlData | Set-Content -Path ".ngrok_urls.tmp" -Encoding UTF8

Write-Host "[INFO] URLs salvas em .ngrok_urls.tmp" -ForegroundColor Gray
Write-Host "`n[INFO] Pressione Ctrl+C nas janelas do ngrok para encerrar" -ForegroundColor Gray
