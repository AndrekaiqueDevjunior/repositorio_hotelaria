@echo off
echo Capturando URLs dos Cloudflare Tunnels...

echo Verificando logs do tunnel do frontend...
powershell "Get-Process | Where-Object {$_.ProcessName -eq 'cloudflared'} | Select-Object -First 1 | ForEach-Object { $_.MainWindowTitle }" > frontend_url.txt

echo Verificando logs do tunnel do backend...
powershell "Get-Process | Where-Object {$_.ProcessName -eq 'cloudflared'} | Select-Object -Skip 1 -First 1 | ForEach-Object { $_.MainWindowTitle }" > backend_url.txt

echo URLs capturadas nos arquivos frontend_url.txt e backend_url.txt
pause
