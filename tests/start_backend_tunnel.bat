@echo off
echo Iniciando Cloudflare Tunnel para Backend (porta 8000)...
cloudflared tunnel --url http://localhost:8000

pause
