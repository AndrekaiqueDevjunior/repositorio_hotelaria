# ============================================================
# Script PowerShell para Aplicar Sprint 4B
# Data: 21/12/2024
# Descrição: Aplica melhorias de segurança de pagamentos
# ============================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SPRINT 4B - APLICAR MELHORIAS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar se PostgreSQL está no PATH
$pgPath = $null
$possiblePaths = @(
    "C:\Program Files\PostgreSQL\16\bin",
    "C:\Program Files\PostgreSQL\15\bin",
    "C:\Program Files\PostgreSQL\14\bin",
    "C:\Program Files\PostgreSQL\13\bin",
    "C:\Program Files (x86)\PostgreSQL\16\bin",
    "C:\Program Files (x86)\PostgreSQL\15\bin"
)

foreach ($path in $possiblePaths) {
    if (Test-Path "$path\psql.exe") {
        $pgPath = $path
        Write-Host "✅ PostgreSQL encontrado em: $pgPath" -ForegroundColor Green
        break
    }
}

if (-not $pgPath) {
    Write-Host "❌ PostgreSQL não encontrado no PATH!" -ForegroundColor Red
    Write-Host ""
    Write-Host "OPÇÕES:" -ForegroundColor Yellow
    Write-Host "1. Adicionar PostgreSQL ao PATH do sistema" -ForegroundColor White
    Write-Host "2. Ou executar manualmente via pgAdmin:" -ForegroundColor White
    Write-Host "   - Abra o pgAdmin" -ForegroundColor Gray
    Write-Host "   - Conecte ao banco 'hotel_cabo_frio'" -ForegroundColor Gray
    Write-Host "   - Vá em Tools > Query Tool" -ForegroundColor Gray
    Write-Host "   - Abra o arquivo: backend/migrations/004_seguranca_pagamentos.sql" -ForegroundColor Gray
    Write-Host "   - Execute o script (F5)" -ForegroundColor Gray
    Write-Host ""
    
    $resposta = Read-Host "Deseja continuar mesmo assim? (S/N)"
    if ($resposta -ne "S" -and $resposta -ne "s") {
        exit
    }
} else {
    # Adicionar temporariamente ao PATH desta sessão
    $env:Path = "$pgPath;$env:Path"
}

# ============================================================
# PASSO 1: BACKUP DO BANCO
# ============================================================
Write-Host ""
Write-Host "PASSO 1: Fazendo backup do banco..." -ForegroundColor Yellow

if ($pgPath) {
    $backupFile = "backup_sprint4b_$(Get-Date -Format 'yyyyMMdd_HHmmss').sql"
    
    try {
        & "$pgPath\pg_dump.exe" -U postgres -d hotel_cabo_frio -f $backupFile
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Backup criado: $backupFile" -ForegroundColor Green
        } else {
            Write-Host "⚠️  Erro ao criar backup (código: $LASTEXITCODE)" -ForegroundColor Yellow
            Write-Host "   Verifique se o usuário 'postgres' está correto" -ForegroundColor Gray
        }
    } catch {
        Write-Host "⚠️  Erro ao criar backup: $_" -ForegroundColor Yellow
    }
} else {
    Write-Host "⏭️  Pulando backup (PostgreSQL não configurado)" -ForegroundColor Gray
}

# ============================================================
# PASSO 2: APLICAR MIGRATION
# ============================================================
Write-Host ""
Write-Host "PASSO 2: Aplicando migration de segurança..." -ForegroundColor Yellow

$migrationFile = "004_seguranca_pagamentos.sql"

if (-not (Test-Path $migrationFile)) {
    Write-Host "❌ Arquivo de migration não encontrado: $migrationFile" -ForegroundColor Red
    Write-Host "   Certifique-se de estar na pasta: backend/migrations" -ForegroundColor Gray
    exit
}

if ($pgPath) {
    Write-Host "   Executando: $migrationFile" -ForegroundColor Gray
    
    try {
        & "$pgPath\psql.exe" -U postgres -d hotel_cabo_frio -f $migrationFile
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Migration aplicada com sucesso!" -ForegroundColor Green
        } else {
            Write-Host "❌ Erro ao aplicar migration (código: $LASTEXITCODE)" -ForegroundColor Red
            exit
        }
    } catch {
        Write-Host "❌ Erro ao aplicar migration: $_" -ForegroundColor Red
        exit
    }
} else {
    Write-Host "⏭️  Execute manualmente via pgAdmin (instruções acima)" -ForegroundColor Yellow
    Read-Host "Pressione ENTER após executar a migration no pgAdmin"
}

# ============================================================
# PASSO 3: ATUALIZAR PRISMA
# ============================================================
Write-Host ""
Write-Host "PASSO 3: Atualizando Prisma Client..." -ForegroundColor Yellow

# Voltar para pasta backend
$backendPath = Split-Path -Parent (Get-Location)
if ((Get-Location).Path -notmatch "backend$") {
    if (Test-Path "..\prisma") {
        Set-Location ..
    } elseif (Test-Path "..\..\backend") {
        Set-Location ..\..\backend
    }
}

Write-Host "   Pasta atual: $(Get-Location)" -ForegroundColor Gray

if (Test-Path "prisma\schema.prisma") {
    try {
        Write-Host "   Executando: npx prisma generate" -ForegroundColor Gray
        npx prisma generate
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Prisma Client atualizado!" -ForegroundColor Green
        } else {
            Write-Host "⚠️  Erro ao atualizar Prisma (código: $LASTEXITCODE)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "⚠️  Erro ao executar npx prisma generate: $_" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️  Arquivo schema.prisma não encontrado" -ForegroundColor Yellow
    Write-Host "   Execute manualmente: cd backend; npx prisma generate" -ForegroundColor Gray
}

# ============================================================
# PASSO 4: INSTRUÇÕES FINAIS
# ============================================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ✅ SPRINT 4B APLICADA!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "PRÓXIMOS PASSOS:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Reiniciar Backend:" -ForegroundColor White
Write-Host "   cd backend" -ForegroundColor Gray
Write-Host "   python -m uvicorn app.main:app --reload" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Frontend (se ainda não estiver rodando):" -ForegroundColor White
Write-Host "   cd frontend" -ForegroundColor Gray
Write-Host "   npm run dev" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Testar as melhorias:" -ForegroundColor White
Write-Host "   - 🔒 Pagamentos: Verificar que CVV não aparece mais" -ForegroundColor Gray
Write-Host "   - 🏨 Quartos: Botão '📊 Histórico' funcionando" -ForegroundColor Gray
Write-Host "   - 🛡️  Antifraude: Botão '📊 Detalhes' com modal rico" -ForegroundColor Gray
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Perguntar se deseja reiniciar o backend agora
$resposta = Read-Host "Deseja reiniciar o backend agora? (S/N)"
if ($resposta -eq "S" -or $resposta -eq "s") {
    Write-Host ""
    Write-Host "Reiniciando backend..." -ForegroundColor Yellow
    
    # Matar processos uvicorn existentes
    Get-Process | Where-Object {$_.ProcessName -like "*python*" -or $_.ProcessName -like "*uvicorn*"} | Stop-Process -Force -ErrorAction SilentlyContinue
    
    Start-Sleep -Seconds 2
    
    # Iniciar novo processo
    if (Test-Path "app\main.py") {
        Write-Host "Iniciando uvicorn..." -ForegroundColor Gray
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "python -m uvicorn app.main:app --reload"
        Write-Host "✅ Backend iniciado em nova janela!" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Certifique-se de estar na pasta 'backend'" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Script concluído! 🎉" -ForegroundColor Green
Write-Host ""

