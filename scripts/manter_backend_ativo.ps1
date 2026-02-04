# Script para manter o backend sempre ativo
# Reinicia automaticamente se cair

Write-Host "🚀 Iniciando monitoramento do backend..." -ForegroundColor Cyan

$backendPath = "G:\app_hotel_cabo_frio\backend"
$scriptPath = "app_simples.py"

while ($true) {
    # Verificar se backend está rodando
    $pythonProcesses = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
        $_.Path -like "*python*"
    }
    
    $backendRunning = $false
    if ($pythonProcesses) {
        # Verificar se a porta 8000 está em uso
        $port8000 = netstat -ano | Select-String ":8000" | Select-String "LISTENING"
        if ($port8000) {
            $backendRunning = $true
        }
    }
    
    if (-not $backendRunning) {
        Write-Host "⚠️ Backend não está rodando. Iniciando..." -ForegroundColor Yellow
        
        # Iniciar backend
        $process = Start-Process -FilePath "python" `
            -ArgumentList "$scriptPath" `
            -WorkingDirectory $backendPath `
            -PassThru `
            -WindowStyle Hidden
        
        Write-Host "✅ Backend iniciado (PID: $($process.Id))" -ForegroundColor Green
        Start-Sleep -Seconds 5
        
        # Verificar se realmente iniciou
        $port8000 = netstat -ano | Select-String ":8000" | Select-String "LISTENING"
        if ($port8000) {
            Write-Host "✅ Backend respondendo na porta 8000" -ForegroundColor Green
        } else {
            Write-Host "❌ Erro: Backend não está respondendo" -ForegroundColor Red
        }
    } else {
        Write-Host "✓ Backend rodando OK ($(Get-Date -Format 'HH:mm:ss'))" -ForegroundColor Gray
    }
    
    # Aguardar 10 segundos antes de verificar novamente
    Start-Sleep -Seconds 10
}

