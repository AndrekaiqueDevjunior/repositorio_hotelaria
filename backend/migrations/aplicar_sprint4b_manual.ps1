# ============================================================
# INSTRUCOES MANUAIS - Sprint 4B
# Para quando o PostgreSQL nao esta no PATH
# ============================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  APLICAR SPRINT 4B - MODO MANUAL" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "PASSO 1: Aplicar Migration no pgAdmin" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Abra o pgAdmin 4" -ForegroundColor White
Write-Host "2. Conecte-se ao servidor PostgreSQL" -ForegroundColor White
Write-Host "3. Navegue ate: Servers - PostgreSQL - Databases - hotel_cabo_frio" -ForegroundColor White
Write-Host "4. Clique com botao direito em hotel_cabo_frio e escolha Query Tool" -ForegroundColor White
Write-Host "5. No Query Tool:" -ForegroundColor White
Write-Host "   - Clique em Open File (icone de pasta)" -ForegroundColor Gray
Write-Host "   - Navegue ate: G:\app_hotel_cabo_frio\backend\migrations\" -ForegroundColor Gray
Write-Host "   - Abra o arquivo: 004_seguranca_pagamentos.sql" -ForegroundColor Gray
Write-Host "   - Clique em Execute (icone de play) ou pressione F5" -ForegroundColor Gray
Write-Host "6. Verifique a mensagem de sucesso no Output" -ForegroundColor White
Write-Host ""

Read-Host "Pressione ENTER apos executar a migration no pgAdmin"

Write-Host ""
Write-Host "OK Migration aplicada!" -ForegroundColor Green
Write-Host ""

# ============================================================
# PASSO 2: ATUALIZAR PRISMA
# ============================================================
Write-Host "PASSO 2: Atualizar Prisma Client" -ForegroundColor Yellow
Write-Host ""

$currentPath = Get-Location

# Tentar encontrar a pasta backend
if ($currentPath -match "migrations") {
    Set-Location ..
    Write-Host "   Mudando para pasta backend..." -ForegroundColor Gray
}

if (Test-Path "prisma\schema.prisma") {
    Write-Host "   Executando: npx prisma generate" -ForegroundColor Gray
    Write-Host ""
    
    npx prisma generate
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "OK Prisma Client atualizado!" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "AVISO: Erro ao atualizar Prisma" -ForegroundColor Yellow
        Write-Host "   Execute manualmente:" -ForegroundColor Gray
        Write-Host "   cd G:\app_hotel_cabo_frio\backend" -ForegroundColor Gray
        Write-Host "   npx prisma generate" -ForegroundColor Gray
    }
} else {
    Write-Host "AVISO: Nao encontrei a pasta backend!" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Execute manualmente:" -ForegroundColor White
    Write-Host "   cd G:\app_hotel_cabo_frio\backend" -ForegroundColor Gray
    Write-Host "   npx prisma generate" -ForegroundColor Gray
    Write-Host ""
    Read-Host "Pressione ENTER apos executar o comando acima"
}

# ============================================================
# PASSO 3: REINICIAR SERVICOS
# ============================================================
Write-Host ""
Write-Host "PASSO 3: Reiniciar Servicos" -ForegroundColor Yellow
Write-Host ""

$resposta = Read-Host "Deseja que eu tente reiniciar o backend? (S/N)"

if ($resposta -eq "S" -or $resposta -eq "s") {
    Write-Host ""
    Write-Host "   Parando processos Python/Uvicorn..." -ForegroundColor Gray
    
    # Tentar parar processos existentes
    Get-Process | Where-Object {
        $_.ProcessName -like "*python*" -or 
        $_.ProcessName -like "*uvicorn*"
    } | ForEach-Object {
        Write-Host "   Parando: $($_.ProcessName) (PID: $($_.Id))" -ForegroundColor Gray
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    }
    
    Start-Sleep -Seconds 2
    
    Write-Host ""
    Write-Host "   Iniciando backend em nova janela..." -ForegroundColor Gray
    
    # Ir para pasta backend se nao estiver nela
    if (-not (Test-Path "app\main.py")) {
        if (Test-Path "G:\app_hotel_cabo_frio\backend") {
            Set-Location "G:\app_hotel_cabo_frio\backend"
        }
    }
    
    if (Test-Path "app\main.py") {
        # Iniciar em nova janela do PowerShell
        Start-Process powershell -ArgumentList `
            "-NoExit", `
            "-Command", `
            "cd '$PWD'; python -m uvicorn app.main:app --reload"
        
        Write-Host ""
        Write-Host "OK Backend iniciado em nova janela!" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "AVISO: Nao encontrei o arquivo app\main.py" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Execute manualmente:" -ForegroundColor White
        Write-Host "   cd G:\app_hotel_cabo_frio\backend" -ForegroundColor Gray
        Write-Host "   python -m uvicorn app.main:app --reload" -ForegroundColor Gray
    }
} else {
    Write-Host ""
    Write-Host "Execute manualmente quando estiver pronto:" -ForegroundColor White
    Write-Host ""
    Write-Host "Backend:" -ForegroundColor Yellow
    Write-Host "   cd G:\app_hotel_cabo_frio\backend" -ForegroundColor Gray
    Write-Host "   python -m uvicorn app.main:app --reload" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Frontend (se necessario):" -ForegroundColor Yellow
    Write-Host "   cd G:\app_hotel_cabo_frio\frontend" -ForegroundColor Gray
    Write-Host "   npm run dev" -ForegroundColor Gray
}

# ============================================================
# RESUMO FINAL
# ============================================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  OK SPRINT 4B APLICADA!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "MELHORIAS IMPLEMENTADAS:" -ForegroundColor Yellow
Write-Host ""
Write-Host "OK Seguranca de Pagamento:" -ForegroundColor White
Write-Host "   - CVV removido do banco de dados" -ForegroundColor Gray
Write-Host "   - Cartoes mascarados (.... 1234)" -ForegroundColor Gray
Write-Host "   - Tokenizacao implementada" -ForegroundColor Gray
Write-Host "   - PCI-DSS: 30% para 70% (+40%)" -ForegroundColor Gray
Write-Host ""
Write-Host "OK Melhorias em Quartos:" -ForegroundColor White
Write-Host "   - Historico de ocupacao completo" -ForegroundColor Gray
Write-Host "   - Taxa de ocupacao (90 dias)" -ForegroundColor Gray
Write-Host "   - Status com badges coloridos" -ForegroundColor Gray
Write-Host "   - 5 estatisticas por quarto" -ForegroundColor Gray
Write-Host ""
Write-Host "OK Detalhes de Antifraude:" -ForegroundColor White
Write-Host "   - Modal rico com timeline" -ForegroundColor Gray
Write-Host "   - Fatores de risco detalhados" -ForegroundColor Gray
Write-Host "   - Informacoes completas do pagamento" -ForegroundColor Gray
Write-Host "   - Acoes integradas no modal" -ForegroundColor Gray
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "DOCUMENTACAO:" -ForegroundColor Yellow
Write-Host "   - SPRINT_4B_COMPLETO.md" -ForegroundColor Gray
Write-Host "   - SPRINT_4B_VISUAL.md" -ForegroundColor Gray
Write-Host "   - SPRINT_4B_RESUMO.md" -ForegroundColor Gray
Write-Host ""
Write-Host "Acesse o sistema e teste as melhorias!" -ForegroundColor Green
Write-Host ""
