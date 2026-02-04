# ============================================================
# Iniciar LocalTunnel e Exibir Senha
# ============================================================

Write-Host "[INFO] Iniciando LocalTunnel com exibição de senha..." -ForegroundColor Green

# Gerar subdomínio único
$timestamp = Get-Date -Format "yyyyMMddHHmm"
$subdomain = "hotel-cabo-frio-$timestamp"

Write-Host "[INFO] Subdomínio: $subdomain" -ForegroundColor Cyan
Write-Host "[INFO] URL será: https://$subdomain.loca.lt" -ForegroundColor Cyan
Write-Host ""

Write-Host "[IMPORTANTE] ATENÇÃO À SENHA!" -ForegroundColor Yellow
Write-Host "A senha será exibida abaixo. Copie e cole no navegador." -ForegroundColor Yellow
Write-Host ""

# Iniciar LocalTunnel diretamente para ver a senha
Write-Host "[TUNNEL] Executando: npx localtunnel --port 8080 --subdomain $subdomain" -ForegroundColor Gray
Write-Host ""

# Executar e mostrar output em tempo real
try {
    & npx localtunnel --port 8080 --subdomain $subdomain
} catch {
    Write-Host "[ERRO] Erro ao executar LocalTunnel: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "[INFO] Para reiniciar: .\INICIAR_LOCALTUNNEL_EXIBIR_SENHA.ps1" -ForegroundColor Cyan
