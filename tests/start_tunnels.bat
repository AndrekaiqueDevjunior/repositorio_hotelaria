@echo off
echo Iniciando Cloudflare Tunnel para frontend...
start "Frontend Tunnel" cloudflared tunnel --url http://localhost:3000

echo Aguardando 5 segundos...
timeout /t 5 /nobreak >nul

echo Iniciando Cloudflare Tunnel para backend...
start "Backend Tunnel" cloudflared tunnel --url http://localhost:8000

echo Túneis iniciados! Verifique as janelas para obter as URLs.
pause
