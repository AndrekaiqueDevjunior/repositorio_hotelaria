# Script para Parar Todos os Processos Ngrok
# Uso: .\PARAR_NGROK.ps1

Write-Host "[INFO] Parando todos os processos ngrok..." -ForegroundColor Cyan

# Parar processos ngrok
Get-Process | Where-Object {$_.ProcessName -like "*ngrok*"} | Stop-Process -Force

# Limpar porta 4040 (API do ngrok)
try {
    $apiTest = Test-NetConnection -ComputerName localhost -Port 4040 -InformationLevel Quiet -WarningAction SilentlyContinue
    if ($apiTest) {
        Write-Host "[AVISO] API do ngrok ainda respondendo em 4040" -ForegroundColor Yellow
        Write-Host "[INFO] Aguarde alguns segundos para liberar porta" -ForegroundColor Gray
    }
} catch {
    # Ignorar erros
}

Write-Host "[OK] Ngrok parado" -ForegroundColor Green
Write-Host "[INFO] Aguarde 5 segundos antes de reiniciar" -ForegroundColor Gray
