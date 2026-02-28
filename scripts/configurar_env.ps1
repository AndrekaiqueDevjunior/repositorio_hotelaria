# ============================================================
# Script: Configurar .env automaticamente
# ============================================================
# Gera chaves seguras e configura o arquivo .env
# ============================================================

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "        CONFIGURADOR AUTOMATICO DO .ENV                        " -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# Verificar se .env existe
if (-not (Test-Path ".env")) {
    Write-Host "[*] Criando .env a partir do exemplo..." -ForegroundColor Cyan
    Copy-Item "env.docker.example" ".env"
    Write-Host "[OK] Arquivo .env criado!" -ForegroundColor Green
} else {
    Write-Host "[*] Arquivo .env ja existe" -ForegroundColor Cyan
    $resposta = Read-Host "Deseja fazer backup antes de atualizar? (S/N)"
    if ($resposta -eq "S" -or $resposta -eq "s") {
        $timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
        Copy-Item ".env" ".env.backup.$timestamp"
        Write-Host "[OK] Backup criado: .env.backup.$timestamp" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "[*] Gerando chaves seguras..." -ForegroundColor Cyan

# Gerar SECRET_KEY
$SECRET_KEY = -join ((65..90) + (97..122) + (48..57) + @(45, 95) | Get-Random -Count 64 | ForEach-Object {[char]$_})
Write-Host "[OK] SECRET_KEY gerada" -ForegroundColor Green

# Gerar JWT_SECRET_KEY
$JWT_SECRET_KEY = -join ((65..90) + (97..122) + (48..57) + @(45, 95) | Get-Random -Count 64 | ForEach-Object {[char]$_})
Write-Host "[OK] JWT_SECRET_KEY gerada" -ForegroundColor Green

Write-Host ""
Write-Host "[*] Atualizando arquivo .env..." -ForegroundColor Cyan

# Ler conteúdo atual
$envContent = Get-Content ".env" -Raw

# Atualizar SECRET_KEY
$envContent = $envContent -replace "SECRET_KEY=.*", "SECRET_KEY=$SECRET_KEY"
$envContent = $envContent -replace "JWT_SECRET_KEY=.*", "JWT_SECRET_KEY=$JWT_SECRET_KEY"

# Salvar
$envContent | Set-Content ".env" -NoNewline

Write-Host "[OK] Chaves atualizadas!" -ForegroundColor Green

Write-Host ""
Write-Host "================================================================" -ForegroundColor Green
Write-Host "        CONFIGURACAO BASICA CONCLUIDA!                         " -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Green
Write-Host ""

Write-Host "PROXIMO PASSO: Configure suas credenciais Cielo" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Abra o arquivo .env:" -ForegroundColor White
Write-Host "   notepad .env" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. Encontre e atualize:" -ForegroundColor White
Write-Host "   CIELO_MERCHANT_ID=seu-merchant-id-aqui" -ForegroundColor Cyan
Write-Host "   CIELO_MERCHANT_KEY=sua-merchant-key-aqui" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. (Opcional) Configure ngrok:" -ForegroundColor White
Write-Host "   NGROK_AUTHTOKEN=seu-token-aqui" -ForegroundColor Cyan
Write-Host "   Obtenha em: https://dashboard.ngrok.com/get-started/your-authtoken" -ForegroundColor Gray
Write-Host ""
Write-Host "4. (Opcional) Mude a senha do admin:" -ForegroundColor White
Write-Host "   ADMIN_PASSWORD=sua-senha-forte" -ForegroundColor Cyan
Write-Host ""

$abrirAgora = Read-Host "Deseja abrir o .env para editar agora? (S/N)"
if ($abrirAgora -eq "S" -or $abrirAgora -eq "s") {
    notepad .env
}

Write-Host ""
Write-Host "[OK] Pronto! Agora voce pode iniciar o sistema:" -ForegroundColor Green
Write-Host "   .\iniciar_docker_ngrok.ps1" -ForegroundColor Cyan
Write-Host ""

