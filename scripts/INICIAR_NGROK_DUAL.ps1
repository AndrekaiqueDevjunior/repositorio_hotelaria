# Iniciar Ngrok com Dois Tuneis
# Uso: .\INICIAR_NGROK_DUAL.ps1

Write-Host "[INFO] Iniciando tuneis ngrok..." -ForegroundColor Cyan

# Verificar se ngrok esta instalado
if (-not (Get-Command ngrok -ErrorAction SilentlyContinue)) {
    Write-Host "[ERRO] Ngrok nao encontrado. Instale em: https://ngrok.com/download" -ForegroundColor Red
    exit 1
}

# Verificar se servicos estao rodando
Write-Host "[INFO] Verificando servicos locais..." -ForegroundColor Yellow

$backendRunning = Test-NetConnection -ComputerName localhost -Port 8000 -InformationLevel Quiet
$frontendRunning = Test-NetConnection -ComputerName localhost -Port 3000 -InformationLevel Quiet

if (-not $backendRunning) {
    Write-Host "[AVISO] Backend nao esta rodando na porta 8000" -ForegroundColor Yellow
    Write-Host "[INFO] Inicie o backend primeiro: docker-compose up backend" -ForegroundColor Cyan
}

if (-not $frontendRunning) {
    Write-Host "[AVISO] Frontend nao esta rodando na porta 3000" -ForegroundColor Yellow
    Write-Host "[INFO] Inicie o frontend primeiro: docker-compose up frontend" -ForegroundColor Cyan
}

# Iniciar tunel backend em background
Write-Host "[INFO] Iniciando tunel para backend (porta 8000)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "ngrok http 8000 --host-header='localhost:8000'"

Start-Sleep -Seconds 2

# Iniciar tunel frontend em background
Write-Host "[INFO] Iniciando tunel para frontend (porta 3000)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "ngrok http 3000 --host-header='localhost:3000'"

Start-Sleep -Seconds 3

# Obter URLs via API do ngrok
Write-Host "`n[INFO] Obtendo URLs publicas..." -ForegroundColor Cyan

try {
    $tunnels = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels"
    
    Write-Host "`n========================================" -ForegroundColor Green
    Write-Host "TUNEIS NGROK ATIVOS" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    
    foreach ($tunnel in $tunnels.tunnels) {
        $port = $tunnel.config.addr -replace ".*:", ""
        $url = $tunnel.public_url
        
        if ($port -eq "8000") {
            Write-Host "`nBACKEND:" -ForegroundColor Yellow
            Write-Host "  URL Publica: $url" -ForegroundColor White
            Write-Host "  URL Local:   http://localhost:8000" -ForegroundColor Gray
        }
        elseif ($port -eq "3000") {
            Write-Host "`nFRONTEND:" -ForegroundColor Yellow
            Write-Host "  URL Publica: $url" -ForegroundColor White
            Write-Host "  URL Local:   http://localhost:3000" -ForegroundColor Gray
        }
    }
    
    Write-Host "`n========================================" -ForegroundColor Green
    Write-Host "`n[IMPORTANTE] Atualize os arquivos .env:" -ForegroundColor Cyan
    Write-Host "1. Backend .env -> CORS_ORIGINS com as URLs acima" -ForegroundColor White
    Write-Host "2. Frontend .env.local -> NEXT_PUBLIC_API_URL com URL do backend" -ForegroundColor White
    Write-Host "`n[INFO] Dashboard ngrok: http://localhost:4040" -ForegroundColor Cyan
    
} catch {
    Write-Host "[AVISO] Nao foi possivel obter URLs automaticamente" -ForegroundColor Yellow
    Write-Host "[INFO] Acesse http://localhost:4040 para ver as URLs" -ForegroundColor Cyan
}

Write-Host "`n[INFO] Pressione Ctrl+C nas janelas do ngrok para encerrar" -ForegroundColor Gray
