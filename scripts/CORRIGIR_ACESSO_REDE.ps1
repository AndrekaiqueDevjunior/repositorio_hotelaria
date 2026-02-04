# =========================================
# Corrigir Acesso Rede - Requer Administrador
# =========================================
# Execute como Administrador: Botão Direito -> Executar como Administrador

Write-Host "[CORRECAO] Configurando portas para acesso externo..." -ForegroundColor Cyan
Write-Host ""
Write-Host "[AVISO] Este script precisa ser executado como Administrador!" -ForegroundColor Yellow
Write-Host ""

# Verificar se está executando como Administrador
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "[ERROR] Execute este script como Administrador!" -ForegroundColor Red
    Write-Host "[INFO] Botão direito no arquivo -> Executar como Administrador" -ForegroundColor Yellow
    Read-Host "Pressione Enter para sair"
    exit 1
}

Write-Host "[OK] Executando como Administrador" -ForegroundColor Green
Write-Host ""

# Limpar regras existentes
Write-Host "[CLEAN] Limpando regras existentes..." -ForegroundColor Yellow
netsh interface portproxy delete v4tov4 listenport=3000 listenaddress=0.0.0.0 2>$null
netsh interface portproxy delete v4tov4 listenport=8000 listenaddress=0.0.0.0 2>$null

# Adicionar regras de port proxy
Write-Host "[SETUP] Configurando redirecionamento de portas..." -ForegroundColor Cyan

# Frontend (porta 3000)
Write-Host "   Configurando porta 3000 (Frontend)..." -ForegroundColor Gray
$result1 = netsh interface portproxy add v4tov4 listenport=3000 listenaddress=0.0.0.0 connectport=3000 connectaddress=127.0.0.1

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Porta 3000 configurada" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Falha ao configurar porta 3000" -ForegroundColor Red
}

# Backend (porta 8000)
Write-Host "   Configurando porta 8000 (Backend)..." -ForegroundColor Gray
$result2 = netsh interface portproxy add v4tov4 listenport=8000 listenaddress=0.0.0.0 connectport=8000 connectaddress=127.0.0.1

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Porta 8000 configurada" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Falha ao configurar porta 8000" -ForegroundColor Red
}

Write-Host ""

# Configurar firewall
Write-Host "[FIREWALL] Configurando regras do firewall..." -ForegroundColor Cyan

# Remover regras existentes
netsh advfirewall firewall delete rule name="Hotel Frontend" 2>$null
netsh advfirewall firewall delete rule name="Hotel Backend" 2>$null

# Adicionar regras para frontend
Write-Host "   Adicionando regra para Frontend (porta 3000)..." -ForegroundColor Gray
netsh advfirewall firewall add rule name="Hotel Frontend" dir=in action=allow protocol=TCP localport=3000

# Adicionar regras para backend
Write-Host "   Adicionando regra para Backend (porta 8000)..." -ForegroundColor Gray
netsh advfirewall firewall add rule name="Hotel Backend" dir=in action=allow protocol=TCP localport=8000

Write-Host ""

# Mostrar regras configuradas
Write-Host "[INFO] Regras de port proxy configuradas:" -ForegroundColor Cyan
netsh interface portproxy show v4tov4

Write-Host ""
Write-Host "[INFO] Regras do firewall configuradas:" -ForegroundColor Cyan
netsh advfirewall firewall show rule name="Hotel Frontend"
netsh advfirewall firewall show rule name="Hotel Backend"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "[OK] Configuracao concluida!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "[TEST] Teste as URLs:" -ForegroundColor Cyan
Write-Host "   Frontend: http://$($ipAddress):3000" -ForegroundColor White
Write-Host "   Backend:  http://$($ipAddress):8000" -ForegroundColor White
Write-Host ""
Write-Host "[IMPORTANTE] Instrucoes:" -ForegroundColor Yellow
Write-Host "   1. Reinicie os containers Docker" -ForegroundColor Gray
Write-Host "   2. Teste o acesso novamente" -ForegroundColor Gray
Write-Host "   3. Se ainda nao funcionar, verifique o antivirus/firewall" -ForegroundColor Gray
Write-Host ""
Write-Host "[RESTART] Para reiniciar containers:" -ForegroundColor Cyan
Write-Host "   docker-compose restart" -ForegroundColor Gray
Write-Host ""
Write-Host "[REMOVE] Para remover estas configuracoes:" -ForegroundColor Red
Write-Host "   netsh interface portproxy delete v4tov4 listenport=3000 listenaddress=0.0.0.0" -ForegroundColor Gray
Write-Host "   netsh interface portproxy delete v4tov4 listenport=8000 listenaddress=0.0.0.0" -ForegroundColor Gray
Write-Host "   netsh advfirewall firewall delete rule name='Hotel Frontend'" -ForegroundColor Gray
Write-Host "   netsh advfirewall firewall delete rule name='Hotel Backend'" -ForegroundColor Gray
Write-Host ""

Read-Host "Pressione Enter para sair"
